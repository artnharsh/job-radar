"""
Arbeitnow collector.

Free open API — https://www.arbeitnow.com/api/job-board-api
No auth required. Strong EU + remote coverage.
"""

from datetime import datetime, timezone

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash


class ArbeitnowCollector(BaseCollector):
    source_name = "Arbeitnow"
    source_type = "api"
    BASE_URL = "https://www.arbeitnow.com/api/job-board-api?page={}"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            for page in range(1, 4):  # 3 pages = ~75 jobs
                try:
                    resp = await client.get(self.BASE_URL.format(page))
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("data", []):
                        posted_at = None
                        ts = item.get("created_at")
                        if ts:
                            try:
                                posted_at = datetime.fromtimestamp(ts, tz=timezone.utc)
                            except (ValueError, TypeError):
                                pass

                        tags = item.get("tags", [])
                        location = "Remote" if item.get("remote") else item.get("location", "")

                        job_hash = make_job_hash(
                            item.get("company_name", ""),
                            item.get("title", ""),
                            location,
                        )

                        jobs.append(JobCreate(
                            title=item.get("title", ""),
                            company=item.get("company_name", ""),
                            location=location,
                            url=item.get("url", ""),
                            description=item.get("description", "")[:500] if item.get("description") else None,
                            source_type="api",
                            job_hash=job_hash,
                            posted_at=posted_at,
                            is_remote=item.get("remote", False),
                        ))

                except Exception as e:
                    self.log.warning("arbeitnow_page_failed", page=page, error=str(e))
                    break

        return jobs