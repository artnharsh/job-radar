"""
Adzuna collector.

Developer API — requires ADZUNA_APP_ID and ADZUNA_APP_KEY from .env
Sign up free: https://developer.adzuna.com

Good India coverage via /in/ endpoint.
Also hits /us/ for US jobs.
"""

from datetime import datetime

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.config import settings
from app.utils.hashing import make_job_hash

SEARCHES = [
    {"country": "in", "what": "software engineer", "country_name": "India"},
    {"country": "in", "what": "backend developer", "country_name": "India"},
    {"country": "in", "what": "frontend developer", "country_name": "India"},
    {"country": "us", "what": "software engineer", "country_name": "USA"},
    {"country": "us", "what": "backend engineer", "country_name": "USA"},
]


class AdzunaCollector(BaseCollector):
    source_name = "Adzuna"
    source_type = "api"
    BASE_URL = (
        "https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        "?app_id={app_id}&app_key={app_key}"
        "&results_per_page=20&what={what}&content-type=application/json"
    )

    async def collect(self) -> list[JobCreate]:
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            self.log.warning("adzuna_credentials_missing")
            return []

        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            for search in SEARCHES:
                try:
                    url = self.BASE_URL.format(
                        country=search["country"],
                        app_id=settings.adzuna_app_id,
                        app_key=settings.adzuna_app_key,
                        what=search["what"].replace(" ", "+"),
                    )
                    resp = await client.get(url)
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("results", []):
                        location = item.get("location", {}).get("display_name", "")
                        company = item.get("company", {}).get("display_name", "")

                        posted_at = None
                        raw = item.get("created")
                        if raw:
                            try:
                                posted_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                            except ValueError:
                                pass

                        job_hash = make_job_hash(company, item.get("title", ""), location)

                        jobs.append(JobCreate(
                            title=item.get("title", ""),
                            company=company,
                            location=location,
                            url=item.get("redirect_url", ""),
                            description=item.get("description", "")[:500] if item.get("description") else None,
                            source_type="api",
                            job_hash=job_hash,
                            posted_at=posted_at,
                            country=search["country_name"],
                            is_remote="remote" in location.lower(),
                            salary_min=int(item["salary_min"]) if item.get("salary_min") else None,
                            salary_max=int(item["salary_max"]) if item.get("salary_max") else None,
                        ))

                except Exception as e:
                    self.log.warning("adzuna_search_failed", search=search, error=str(e))
                    continue

        return jobs