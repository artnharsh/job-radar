"""
Lever collector.

Lever hosts job boards at:
  https://api.lever.co/v0/postings/{company}?mode=json

Public API — no auth required.
"""

import asyncio
from datetime import datetime, timezone

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash

COMPANIES = [
    "netflix", "uber", "lyft", "reddit", "pinterest", "dropbox",
    "atlassian", "canva", "clickup", "notion", "loom", "airtable",
    "scale-ai", "openai", "anthropic", "cohere", "huggingface",
    "cloudflare", "fastly", "datadog", "pagerduty", "grafana",
    "dbt-labs", "airbyte", "starburst", "fivetran",
]


class LeverCollector(BaseCollector):
    source_name = "Lever"
    source_type = "api"
    BASE_URL = "https://api.lever.co/v0/postings/{}?mode=json"

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

            for item in data:
                categories = item.get("categories", {})
                location = categories.get("location", "") or item.get("workplaceType", "")
                commitment = categories.get("commitment", "")

                job_type = None
                if commitment:
                    c = commitment.lower()
                    if "full" in c:
                        job_type = "full_time"
                    elif "part" in c:
                        job_type = "part_time"
                    elif "intern" in c:
                        job_type = "internship"
                    elif "contract" in c:
                        job_type = "contract"

                posted_at = None
                ts = item.get("createdAt")
                if ts:
                    try:
                        posted_at = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                    except (ValueError, TypeError):
                        pass

                job_hash = make_job_hash(company, item.get("text", ""), location)

                jobs.append(JobCreate(
                    title=item.get("text", ""),
                    company=company.capitalize(),
                    location=location,
                    url=item.get("hostedUrl", ""),
                    description=item.get("descriptionPlain", "")[:500] if item.get("descriptionPlain") else None,
                    source_type="api",
                    job_hash=job_hash,
                    posted_at=posted_at,
                    job_type=job_type,
                    is_remote="remote" in location.lower(),
                ))

            return jobs

        except Exception:
            return []