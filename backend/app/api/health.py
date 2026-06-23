"""
Health check endpoints.
Used by Docker healthcheck, load balancers, and uptime monitors.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis

from app.database.connection import get_db
from app.utils.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@router.get("/db")
async def db_health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        log.error("db_health_failed", error=str(e))
        return {"status": "error", "database": str(e)}


@router.get("/redis")
async def redis_health():
    try:
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        log.error("redis_health_failed", error=str(e))
        return {"status": "error", "redis": str(e)}


@router.get("/full")
async def full_health(db: AsyncSession = Depends(get_db)):
    """Single endpoint that checks all dependencies."""
    results = {"app": "ok", "database": "unknown", "redis": "unknown"}

    try:
        await db.execute(text("SELECT 1"))
        results["database"] = "ok"
    except Exception as e:
        results["database"] = f"error: {e}"

    try:
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        results["redis"] = "ok"
    except Exception as e:
        results["redis"] = f"error: {e}"

    overall = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    return {"status": overall, **results}