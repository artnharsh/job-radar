"""
Base collector class.

Every collector (API or scraper) inherits from BaseCollector.
It enforces a consistent interface and handles:
  - source_health updates on success/failure
  - structured logging
  - common HTTP client setup with timeouts and retries

Subclasses must implement:
    async def collect(self) -> list[JobCreate]
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx

from app.schemas.job import JobCreate
from app.utils.logger import get_logger
from app.utils.user_agents import get_headers

log = get_logger(__name__)

# Shared timeout config — all collectors use this
REQUEST_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


class BaseCollector(ABC):
    """
    Abstract base for all job collectors.

    Attributes:
        source_name : Must match exactly the name in the sources table
        source_type : "api" for Tier 1, "scrape" for grey zone
    """

    source_name: str = ""
    source_type: str = "api"

    def __init__(self) -> None:
        self.log = get_logger(self.__class__.__name__)

    def get_client(self, extra_headers: dict | None = None) -> httpx.AsyncClient:
        """
        Returns a configured async HTTP client.
        Grey zone collectors get browser-like headers.
        API collectors only need Accept: application/json.
        """
        if self.source_type == "scrape":
            headers = get_headers()
        else:
            headers = {
                "Accept": "application/json",
                "User-Agent": "JobRadarAI/1.0 (job aggregator; contact: admin@jobradar.ai)",
            }

        if extra_headers:
            headers.update(extra_headers)

        return httpx.AsyncClient(
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )

    @abstractmethod
    async def collect(self) -> list[JobCreate]:
        """
        Fetch jobs from the source.
        Must return a list of JobCreate objects.
        Returns empty list on failure — never raises.
        """
        ...

    async def safe_collect(self) -> tuple[list[JobCreate], Exception | None]:
        """
        Wraps collect() with error handling.
        Returns (jobs, None) on success.
        Returns ([], exception) on failure.
        Caller uses this to update source_health.
        """
        try:
            jobs = await self.collect()
            self.log.info(
                "collector_success",
                source=self.source_name,
                count=len(jobs),
            )
            return jobs, None
        except Exception as e:
            self.log.error(
                "collector_failed",
                source=self.source_name,
                error=str(e),
                exc_info=True,
            )
            return [], e