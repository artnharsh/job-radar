"""
Greenhouse collector.

Greenhouse hosts job boards for thousands of companies at:
  https://boards-api.greenhouse.io/v1/boards/{company}/jobs

We fetch from a curated list of top tech companies.
This is a public API — no auth, no ToS issues.
"""

import asyncio
from datetime import datetime, timezone

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash

# Top tech companies with Greenhouse job boards
COMPANIES = [
    "airbnb", "stripe", "notion", "figma", "vercel", "linear",
    "supabase", "planetscale", "retool", "brex", "ramp", "plaid",
    "robinhood", "coinbase", "databricks", "snowflake", "confluent",
    "hashicorp", "gitlab", "docker", "mongodb", "elastic",
    "twilio", "sendgrid", "segment", "mixpanel", "amplitude",
    "intercom", "zendesk", "hubspot", "asana", "monday",
]


class GreenhouseCollector(BaseCollector):
    source_name = "Greenhouse"
    source_type = "api"
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{}/jobs?content=true"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            tasks = [self._fetch_company(client, company) for company in COMPANIES]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                self.log.warning("greenhouse_company_failed", error=str(result))
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
                location = ""
                offices = item.get("offices", [])
                if offices:
                    location = offices[0].get("name", "")

                posted_at = None
                raw_date = item.get("updated_at") or item.get("created_at")
                if raw_date:
                    try:
                        posted_at = datetime.fromisoformat(
                            raw_date.replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        pass

                job_hash = make_job_hash(company, item.get("title", ""), location)

                jobs.append(JobCreate(
                    title=item.get("title", ""),
                    company=company.capitalize(),
                    location=location,
                    url=item.get("absolute_url", ""),
                    description=None,
                    source_type="api",
                    job_hash=job_hash,
                    posted_at=posted_at,
                    is_remote="remote" in location.lower(),
                ))

            return jobs

        except Exception as e:
            self.log.debug("greenhouse_fetch_failed", company=company, error=str(e))
            return []