"""
Watchlist API — Day 5.

Company watchlist: when a watched company posts a job,
an immediate Telegram alert is fired.

Endpoints:
  POST   /watchlist/     — add a company to watch
  DELETE /watchlist/{id} — remove a watched company
  GET    /watchlist/     — list all watched companies
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.models import Watchlist
from app.schemas.watchlist import WatchlistCreate, WatchlistRead
from app.services.source_selector_service import DEFAULT_USER_ID
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("/", response_model=list[WatchlistRead])
async def list_watchlist(db: AsyncSession = Depends(get_db)):
    """List all watched companies for the default user."""
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == DEFAULT_USER_ID)
        .order_by(Watchlist.company_name)
    )
    return result.scalars().all()


@router.post("/", response_model=WatchlistRead, status_code=201)
async def add_to_watchlist(
    body: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a company to the watchlist.
    Idempotent — returns existing entry if already watched.
    """
    existing = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == DEFAULT_USER_ID,
            Watchlist.company_name.ilike(body.company_name),
        )
    )
    entry = existing.scalar_one_or_none()
    if entry:
        return entry

    entry = Watchlist(
        user_id=DEFAULT_USER_ID,
        company_name=body.company_name,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    log.info("watchlist_added", company=entry.company_name)
    return entry


@router.delete("/{watchlist_id}", status_code=204)
async def remove_from_watchlist(
    watchlist_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a company from the watchlist."""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == DEFAULT_USER_ID,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")

    await db.delete(entry)
    await db.commit()
    log.info("watchlist_removed", watchlist_id=str(watchlist_id))
