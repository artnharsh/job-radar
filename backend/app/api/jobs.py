from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models import Job
from app.schemas.job import JobRead, JobListResponse
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


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

    where_clause = and_(*filters) if filters else True

    # COUNT query — uses SQL COUNT not Python len()
    count_result = await db.execute(
        select(func.count()).select_from(Job).where(where_clause)
    )
    total = count_result.scalar_one()

    # DATA query
    data_result = await db.execute(
        select(Job)
        .where(where_clause)
        .order_by(Job.first_seen.desc())
        .limit(limit)
    )
    jobs = data_result.scalars().all()

    return JobListResponse(total=total, jobs=list(jobs))


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> JobRead:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return job