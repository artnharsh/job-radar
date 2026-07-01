"""
Jobicy collector.

Free open API — https://jobicy.com/api/v2/remote-jobs
No auth required. Returns remote jobs.
"""

from datetime import datetime

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash


class JobicyCollector(BaseCollector):
    source_name = "Jobicy"
    source_type = "api"
    BASE_URL = "https://jobicy.com/api/v2/remote-jobs?count=50&tag=engineer"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            resp = await client.get(self.BASE_URL)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("jobs", []):
                posted_at = None
                raw = item.get("jobPubDate")
                if raw:
                    try:
                        posted_at = datetime.fromisoformat(raw)
                    except ValueError:
                        pass

                location = item.get("jobGeo", "Remote")
                job_hash = make_job_hash(
                    item.get("companyName", ""),
                    item.get("jobTitle", ""),
                    location,
                )

                jobs.append(JobCreate(
                    title=item.get("jobTitle", ""),
                    company=item.get("companyName", ""),
                    location=location,
                    url=item.get("url", ""),
                    source_type="api",
                    job_hash=job_hash,
                    posted_at=posted_at,
                    is_remote=True,
                    country=item.get("jobGeo"),
                ))

        return jobs