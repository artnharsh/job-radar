"""
APScheduler — updated Day 4.

Changes from Day 2:
  - Reads enabled sources from user_sources before each run
  - Skips collectors for disabled sources
  - Logs skipped sources explicitly
"""

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.collectors.registry import TIER1_COLLECTORS, GREY_COLLECTORS
from app.database.connection import AsyncSessionLocal
from app.services.job_ingestion_service import ingest_jobs
from app.services.source_selector_service import (
    get_enabled_source_names,
    DEFAULT_USER_ID,
)
from app.utils.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")


async def _run_collector(collector, enabled_sources: set[str]) -> None:
    """
    Run a single collector if it is enabled for the default user.
    Skips disabled sources silently (logged at debug level).
    """
    if collector.source_name not in enabled_sources:
        log.debug("collector_skipped_disabled", source=collector.source_name)
        return

    log.info("collector_start", source=collector.source_name)
    jobs, error = await collector.safe_collect()

    async with AsyncSessionLocal() as db:
        result = await ingest_jobs(db, jobs, collector.source_name, error)

    log.info(
        "collector_done",
        source=collector.source_name,
        inserted=result["inserted"],
        skipped=result["skipped"],
        status=result["status"],
    )


async def run_tier1_collectors() -> None:
    """Called every 15 minutes."""
    async with AsyncSessionLocal() as db:
        enabled = await get_enabled_source_names(db, DEFAULT_USER_ID)

    log.info(
        "scheduler_tier1_start",
        total=len(TIER1_COLLECTORS),
        enabled=len([c for c in TIER1_COLLECTORS if c.source_name in enabled]),
    )

    for collector in TIER1_COLLECTORS:
        try:
            await _run_collector(collector, enabled)
        except Exception as e:
            log.error(
                "scheduler_collector_crash",
                source=collector.source_name,
                error=str(e),
            )


async def run_grey_collectors() -> None:
    """Called every 30 minutes."""
    async with AsyncSessionLocal() as db:
        enabled = await get_enabled_source_names(db, DEFAULT_USER_ID)

    log.info(
        "scheduler_grey_start",
        total=len(GREY_COLLECTORS),
        enabled=len([c for c in GREY_COLLECTORS if c.source_name in enabled]),
    )

    for collector in GREY_COLLECTORS:
        try:
            await _run_collector(collector, enabled)
        except Exception as e:
            log.error(
                "scheduler_collector_crash",
                source=collector.source_name,
                error=str(e),
            )


def start_scheduler() -> None:
    scheduler.add_job(
        run_tier1_collectors,
        trigger=IntervalTrigger(minutes=settings.tier1_poll_interval_minutes),
        id="tier1_collectors",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        run_grey_collectors,
        trigger=IntervalTrigger(minutes=settings.greytier_poll_interval_minutes),
        id="grey_collectors",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    log.info(
        "scheduler_started",
        tier1_interval=settings.tier1_poll_interval_minutes,
        grey_interval=settings.greytier_poll_interval_minutes,
    )