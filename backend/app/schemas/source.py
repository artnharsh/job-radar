from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class SourceRead(BaseModel):
    id: UUID
    name: str
    tier: int
    trust_score: float
    poll_interval: int
    is_active: bool

    model_config = {"from_attributes": True}


class SourceHealthRead(BaseModel):
    source_id: UUID
    status: str
    last_success: datetime | None
    last_failure: datetime | None
    error_message: str | None
    consecutive_failures: int

    model_config = {"from_attributes": True}


class SourceWithHealth(SourceRead):
    health: SourceHealthRead | None = None