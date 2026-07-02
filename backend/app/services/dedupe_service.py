"""
Dedupe service — Day 4.

Provides utilities to check and report deduplication stats.
The actual dedup logic lives in job_ingestion_service.py via
ON CONFLICT DO UPDATE — this service adds observability on top.

Also provides freshness scoring used by Day 5 priority engine.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Job
from app.utils.logger import get_logger

log = get_logger(__name__)


def compute_freshness_score(first_seen: datetime | None) -> float:
    """
    Freshness score based on how recently the job was first seen.

    Score   | Age
    --------|--------------------
    1.00    | < 1 hour
    0.90    | 1-6 hours
    0.75    | 6-24 hours
    0.50    | 1-3 days
    0.25    | 3-7 days
    0.10    | > 7 days

    Returns 0.5 as default if first_seen is None.
    """
    if first_seen is None:
        return 0.5

    now = datetime.now(timezone.utc)

    # Normalise timezone — first_seen may be naive UTC from DB
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=timezone.utc)

    age = now - first_seen

    if age < timedelta(hours=1):
        return 1.00
    elif age < timedelta(hours=6):
        return 0.90
    elif age < timedelta(hours=24):
        return 0.75
    elif age < timedelta(days=3):
        return 0.50
    elif age < timedelta(days=7):
        return 0.25
    else:
        return 0.10


async def get_dedupe_stats(db: AsyncSession) -> dict:
    """
    Returns deduplication statistics.
    Useful for the dashboard and for demonstrating the system works.
    """
    # Total jobs stored
    total_result = await db.execute(select(func.count()).select_from(Job))
    total = total_result.scalar_one()

    # Jobs by source
    source_result = await db.execute(
        select(Job.source_name, func.count().label("count"))
        .group_by(Job.source_name)
        .order_by(func.count().desc())
    )
    by_source = {row.source_name: row.count for row in source_result.all()}

    # Jobs seen in last 24 hours (freshness indicator)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_result = await db.execute(
        select(func.count()).select_from(Job).where(Job.first_seen >= cutoff)
    )
    recent_24h = recent_result.scalar_one()

    # Jobs still active (last_seen within 24h)
    active_result = await db.execute(
        select(func.count()).select_from(Job).where(Job.last_seen >= cutoff)
    )
    active_24h = active_result.scalar_one()

    return {
        "total_jobs": total,
        "jobs_by_source": by_source,
        "new_last_24h": recent_24h,
        "still_active_24h": active_24h,
    }