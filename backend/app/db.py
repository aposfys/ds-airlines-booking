"""Database engine and session management.

One session per request, committed by the request handler and rolled back on
any exception. Replaces `app/database.py`, which exposed a single shared
Motor handle imported directly by every module — a binding that had to be
monkeypatched in seven places to make tests work.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import DATABASE_URL, SQL_ECHO

engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    pool_pre_ping=True,  # drop connections killed by a proxy or a restart
)

SessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # response serialisation happens after commit
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a transactional session.

    The handler does not commit. Committing here, once, means a request
    either applies in full or not at all — which is the entire point of
    ADR-001, and what the Mongo compensating writes could not offer.
    """
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
