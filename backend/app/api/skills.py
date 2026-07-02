"""
Skills API — Day 5.

Provides CRUD for user skills used by the match engine.

Endpoints:
  POST   /skills/     — add a skill
  DELETE /skills/{id} — remove a skill
  GET    /skills/     — list all user skills
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models import Skill
from app.schemas.skill import SkillCreate, SkillRead
from app.services.source_selector_service import DEFAULT_USER_ID
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/", response_model=list[SkillRead])
async def list_skills(db: AsyncSession = Depends(get_db)):
    """List all skills for the default user."""
    result = await db.execute(
        select(Skill)
        .where(Skill.user_id == DEFAULT_USER_ID)
        .order_by(Skill.skill_name)
    )
    return result.scalars().all()


@router.post("/", response_model=SkillRead, status_code=201)
async def add_skill(
    body: SkillCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a skill for the default user.
    Silently returns existing skill if already present (idempotent).
    """
    # Check if skill already exists (case-insensitive)
    existing = await db.execute(
        select(Skill).where(
            Skill.user_id == DEFAULT_USER_ID,
            Skill.skill_name.ilike(body.skill_name.strip()),
        )
    )
    skill = existing.scalar_one_or_none()
    if skill:
        return skill

    skill = Skill(
        user_id=DEFAULT_USER_ID,
        skill_name=body.skill_name.strip(),
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)

    log.info("skill_added", skill=skill.skill_name)
    return skill


@router.delete("/{skill_id}", status_code=204)
async def remove_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a skill by its UUID."""
    result = await db.execute(
        select(Skill).where(
            Skill.id == skill_id,
            Skill.user_id == DEFAULT_USER_ID,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    await db.delete(skill)
    await db.commit()
    log.info("skill_removed", skill_id=str(skill_id))
