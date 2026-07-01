"""
Source health service.

Updates source_health table after every collection run.
Called by job_ingestion_service with success or failure result.

Status transitions:
  unknown  -> healthy  (first success)
  healthy  -> healthy  (continued success)
  healthy  -> degraded (1-2 consecutive failures)
  degraded -> failed   (3+ consecutive failures)
  failed   -> healthy  (recovery on success)
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Source, SourceHealth
from app.utils.logger import get_logger

log = get_logger(__name__)

DEGRADED_THRESHOLD = 2   # failures before degraded
FAILED_THRESHOLD = 3     # failures before failed


async def mark_success(db: AsyncSession, source_name: str) -> None:
    """Call after a collector returns jobs successfully."""
    health = await _get_or_create(db, source_name)
    if health is None:
        return

    now = datetime.now(timezone.utc)
    health.last_success = now
    health.status = "healthy"
    health.consecutive_failures = 0
    health.error_message = None

    await db.commit()
    log.info("source_health_updated", source=source_name, status="healthy")


async def mark_failure(db: AsyncSession, source_name: str, error: str) -> None:
    """Call after a collector raises an exception."""
    health = await _get_or_create(db, source_name)
    if health is None:
        return

    now = datetime.now(timezone.utc)
    health.last_failure = now
    health.consecutive_failures += 1
    health.error_message = error[:500]  # truncate very long errors

    if health.consecutive_failures >= FAILED_THRESHOLD:
        health.status = "failed"
    elif health.consecutive_failures >= DEGRADED_THRESHOLD:
        health.status = "degraded"
    else:
        health.status = "degraded"

    await db.commit()
    log.warning(
        "source_health_updated",
        source=source_name,
        status=health.status,
        consecutive_failures=health.consecutive_failures,
    )


async def _get_or_create(db: AsyncSession, source_name: str) -> SourceHealth | None:
    """
    Fetch SourceHealth by source name.
    Creates it if missing (defensive — seeder should have created it).
    """
    result = await db.execute(
        select(SourceHealth)
        .join(Source, SourceHealth.source_id == Source.id)
        .where(Source.name == source_name)
    )
    health = result.scalar_one_or_none()

    if health is None:
        # Source exists but health row is missing — create it
        source_result = await db.execute(
            select(Source).where(Source.name == source_name)
        )
        source = source_result.scalar_one_or_none()
        if source is None:
            log.error("source_not_found_in_db", source=source_name)
            return None

        health = SourceHealth(source_id=source.id, status="unknown")
        db.add(health)
        await db.flush()

    return health