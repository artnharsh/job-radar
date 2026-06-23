from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    job_id: UUID
    status: str = "saved"


class ApplicationRead(BaseModel):
    id: UUID
    job_id: UUID
    status: str
    applied_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicationUpdate(BaseModel):
    status: str