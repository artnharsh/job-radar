"""
Remotive collector.

Free open REST API — https://remotive.com/api/remote-jobs
No auth, no rate limiting mentioned.
Returns remote tech jobs globally.
"""

from datetime import datetime

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash

CATEGORIES = [
    "software-dev", "devops-sysadmin", "data",
    "product", "backend", "frontend", "fullstack",
]


class RemotiveCollector(BaseCollector):
    source_name = "Remotive"
    source_type = "api"
    BASE_URL = "https://remotive.com/api/remote-jobs?category={}&limit=50"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            for category in CATEGORIES:
                try:
                    resp = await client.get(self.BASE_URL.format(category))
                    if resp.status_code != 200:
                        continue

                    data = resp.json()

                    for item in data.get("jobs", []):
                        posted_at = None
                        raw = item.get("publication_date")
                        if raw:
                            try:
                                posted_at = datetime.fromisoformat(raw)
                            except ValueError:
                                pass

                        job_hash = make_job_hash(
                            item.get("company_name", ""),
                            item.get("title", ""),
                            item.get("candidate_required_location", "Remote"),
                        )

                        jobs.append(JobCreate(
                            title=item.get("title", ""),
                            company=item.get("company_name", ""),
                            location=item.get("candidate_required_location", "Remote"),
                            url=item.get("url", ""),
                            description=item.get("description", "")[:500] if item.get("description") else None,
                            source_type="api",
                            job_hash=job_hash,
                            posted_at=posted_at,
                            is_remote=True,
                            job_type=self._map_job_type(item.get("job_type", "")),
                        ))

                except Exception as e:
                    self.log.warning("remotive_category_failed", category=category, error=str(e))
                    continue

        return jobs

    @staticmethod
    def _map_job_type(raw: str) -> str | None:
        raw = raw.lower()
        if "full" in raw:
            return "full_time"
        if "part" in raw:
            return "part_time"
        if "contract" in raw:
            return "contract"
        return None