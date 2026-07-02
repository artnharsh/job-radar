"""
Job ingestion service.

Central pipeline for inserting collected jobs into PostgreSQL.
Handles:
  - Deduplication via job_hash (SHA256)
  - last_seen update for existing jobs
  - trust_score assignment from source
  - Bulk insert for performance
  - source_health update on success/failure
  - Watchlist check + Telegram alert on new inserts (Day 5)
"""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Job, Source, Watchlist
from app.schemas.job import JobCreate
from app.services import source_health_service
from app.services.telegram_service import send_watchlist_alert
from app.services.source_selector_service import DEFAULT_USER_ID
from app.utils.hashing import make_job_hash
from app.utils.logger import get_logger

log = get_logger(__name__)


async def ingest_jobs(
    db: AsyncSession,
    jobs: list[JobCreate],
    source_name: str,
    error: Exception | None,
) -> dict:
    """
    Main ingestion entry point.
    Called by the scheduler after each collector run.

    Returns a summary dict: {inserted, skipped, source, status}
    """
    # Always update source_health regardless of result
    if error is not None:
        await source_health_service.mark_failure(
            db, source_name, str(error)
        )
        return {"inserted": 0, "skipped": 0, "source": source_name, "status": "failed"}

    await source_health_service.mark_success(db, source_name)

    if not jobs:
        return {"inserted": 0, "skipped": 0, "source": source_name, "status": "empty"}

    # Fetch source trust_score once
    source_result = await db.execute(
        select(Source).where(Source.name == source_name)
    )
    source = source_result.scalar_one_or_none()
    trust_score = source.trust_score if source else 0.5
    source_id = source.id if source else None

    inserted = 0
    skipped = 0
    now = datetime.now(timezone.utc)

    # Load watchlist once per batch — case-insensitive company names
    watchlist_result = await db.execute(
        select(Watchlist.company_name).where(Watchlist.user_id == DEFAULT_USER_ID)
    )
    watched_companies: set[str] = {
        row[0].lower().strip() for row in watchlist_result.all()
    }

    newly_inserted: list[JobCreate] = []  # track new jobs for watchlist check

    for job in jobs:
        # Ensure hash is set (collectors set it but defensive check)
        if not job.job_hash:
            job.job_hash = make_job_hash(job.company, job.title, job.location or "")

        # Try insert — skip on hash conflict (duplicate)
        stmt = (
            insert(Job)
            .values(
                title=job.title,
                company=job.company,
                location=job.location,
                url=job.url,
                description=job.description,
                source_id=source_id,
                source_name=source_name,
                source_type=job.source_type,
                job_hash=job.job_hash,
                first_seen=now,
                last_seen=now,
                posted_at=job.posted_at,
                trust_score=trust_score,
                job_type=job.job_type,
                experience_level=job.experience_level,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                is_remote=job.is_remote,
                country=job.country,
                city=job.city,
            )
            .on_conflict_do_update(
                index_elements=["job_hash"],
                set_={"last_seen": now},  # only update last_seen on duplicate
            )
        )
        result = await db.execute(stmt)

        # rowcount=1 means inserted, 0 means conflict (duplicate updated)
        if result.rowcount == 1:
            inserted += 1
            newly_inserted.append(job)
        else:
            skipped += 1

    # ── Watchlist alerts — fire AFTER commit so DB is consistent ──
    # Collect alerts to fire after commit (non-blocking)
    alerts_to_fire = []
    for job in newly_inserted:
        company_lower = job.company.lower().strip()
        for watched in watched_companies:
            if watched in company_lower or company_lower in watched:
                alerts_to_fire.append(job)
                log.info(
                    "watchlist_hit",
                    company=job.company,
                    title=job.title,
                )
                break

    await db.commit()

    # Fire Telegram alerts after commit — non-blocking
    for job in alerts_to_fire:
        asyncio.create_task(
            send_watchlist_alert(
                company=job.company,
                title=job.title,
                url=job.url,
                location=job.location,
            )
        )

    log.info(
        "ingestion_complete",
        source=source_name,
        inserted=inserted,
        skipped=skipped,
        alerts_fired=len(alerts_to_fire),
    )

    return {
        "inserted": inserted,
        "skipped": skipped,
        "source": source_name,
        "status": "ok",
        "alerts_fired": len(alerts_to_fire),
    }