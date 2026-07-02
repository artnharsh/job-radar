"""
Jobs API — updated Day 5.

Changes from Day 4:
  - GET /jobs/high-match  — jobs sorted by weighted priority score
  - GET /jobs/{id}        — now includes match_score, skill_gap, priority_score
  - GET /jobs/            — unchanged (all jobs, freshness + is_viewed)
  - GET /jobs/stats       — unchanged (dedupe stats)
  - POST /jobs/{id}/view  — unchanged (explicit view tracking)
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models import Job, JobView, Skill
from app.schemas.job import (
    JobRead,
    JobListResponse,
    JobReadWithMeta,
    JobReadWithScore,
    HighMatchResponse,
)
from app.services.dedupe_service import compute_freshness_score, get_dedupe_stats
from app.services.job_view_service import (
    record_view,
    get_viewed_job_ids,
    get_view_stats,
)
from app.services.match_engine import (
    compute_match_score,
    compute_skill_gap,
    compute_priority_score,
)
from app.services.source_selector_service import DEFAULT_USER_ID
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/stats")
async def job_stats(db: AsyncSession = Depends(get_db)):
    """
    Dedupe and freshness statistics.
    Shows how many jobs are stored, by source, and freshness breakdown.
    """
    dedupe = await get_dedupe_stats(db)
    views = await get_view_stats(db, DEFAULT_USER_ID)
    return {**dedupe, **views}


@router.get("/high-match", response_model=HighMatchResponse)
async def high_match_jobs(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> HighMatchResponse:
    """
    GET /jobs/high-match — Day 5.

    Returns jobs ranked by weighted priority score:
      priority = (match × 0.50) + (trust × 0.30) + (freshness × 0.20)

    Only jobs from the last 7 days are considered (freshness > 0.10).
    """
    # Fetch user skills
    skills_result = await db.execute(
        select(Skill.skill_name).where(Skill.user_id == DEFAULT_USER_ID)
    )
    user_skills: list[str] = [row[0] for row in skills_result.all()]

    # Fetch recent jobs (last 7 days) for scoring
    from datetime import timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    jobs_result = await db.execute(
        select(Job)
        .where(Job.first_seen >= cutoff)
        .order_by(Job.first_seen.desc())
        .limit(500)  # Score up to 500 recent jobs, return top `limit`
    )
    jobs = jobs_result.scalars().all()

    # Fetch viewed IDs for is_viewed flag
    viewed_ids = await get_viewed_job_ids(db, DEFAULT_USER_ID)

    # Score each job
    scored: list[tuple[float, Job, float, float, list[str]]] = []
    for job in jobs:
        freshness = compute_freshness_score(job.first_seen)
        match = compute_match_score(user_skills, job.description)
        gap = compute_skill_gap(user_skills, job.description)
        priority = compute_priority_score(match, job.trust_score, freshness)
        scored.append((priority, job, match, freshness, gap))

    # Sort by priority descending
    scored.sort(key=lambda x: x[0], reverse=True)

    result_jobs: list[JobReadWithScore] = []
    for priority, job, match, freshness, gap in scored[:limit]:
        base = JobRead.model_validate(job).model_dump()
        result_jobs.append(JobReadWithScore(
            **base,
            freshness_score=freshness,
            is_viewed=job.id in viewed_ids,
            match_score=match,
            skill_gap=gap,
            priority_score=priority,
        ))

    return HighMatchResponse(
        user_skill_count=len(user_skills),
        jobs=result_jobs,
    )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    source_type: str | None = Query(None),
    job_type: str | None = Query(None),
    experience_level: str | None = Query(None),
    is_remote: bool | None = Query(None),
    country: str | None = Query(None),
    min_salary: int | None = Query(None),
    max_salary: int | None = Query(None),
    search: str | None = Query(None),
    unseen_only: bool = Query(False, description="Only show unviewed jobs"),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:

    filters = []

    if cursor:
        filters.append(Job.first_seen < cursor)
    if source_type:
        filters.append(Job.source_type == source_type)
    if job_type:
        filters.append(Job.job_type == job_type)
    if experience_level:
        filters.append(Job.experience_level == experience_level)
    if is_remote is not None:
        filters.append(Job.is_remote == is_remote)
    if country:
        filters.append(Job.country.ilike(f"%{country}%"))
    if min_salary is not None:
        filters.append(Job.salary_min >= min_salary)
    if max_salary is not None:
        filters.append(Job.salary_max <= max_salary)
    if search:
        filters.append(
            or_(
                Job.title.ilike(f"%{search}%"),
                Job.company.ilike(f"%{search}%"),
            )
        )

    # unseen_only: exclude jobs the user has already viewed
    viewed_ids: set[uuid.UUID] = set()
    if unseen_only:
        viewed_ids = await get_viewed_job_ids(db, DEFAULT_USER_ID)
        if viewed_ids:
            filters.append(Job.id.notin_(viewed_ids))

    where_clause = and_(*filters) if filters else True

    # COUNT
    count_result = await db.execute(
        select(func.count()).select_from(Job).where(where_clause)
    )
    total = count_result.scalar_one()

    # DATA — ordered by freshness (newest first)
    data_result = await db.execute(
        select(Job)
        .where(where_clause)
        .order_by(Job.first_seen.desc())
        .limit(limit)
    )
    jobs = data_result.scalars().all()

    # Get viewed IDs for is_viewed flag (if not already fetched)
    if not unseen_only:
        viewed_ids = await get_viewed_job_ids(db, DEFAULT_USER_ID)

    # Build response with freshness scores and viewed flags
    job_list = []
    for job in jobs:
        freshness = compute_freshness_score(job.first_seen)
        is_viewed = job.id in viewed_ids
        job_list.append(JobReadWithMeta(
            **JobRead.model_validate(job).model_dump(),
            freshness_score=freshness,
            is_viewed=is_viewed,
        ))

    return JobListResponse(total=total, jobs=job_list)


@router.get("/{job_id}", response_model=JobReadWithScore)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> JobReadWithScore:
    """
    Get a single job. Automatically records a view event.
    Returns match_score and skill_gap against the user's current skills.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")

    # Record view
    await record_view(db, job_id, DEFAULT_USER_ID)

    # Fetch user skills for match scoring
    skills_result = await db.execute(
        select(Skill.skill_name).where(Skill.user_id == DEFAULT_USER_ID)
    )
    user_skills = [row[0] for row in skills_result.all()]

    freshness = compute_freshness_score(job.first_seen)
    match = compute_match_score(user_skills, job.description)
    gap = compute_skill_gap(user_skills, job.description)
    priority = compute_priority_score(match, job.trust_score, freshness)

    return JobReadWithScore(
        **JobRead.model_validate(job).model_dump(),
        freshness_score=freshness,
        is_viewed=True,  # just viewed it
        match_score=match,
        skill_gap=gap,
        priority_score=priority,
    )


@router.post("/{job_id}/view")
async def mark_viewed(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Explicitly mark a job as viewed.
    Called by frontend when user hovers or expands a job card
    without fully opening it.
    """
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")

    await record_view(db, job_id, DEFAULT_USER_ID)
    return {"status": "ok", "job_id": str(job_id)}
