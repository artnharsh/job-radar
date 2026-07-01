"""
APScheduler — runs collectors on a fixed interval.

Tier 1 API collectors  : every 15 minutes
Grey zone collectors   : every 30 minutes

Uses AsyncIOScheduler so it runs inside FastAPI's event loop
without blocking request handling.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.collectors.registry import TIER1_COLLECTORS, GREY_COLLECTORS
from app.database.connection import AsyncSessionLocal
from app.services.job_ingestion_service import ingest_jobs
from app.utils.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")


async def _run_collector(collector) -> None:
    """Run a single collector and ingest results into the DB."""
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
    """Called every 15 minutes by the scheduler."""
    log.info("scheduler_tier1_start", count=len(TIER1_COLLECTORS))
    for collector in TIER1_COLLECTORS:
        try:
            await _run_collector(collector)
        except Exception as e:
            log.error("scheduler_collector_crash", source=collector.source_name, error=str(e))


async def run_grey_collectors() -> None:
    """Called every 30 minutes by the scheduler."""
    log.info("scheduler_grey_start", count=len(GREY_COLLECTORS))
    for collector in GREY_COLLECTORS:
        try:
            await _run_collector(collector)
        except Exception as e:
            log.error("scheduler_collector_crash", source=collector.source_name, error=str(e))


def start_scheduler() -> None:
    scheduler.add_job(
        run_tier1_collectors,
        trigger=IntervalTrigger(minutes=settings.tier1_poll_interval_minutes),
        id="tier1_collectors",
        replace_existing=True,
        max_instances=1,  # Prevents overlap if a run takes longer than interval
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