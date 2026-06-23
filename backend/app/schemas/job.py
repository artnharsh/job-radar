from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, HttpUrl, field_validator


class JobBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    url: str
    description: str | None = None
    source_name: str
    source_type: str
    job_type: str | None = None
    experience_level: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    is_remote: bool = False
    country: str | None = None
    city: str | None = None


class JobCreate(JobBase):
    job_hash: str
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


class JobListResponse(BaseModel):
    total: int
    jobs: list[JobRead]