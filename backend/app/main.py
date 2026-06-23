"""
FastAPI application entry point.

Startup sequence:
  1. Logging configured
  2. CORS middleware attached
  3. Routers registered
  4. Redis connection verified on startup event
"""

from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.utils.config import settings
from app.utils.logger import get_logger, setup_logging

setup_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────
    log.info("startup", env=settings.app_env, version=settings.app_version)

    # Verify Redis is reachable
    try:
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        log.info("redis_connected")
    except Exception as e:
        log.error("redis_connection_failed", error=str(e))

    yield

    # ── Shutdown ──────────────────────────────────────────────────
    log.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)

# Day 2+ routers registered here as they're built:
# app.include_router(jobs.router)
# app.include_router(users.router)
# app.include_router(sources.router)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }