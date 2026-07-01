"""
Sources API.

Endpoints:
  GET  /sources/          List all sources with health status
  GET  /sources/health    Source health dashboard
  POST /sources/select    Enable or disable a source for the default user
  POST /sources/mode      Apply a preset mode (trusted/india/remote/all/custom)

Day 3 uses a single default user seeded at startup.
Auth wired properly in Day 6.
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models import Source, SourceHealth, UserSource, User
from app.schemas.source import SourceRead, SourceWithHealth, SourceHealthRead
from app.services.source_selector_service import (
    get_or_create_user_sources,
    set_source_enabled,
    apply_mode,
    DEFAULT_USER_ID,
)
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/sources", tags=["sources"])


# ── Request schemas ───────────────────────────────────────────────

class SourceSelectRequest(BaseModel):
    source_id: uuid.UUID
    is_enabled: bool


class SourceModeRequest(BaseModel):
    mode: Literal["all", "trusted", "india", "remote", "custom"]
    # Only used when mode = "custom"
    source_ids: list[uuid.UUID] = []


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/", response_model=list[SourceWithHealth])
async def list_sources(db: AsyncSession = Depends(get_db)):
    """
    List all sources with their health status and whether the
    default user has them enabled.
    """
    # Ensure user_sources rows exist for all sources
    await get_or_create_user_sources(db, DEFAULT_USER_ID)

    result = await db.execute(
        select(Source, SourceHealth, UserSource)
        .outerjoin(SourceHealth, SourceHealth.source_id == Source.id)
        .outerjoin(
            UserSource,
            and_(
                UserSource.source_id == Source.id,
                UserSource.user_id == DEFAULT_USER_ID,
            ),
        )
        .order_by(Source.tier, Source.name)
    )

    rows = result.all()
    sources = []

    for source, health, user_source in rows:
        health_data = None
        if health:
            health_data = SourceHealthRead.model_validate(health)

        sources.append(SourceWithHealth(
            id=source.id,
            name=source.name,
            tier=source.tier,
            trust_score=source.trust_score,
            poll_interval=source.poll_interval,
            is_active=source.is_active,
            is_enabled=user_source.is_enabled if user_source else True,
            health=health_data,
        ))

    return sources


@router.get("/health", response_model=list[SourceHealthRead])
async def sources_health(db: AsyncSession = Depends(get_db)):
    """
    Source health dashboard.
    Returns health status for all sources sorted by status severity.
    Failed first, then degraded, then healthy.
    """
    result = await db.execute(
        select(SourceHealth, Source.name, Source.tier)
        .join(Source, SourceHealth.source_id == Source.id)
        .order_by(
            # Show problems first
            SourceHealth.consecutive_failures.desc(),
            Source.tier,
        )
    )

    rows = result.all()
    health_list = []

    for health, source_name, tier in rows:
        item = SourceHealthRead.model_validate(health)
        item.source_name = source_name
        item.tier = tier
        health_list.append(item)

    return health_list


@router.post("/select")
async def select_source(
    body: SourceSelectRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Enable or disable a single source for the default user.
    """
    await set_source_enabled(db, DEFAULT_USER_ID, body.source_id, body.is_enabled)
    action = "enabled" if body.is_enabled else "disabled"
    log.info("source_toggled", source_id=str(body.source_id), action=action)
    return {"status": "ok", "source_id": str(body.source_id), "is_enabled": body.is_enabled}


@router.post("/mode")
async def set_mode(
    body: SourceModeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Apply a preset source mode.

    all     — enable every source
    trusted — enable Tier 1 API sources only
    india   — enable India-focused sources only
    remote  — enable remote-focused sources only
    custom  — enable only the source_ids provided in the request
    """
    updated = await apply_mode(db, DEFAULT_USER_ID, body.mode, body.source_ids)
    log.info("source_mode_applied", mode=body.mode, updated=updated)
    return {"status": "ok", "mode": body.mode, "sources_updated": updated}


@router.get("/tiers")
async def get_tiers(db: AsyncSession = Depends(get_db)):
    """
    Returns sources grouped by tier — used by the frontend
    to render the source selector organised by tier.
    """
    result = await db.execute(
        select(Source).order_by(Source.tier, Source.name)
    )
    sources = result.scalars().all()

    tiers: dict[int, list] = {}
    for source in sources:
        tier = source.tier
        if tier not in tiers:
            tiers[tier] = []
        tiers[tier].append(SourceRead.model_validate(source))

    return tiers