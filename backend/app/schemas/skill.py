from uuid import UUID
from pydantic import BaseModel


class SkillCreate(BaseModel):
    skill_name: str


class SkillRead(BaseModel):
    id: UUID
    skill_name: str

    model_config = {"from_attributes": True}