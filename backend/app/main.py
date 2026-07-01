import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api import jobs
from app.api import source
from app.scheduler.job_scheduler import (
    start_scheduler,
    run_tier1_collectors,
    run_grey_collectors,
)
from app.utils.config import settings
from app.utils.logger import get_logger, setup_logging

setup_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", env=settings.app_env, version=settings.app_version)

    try:
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        log.info("redis_connected")
    except Exception as e:
        log.error("redis_connection_failed", error=str(e))

    start_scheduler()

    # Fire initial collection immediately without blocking startup
    asyncio.create_task(run_tier1_collectors())
    asyncio.create_task(run_grey_collectors())
    log.info("initial_collection_triggered")

    yield
    log.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(source.router)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }