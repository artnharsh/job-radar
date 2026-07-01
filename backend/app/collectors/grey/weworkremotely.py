"""
WeWorkRemotely collector — grey zone scraper.
One of the oldest remote job boards.
"""

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash

SECTIONS = [
    "https://weworkremotely.com/categories/remote-programming-jobs",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs",
]


class WeWorkRemotelyCollector(BaseCollector):
    source_name = "WeWorkRemotely"
    source_type = "scrape"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []
        seen = set()

        async with self.get_client() as client:
            for url in SECTIONS:
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")
                    listings = soup.find_all("li", class_=lambda c: c and "feature" not in c if c else True)

                    for li in listings[:40]:
                        link = li.find("a", href=lambda h: h and "/remote-jobs/" in h)
                        if not link:
                            continue

                        href = link.get("href", "")
                        job_url = f"https://weworkremotely.com{href}" if not href.startswith("http") else href

                        if job_url in seen:
                            continue
                        seen.add(job_url)

                        company_el = li.find("span", class_="company")
                        title_el = li.find("span", class_="title")
                        region_el = li.find("span", class_="region")

                        company = company_el.get_text(strip=True) if company_el else ""
                        title = title_el.get_text(strip=True) if title_el else ""
                        location = region_el.get_text(strip=True) if region_el else "Remote"

                        if not title:
                            continue

                        job_hash = make_job_hash(company, title, location)
                        jobs.append(JobCreate(
                            title=title,
                            company=company,
                            location=location,
                            url=job_url,
                            source_type="scrape",
                            job_hash=job_hash,
                            is_remote=True,
                        ))

                except Exception as e:
                    self.log.warning("wwr_section_failed", url=url, error=str(e))

        return jobs