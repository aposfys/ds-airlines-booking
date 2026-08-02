#!/usr/bin/env python
"""Load reference and demo data into the configured database.

Separate from the application's startup seeding so that populating a
development database is an explicit act rather than a side effect of running
the server — the original code seeded unconditionally on every boot,
production included (DEF-004).

    SEED_ADMIN_EMAIL=... SEED_ADMIN_PASSWORD=... python scripts/seed.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionFactory, engine  # noqa: E402
from app.seed import seed_data  # noqa: E402


async def main() -> None:
    async with SessionFactory() as session:
        await seed_data(session)
        await session.commit()
    await engine.dispose()
    print("Seeded reference data, demo flights and the administrator.")


if __name__ == "__main__":
    asyncio.run(main())
