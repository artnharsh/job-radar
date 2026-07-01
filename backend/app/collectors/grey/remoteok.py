"""
RemoteOK collector.

RemoteOK provides a public JSON API endpoint.
Technically grey zone but has the least friction of all grey sources.
"""

from datetime import datetime, timezone

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash


class RemoteOKCollector(BaseCollector):
    source_name = "RemoteOK"
    source_type = "scrape"
    URL = "https://remoteok.com/api"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            resp = await client.get(self.URL)
            resp.raise_for_status()
            data = resp.json()

            # First item is a legal notice dict, skip it
            for item in data[1:]:
                if not isinstance(item, dict):
                    continue

                tags = item.get("tags", [])
                company = item.get("company", "")
                title = item.get("position", "")
                location = item.get("location", "Remote") or "Remote"

                posted_at = None
                ts = item.get("epoch")
                if ts:
                    try:
                        posted_at = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                    except (ValueError, TypeError):
                        pass

                job_hash = make_job_hash(company, title, location)

                jobs.append(JobCreate(
                    title=title,
                    company=company,
                    location=location,
                    url=item.get("url", ""),
                    source_type="scrape",
                    job_hash=job_hash,
                    posted_at=posted_at,
                    is_remote=True,
                    salary_min=int(item["salary_min"]) if item.get("salary_min") else None,
                    salary_max=int(item["salary_max"]) if item.get("salary_max") else None,
                ))

        return jobs