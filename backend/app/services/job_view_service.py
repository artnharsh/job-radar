"""
Job view tracking service — Day 4.

Records when a user opens a job. Used by:
  - Day 6 daily digest (seen/unseen breakdown)
  - Day 5 priority score (deprioritise already-seen jobs)
  - UI "Seen" badge on job cards

Each view is a separate row in job_views.
We do not deduplicate views — multiple views are valid
(user might open same job multiple times before applying).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import JobView, Job
from app.services.source_selector_service import DEFAULT_USER_ID
from app.utils.logger import get_logger

log = get_logger(__name__)


async def record_view(
    db: AsyncSession,
    job_id: uuid.UUID,
    user_id: uuid.UUID = DEFAULT_USER_ID,
) -> JobView:
    """
    Record that a user viewed a job.
    Called when GET /jobs/{id} is hit.
    """
    view = JobView(
        job_id=job_id,
        user_id=user_id,
        viewed_at=datetime.now(timezone.utc),
    )
    db.add(view)
    await db.commit()
    await db.refresh(view)

    log.info("job_viewed", job_id=str(job_id), user_id=str(user_id))
    return view


async def get_viewed_job_ids(
    db: AsyncSession,
    user_id: uuid.UUID = DEFAULT_USER_ID,
) -> set[uuid.UUID]:
    """
    Returns set of job IDs the user has viewed.
    Used by the jobs list to mark seen/unseen.
    """
    result = await db.execute(
        select(JobView.job_id)
        .where(JobView.user_id == user_id)
        .distinct()
    )
    return {row[0] for row in result.all()}


async def get_view_stats(
    db: AsyncSession,
    user_id: uuid.UUID = DEFAULT_USER_ID,
) -> dict:
    """
    View statistics for daily digest (Day 6).
    Returns counts of seen/unseen/applied jobs.
    """
    # Total jobs viewed
    viewed_result = await db.execute(
        select(func.count(JobView.job_id.distinct()))
        .where(JobView.user_id == user_id)
    )
    total_viewed = viewed_result.scalar_one()

    # Total jobs in DB
    total_result = await db.execute(select(func.count()).select_from(Job))
    total_jobs = total_result.scalar_one()

    return {
        "total_jobs": total_jobs,
        "viewed": total_viewed,
        "unseen": max(0, total_jobs - total_viewed),
    }