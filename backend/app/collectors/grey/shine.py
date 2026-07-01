"""
Shine.com collector — JSON-LD + broad fallback.
Shine now uses Next.js so CSS classes are hashed. JSON-LD is stable.
"""

import json
import re
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash


class ShineCollector(BaseCollector):
    source_name = "Shine"
    source_type = "scrape"
    URL = "https://www.shine.com/job-search/software-engineer-jobs"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            try:
                resp = await client.get(self.URL)
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "lxml")

                # Strategy 1: JSON-LD
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string or "")
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            if item.get("@type") != "JobPosting":
                                continue
                            title = item.get("title", "")
                            company = item.get("hiringOrganization", {}).get("name", "")
                            location = item.get("jobLocation", {}).get("address", {}).get("addressLocality", "India")
                            url = item.get("url", self.URL)
                            if not title:
                                continue
                            job_hash = make_job_hash(company, title, location)
                            jobs.append(JobCreate(
                                title=title[:255], company=company[:255],
                                location=location, url=url,
                                source_type="scrape", job_hash=job_hash, country="India",
                            ))
                    except (json.JSONDecodeError, AttributeError):
                        continue

                # Strategy 2: __NEXT_DATA__ JSON embedded in page
                if not jobs:
                    next_data = soup.find("script", id="__NEXT_DATA__")
                    if next_data:
                        try:
                            data = json.loads(next_data.string or "")
                            job_list = (
                                data.get("props", {})
                                .get("pageProps", {})
                                .get("jobList", [])
                            )
                            for item in job_list[:40]:
                                title = item.get("jobTitle", "") or item.get("title", "")
                                company = item.get("companyName", "") or item.get("company", "")
                                location = item.get("location", "India")
                                url = item.get("jobUrl", "") or item.get("url", self.URL)
                                if not title:
                                    continue
                                job_hash = make_job_hash(company, title, location)
                                jobs.append(JobCreate(
                                    title=title[:255], company=company[:255],
                                    location=location, url=url,
                                    source_type="scrape", job_hash=job_hash, country="India",
                                ))
                        except (json.JSONDecodeError, KeyError):
                            pass

            except Exception as e:
                self.log.warning("shine_parse_failed", error=str(e))

        return jobs