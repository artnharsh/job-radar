"""
TimesJobs collector.
SSL cert issue fixed by disabling verification for this source only.
Uses broad selectors since TimesJobs HTML is fairly stable.
"""

import re
import ssl
import httpx
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash
from app.utils.user_agents import get_headers


class TimesJobsCollector(BaseCollector):
    source_name = "TimesJobs"
    source_type = "scrape"
    URL = "https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords=software+engineer&txtLocation="

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        # TimesJobs has SSL cert issues — disable verification for this source
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            async with httpx.AsyncClient(
                headers=get_headers(),
                timeout=httpx.Timeout(15.0, connect=5.0),
                follow_redirects=True,
                verify=False,          # TimesJobs cert chain is broken
            ) as client:
                resp = await client.get(self.URL)
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "lxml")

                # TimesJobs uses <li class="clearfix"> for job cards
                cards = soup.find_all("li", class_="clearfix")

                for card in cards[:40]:
                    # Title is in <h2><a>
                    h2 = card.find("h2")
                    title_link = h2.find("a") if h2 else None
                    title = title_link.get_text(strip=True) if title_link else ""
                    url = title_link.get("href", "") if title_link else ""

                    # Company in class containing "comp-name"
                    company_el = card.find(class_=re.compile(r"comp.name|company", re.I))
                    company = company_el.get_text(strip=True) if company_el else ""

                    # Location
                    loc_el = card.find(class_=re.compile(r"location|loc", re.I))
                    location = loc_el.get_text(strip=True) if loc_el else "India"

                    if not title:
                        continue

                    job_hash = make_job_hash(company, title, location)
                    jobs.append(JobCreate(
                        title=title[:255],
                        company=company[:255],
                        location=location[:255],
                        url=url,
                        source_type="scrape",
                        job_hash=job_hash,
                        country="India",
                    ))

        except Exception as e:
            self.log.warning("timesjobs_parse_failed", error=str(e))

        return jobs