"""
Source selector service.

Manages which sources are enabled per user.
Day 3 operates on a single DEFAULT_USER_ID.
Auth integration in Day 6 replaces DEFAULT_USER_ID with real user.

Mode definitions:
  all     — all sources enabled
  trusted — Tier 1 only (public APIs, zero legal risk)
  india   — Tier 4 (Internshala, Foundit, Shine, TimesJobs)
            + Adzuna India results
  remote  — Remotive, RemoteOK, WeWorkRemotely, Arbeitnow, Jobicy
  custom  — caller provides explicit list of source_ids
"""

import uuid
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Source, UserSource
from app.utils.logger import get_logger

log = get_logger(__name__)

# Single default user UUID — stable across restarts
# Replaced by real user_id in Day 6
DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# Mode → which tiers or source names are enabled
MODE_TIERS: dict[str, list[int]] = {
    "all":     [1, 2, 3, 4, 5],
    "trusted": [1],
    "india":   [4],
    "remote":  [],  # handled by name filter below
}

REMOTE_SOURCE_NAMES = {
    "Remotive", "RemoteOK", "WeWorkRemotely", "Arbeitnow", "Jobicy"
}

INDIA_EXTRA_NAMES = {
    "Adzuna"  # Adzuna covers India via /in/ endpoint
}


async def get_or_create_user_sources(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    """
    Ensure every source has a user_sources row for this user.
    Idempotent — safe to call on every request.
    Uses INSERT ON CONFLICT DO NOTHING.
    """
    result = await db.execute(select(Source))
    all_sources = result.scalars().all()

    for source in all_sources:
        stmt = (
            insert(UserSource)
            .values(
                id=uuid.uuid4(),
                user_id=user_id,
                source_id=source.id,
                is_enabled=True,  # default: all enabled
            )
            .on_conflict_do_nothing(
                index_elements=["user_id", "source_id"]
            )
        )
        await db.execute(stmt)

    await db.commit()


async def set_source_enabled(
    db: AsyncSession,
    user_id: uuid.UUID,
    source_id: uuid.UUID,
    is_enabled: bool,
) -> None:
    """Toggle a single source on or off for this user."""
    await get_or_create_user_sources(db, user_id)

    await db.execute(
        update(UserSource)
        .where(
            UserSource.user_id == user_id,
            UserSource.source_id == source_id,
        )
        .values(is_enabled=is_enabled)
    )
    await db.commit()


async def apply_mode(
    db: AsyncSession,
    user_id: uuid.UUID,
    mode: str,
    custom_ids: list[uuid.UUID] = [],
) -> int:
    """
    Apply a preset mode — sets is_enabled for all sources.
    Returns count of sources updated.
    """
    await get_or_create_user_sources(db, user_id)

    result = await db.execute(select(Source))
    all_sources = result.scalars().all()

    updated = 0

    for source in all_sources:
        if mode == "all":
            enabled = True

        elif mode == "trusted":
            enabled = source.tier == 1

        elif mode == "india":
            enabled = (
                source.tier == 4
                or source.name in INDIA_EXTRA_NAMES
            )

        elif mode == "remote":
            enabled = source.name in REMOTE_SOURCE_NAMES

        elif mode == "custom":
            enabled = source.id in custom_ids

        else:
            enabled = True  # fallback

        await db.execute(
            update(UserSource)
            .where(
                UserSource.user_id == user_id,
                UserSource.source_id == source.id,
            )
            .values(is_enabled=enabled)
        )
        updated += 1

    await db.commit()
    return updated


async def get_enabled_source_names(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> set[str]:
    """
    Returns the set of source names currently enabled for this user.
    Used by the scheduler in Day 4+ to filter which collectors run.
    """
    result = await db.execute(
        select(Source.name)
        .join(UserSource, UserSource.source_id == Source.id)
        .where(
            UserSource.user_id == user_id,
            UserSource.is_enabled == True,
        )
    )
    return {row[0] for row in result.all()}