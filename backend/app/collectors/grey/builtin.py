"""
BuiltIn collector — grey zone scraper.
Targets software engineering roles.
"""

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash

CITIES = ["nyc", "chicago", "la", "seattle", "boston", "austin"]


class BuiltInCollector(BaseCollector):
    source_name = "BuiltIn"
    source_type = "scrape"
    BASE_URL = "https://builtin.com/jobs/dev-engineering"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            try:
                resp = await client.get(self.BASE_URL)
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "lxml")
                cards = soup.find_all("div", attrs={"data-id": True})

                for card in cards[:60]:
                    title_el = card.find(["a", "h2"], class_=lambda c: c and "title" in c.lower() if c else False)
                    company_el = card.find(["span", "a"], class_=lambda c: c and "company" in c.lower() if c else False)
                    location_el = card.find(["span"], class_=lambda c: c and "location" in c.lower() if c else False)

                    title = title_el.get_text(strip=True) if title_el else ""
                    company = company_el.get_text(strip=True) if company_el else ""
                    location = location_el.get_text(strip=True) if location_el else "USA"

                    if not title:
                        continue

                    link = card.find("a", href=True)
                    url = ""
                    if link:
                        href = link["href"]
                        url = href if href.startswith("http") else f"https://builtin.com{href}"

                    job_hash = make_job_hash(company, title, location)
                    jobs.append(JobCreate(
                        title=title,
                        company=company,
                        location=location,
                        url=url,
                        source_type="scrape",
                        job_hash=job_hash,
                        country="USA",
                        is_remote="remote" in location.lower(),
                    ))

            except Exception as e:
                self.log.warning("builtin_parse_failed", error=str(e))

        return jobs