"""
Idempotent source seeder.
Run after every `alembic upgrade head`.
Uses INSERT ... ON CONFLICT DO NOTHING — safe to run multiple times.
"""

import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.dialects.postgresql import insert

from app.utils.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

SOURCES = [
    # ── Tier 1: Public APIs ───────────────────────────────────────
    {"name": "Greenhouse",    "tier": 1, "trust_score": 1.0, "poll_interval": 15},
    {"name": "Lever",         "tier": 1, "trust_score": 1.0, "poll_interval": 15},
    {"name": "Ashby",         "tier": 1, "trust_score": 1.0, "poll_interval": 15},
    {"name": "Remotive",      "tier": 1, "trust_score": 0.95, "poll_interval": 15},
    {"name": "Jobicy",        "tier": 1, "trust_score": 0.95, "poll_interval": 15},
    {"name": "Arbeitnow",     "tier": 1, "trust_score": 0.95, "poll_interval": 15},
    {"name": "Adzuna",        "tier": 1, "trust_score": 0.90, "poll_interval": 15},
    {"name": "TheMuse",       "tier": 1, "trust_score": 0.90, "poll_interval": 15},
    # ── Tier 2: Startup & Curated ─────────────────────────────────
    {"name": "Wellfound",     "tier": 2, "trust_score": 0.85, "poll_interval": 30},
    {"name": "YC Jobs",       "tier": 2, "trust_score": 0.85, "poll_interval": 30},
    {"name": "BuiltIn",       "tier": 2, "trust_score": 0.80, "poll_interval": 30},
    # ── Tier 3: Remote ────────────────────────────────────────────
    {"name": "RemoteOK",      "tier": 3, "trust_score": 0.75, "poll_interval": 30},
    {"name": "WeWorkRemotely","tier": 3, "trust_score": 0.75, "poll_interval": 30},
    {"name": "HackerNews",    "tier": 3, "trust_score": 0.80, "poll_interval": 30},
    # ── Tier 4: India ─────────────────────────────────────────────
    {"name": "Internshala",   "tier": 4, "trust_score": 0.70, "poll_interval": 30},
    {"name": "Foundit",       "tier": 4, "trust_score": 0.65, "poll_interval": 30},
    {"name": "Shine",         "tier": 4, "trust_score": 0.60, "poll_interval": 30},
    {"name": "TimesJobs",     "tier": 4, "trust_score": 0.60, "poll_interval": 30},
    # ── Tier 5: Aggregators ───────────────────────────────────────
    {"name": "Simplify",      "tier": 5, "trust_score": 0.70, "poll_interval": 30},
    {"name": "Jobright",      "tier": 5, "trust_score": 0.70, "poll_interval": 30},
    {"name": "Levelsfyi",     "tier": 5, "trust_score": 0.75, "poll_interval": 30},
]


async def seed(session: AsyncSession) -> None:
    from app.database.models import Source, SourceHealth

    for data in SOURCES:
        # Upsert source — skip if name already exists
        stmt = (
            insert(Source)
            .values(id=uuid.uuid4(), **data, is_active=True)
            .on_conflict_do_nothing(index_elements=["name"])
        )
        await session.execute(stmt)

    await session.flush()

    # Ensure every source has a source_health row
    from sqlalchemy import select
    result = await session.execute(select(Source))
    sources = result.scalars().all()

    for source in sources:
        health_stmt = (
            insert(SourceHealth)
            .values(id=uuid.uuid4(), source_id=source.id, status="unknown")
            .on_conflict_do_nothing(index_elements=["source_id"])
        )
        await session.execute(health_stmt)

    await session.commit()
    log.info("seed_complete", total_sources=len(sources))


async def main() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await seed(session)
        await seed_default_user(session) 
    await engine.dispose()

async def seed_default_user(session: AsyncSession) -> None:
    """
    Create the default user used in Day 3-5 before auth is wired.
    UUID is stable: 00000000-0000-0000-0000-000000000001
    """
    from app.database.models import User
    from app.services.source_selector_service import DEFAULT_USER_ID

    stmt = (
        insert(User)
        .values(
            id=DEFAULT_USER_ID,
            name="Default User",
            email="default@jobradar.local",
            hashed_password="not-set",  # no auth yet
            telegram_id=None,
            is_active=True,
        )
        .on_conflict_do_nothing(index_elements=["email"])
    )
    await session.execute(stmt)
    await session.commit()
    log.info("default_user_seeded", user_id=str(DEFAULT_USER_ID))

if __name__ == "__main__":
    asyncio.run(main())