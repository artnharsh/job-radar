"""
Foundit collector — uses JSON-LD + broad fallback.
"""

import json
import re
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash


class FounditCollector(BaseCollector):
    source_name = "Foundit"
    source_type = "scrape"
    URL = "https://www.foundit.in/srp/results?query=software+engineer&experience=0,3"

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

                # Strategy 2: any card with a job link
                if not jobs:
                    for link in soup.find_all("a", href=re.compile(r"/job-detail|/srp/"))[:30]:
                        title = link.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue
                        href = link.get("href", "")
                        url = href if href.startswith("http") else f"https://www.foundit.in{href}"
                        job_hash = make_job_hash("", title, "India")
                        jobs.append(JobCreate(
                            title=title[:255], company="", location="India",
                            url=url, source_type="scrape",
                            job_hash=job_hash, country="India",
                        ))

            except Exception as e:
                self.log.warning("foundit_parse_failed", error=str(e))

        return jobs