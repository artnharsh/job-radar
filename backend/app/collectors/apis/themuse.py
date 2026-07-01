"""
The Muse collector.

Free public API — https://www.themuse.com/api/public/jobs
No auth required for basic access.
"""

from datetime import datetime

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash


class TheMuseCollector(BaseCollector):
    source_name = "TheMuse"
    source_type = "api"
    BASE_URL = "https://www.themuse.com/api/public/jobs?category=Engineering&page={}&descending=true"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            for page in range(1, 4):
                try:
                    resp = await client.get(self.BASE_URL.format(page))
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("results", []):
                        company = item.get("company", {}).get("name", "")
                        locations = item.get("locations", [])
                        location = locations[0].get("name", "") if locations else "Remote"

                        levels = item.get("levels", [])
                        experience_level = None
                        if levels:
                            lvl = levels[0].get("short_name", "").lower()
                            if "entry" in lvl or "junior" in lvl:
                                experience_level = "entry"
                            elif "mid" in lvl or "senior" not in lvl:
                                experience_level = "mid"
                            elif "senior" in lvl:
                                experience_level = "senior"

                        posted_at = None
                        raw = item.get("publication_date")
                        if raw:
                            try:
                                posted_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                            except ValueError:
                                pass

                        job_hash = make_job_hash(company, item.get("name", ""), location)

                        jobs.append(JobCreate(
                            title=item.get("name", ""),
                            company=company,
                            location=location,
                            url=item.get("refs", {}).get("landing_page", ""),
                            source_type="api",
                            job_hash=job_hash,
                            posted_at=posted_at,
                            experience_level=experience_level,
                            is_remote="flexible" in location.lower() or "remote" in location.lower(),
                        ))

                except Exception as e:
                    self.log.warning("themuse_page_failed", page=page, error=str(e))
                    break

        return jobs