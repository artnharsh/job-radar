"""
YC Jobs collector.

YC companies post jobs via Greenhouse — we query YC's job board
which aggregates all of them. Uses public job board page.
"""

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash


class YCJobsCollector(BaseCollector):
    source_name = "YC Jobs"
    source_type = "scrape"
    URL = "https://www.ycombinator.com/jobs"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            try:
                resp = await client.get(self.URL)
                if resp.status_code != 200:
                    self.log.warning("yc_jobs_blocked", status=resp.status_code)
                    return []

                soup = BeautifulSoup(resp.text, "lxml")

                # Each job is in a <div> with role listing pattern
                listings = soup.find_all("a", href=lambda h: h and "/companies/" in h and "/jobs/" in h)

                seen = set()
                for link in listings[:80]:
                    url = link.get("href", "")
                    if not url.startswith("http"):
                        url = f"https://www.ycombinator.com{url}"

                    if url in seen:
                        continue
                    seen.add(url)

                    # Extract title and company from link text and parent
                    title = link.get_text(strip=True)
                    parent = link.find_parent(["div", "li"])
                    company = ""
                    if parent:
                        company_el = parent.find(["span", "p", "div"],
                                                  class_=lambda c: c and "company" in c.lower() if c else False)
                        if company_el:
                            company = company_el.get_text(strip=True)

                    if not title:
                        continue

                    job_hash = make_job_hash(company or "YC Company", title, "")
                    jobs.append(JobCreate(
                        title=title,
                        company=company or "YC Company",
                        location="",
                        url=url,
                        source_type="scrape",
                        job_hash=job_hash,
                    ))

            except Exception as e:
                self.log.warning("yc_jobs_parse_failed", error=str(e))

        return jobs