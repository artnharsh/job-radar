from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator


class WatchlistCreate(BaseModel):
    company_name: str

    @field_validator("company_name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("company_name cannot be empty")
        return v


class WatchlistRead(BaseModel):
    id: UUID
    company_name: str
    created_at: datetime

    model_config = {"from_attributes": True}
