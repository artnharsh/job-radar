from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    url: str
    description: str | None = None
    source_name: str = ""
    source_type: str = "api"
    job_type: str | None = None
    experience_level: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    is_remote: bool = False
    country: str | None = None
    city: str | None = None


class JobCreate(JobBase):
    job_hash: str = ""
    trust_score: float = 0.5
    posted_at: datetime | None = None


class JobRead(JobBase):
    id: UUID
    job_hash: str
    trust_score: float
    first_seen: datetime
    last_seen: datetime
    posted_at: datetime | None

    model_config = {"from_attributes": True}


class JobReadWithMeta(JobRead):
    """
    Extended job response — includes computed fields
    that are not stored in the database.
    """
    freshness_score: float = 0.5
    is_viewed: bool = False


class JobReadWithScore(JobReadWithMeta):
    """
    Match-scored job response — Day 5.
    Extends JobReadWithMeta with match engine output.
    """
    match_score: float = 0.5
    skill_gap: list[str] = []
    priority_score: float = 0.5


class JobListResponse(BaseModel):
    total: int
    jobs: list[JobReadWithMeta]


class HighMatchResponse(BaseModel):
    """Response for GET /jobs/high-match — Day 5."""
    user_skill_count: int
    jobs: list[JobReadWithScore]