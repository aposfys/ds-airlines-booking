"""A minimal in-memory stand-in for the Motor collection API.

The existing tests could only exercise the two auth endpoints, because
anything touching flights or bookings needed a live MongoDB. That is why the
dead admin surface and the seat-leak both survived: nothing could reach them.

This implements only the operators the application actually uses
($gt, $regex, $inc, $set) and deliberately nothing more.
"""

import re
from typing import Any, Optional

from bson import ObjectId


def _matches(doc: dict, query: dict) -> bool:
    for key, condition in query.items():
        value = doc.get(key)
        if isinstance(condition, dict):
            for op, operand in condition.items():
                if op == "$gt" and not (value is not None and value > operand):
                    return False
                elif op == "$gte" and not (value is not None and value >= operand):
                    return False
                elif op == "$regex":
                    flags = re.IGNORECASE if "i" in condition.get("$options", "") else 0
                    if value is None or not re.search(operand, str(value), flags):
                        return False
                elif op == "$options":
                    continue
        elif value != condition:
            return False
    return True


class _Cursor:
    def __init__(self, docs: list[dict]):
        self._docs = docs

    def skip(self, n: int) -> "_Cursor":
        return _Cursor(self._docs[n:])

    def limit(self, n: int) -> "_Cursor":
        return _Cursor(self._docs[:n])

    async def to_list(self, length: Optional[int] = None) -> list[dict]:
        return list(self._docs[:length] if length else self._docs)


class _InsertResult:
    def __init__(self, inserted_id: Any):
        self.inserted_id = inserted_id


class _UpdateResult:
    def __init__(self, modified_count: int):
        self.modified_count = modified_count
        self.matched_count = modified_count


class _DeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []
        self._unique_keys: list[str] = []

    async def create_index(self, keys, unique: bool = False, **kwargs) -> str:
        if unique and isinstance(keys, str):
            self._unique_keys.append(keys)
        return "index"

    async def insert_one(self, doc: dict) -> _InsertResult:
        from pymongo.errors import DuplicateKeyError

        for key in self._unique_keys:
            if key in doc and any(d.get(key) == doc[key] for d in self.docs):
                raise DuplicateKeyError(f"duplicate key: {key}")
        stored = dict(doc)
        stored.setdefault("_id", ObjectId())
        self.docs.append(stored)
        return _InsertResult(stored["_id"])

    async def insert_many(self, docs: list[dict]) -> None:
        for doc in docs:
            await self.insert_one(doc)

    async def find_one(self, query: dict) -> Optional[dict]:
        return next((dict(d) for d in self.docs if _matches(d, query)), None)

    def find(self, query: Optional[dict] = None) -> _Cursor:
        query = query or {}
        return _Cursor([dict(d) for d in self.docs if _matches(d, query)])

    async def count_documents(self, query: dict) -> int:
        return sum(1 for d in self.docs if _matches(d, query))

    async def update_one(self, query: dict, update: dict) -> _UpdateResult:
        for doc in self.docs:
            if _matches(doc, query):
                for field, delta in update.get("$inc", {}).items():
                    doc[field] = doc.get(field, 0) + delta
                doc.update(update.get("$set", {}))
                return _UpdateResult(1)
        return _UpdateResult(0)

    async def delete_one(self, query: dict) -> _DeleteResult:
        for i, doc in enumerate(self.docs):
            if _matches(doc, query):
                del self.docs[i]
                return _DeleteResult(1)
        return _DeleteResult(0)

    async def find_one_and_delete(self, query: dict) -> Optional[dict]:
        for i, doc in enumerate(self.docs):
            if _matches(doc, query):
                return self.docs.pop(i)
        return None


class FakeDB:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getattr__(self, name: str) -> FakeCollection:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._collections.setdefault(name, FakeCollection())

    def __getitem__(self, name: str) -> FakeCollection:
        return getattr(self, name)
