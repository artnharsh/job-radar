"""
Ashby collector.

Ashby job board API:
  https://api.ashbyhq.com/posting-api/job-board/{company}

Public API — no auth required.
"""

import asyncio
from datetime import datetime

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash

COMPANIES = [
    "ramp", "rippling", "mercury", "brex", "deel", "remote",
    "lemon-squeezy", "resend", "trigger", "cal",
    "posthog", "highlight", "papermark",
]


class AshbyCollector(BaseCollector):
    source_name = "Ashby"
    source_type = "api"
    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{}"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            tasks = [self._fetch_company(client, company) for company in COMPANIES]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                continue
            jobs.extend(result)

        return jobs

    async def _fetch_company(self, client, company: str) -> list[JobCreate]:
        try:
            resp = await client.get(self.BASE_URL.format(company))
            if resp.status_code != 200:
                return []

            data = resp.json()
            jobs = []

            for item in data.get("jobs", []):
                location = item.get("location", "") or ""

                posted_at = None
                raw = item.get("publishedDate")
                if raw:
                    try:
                        posted_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass

                job_hash = make_job_hash(company, item.get("title", ""), location)

                jobs.append(JobCreate(
                    title=item.get("title", ""),
                    company=company.capitalize(),
                    location=location,
                    url=item.get("jobUrl", ""),
                    source_type="api",
                    job_hash=job_hash,
                    posted_at=posted_at,
                    is_remote=item.get("isRemote", False),
                ))

            return jobs
        except Exception:
            return []