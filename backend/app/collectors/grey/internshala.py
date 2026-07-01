"""
Internshala collector.
Uses JSON-LD structured data embedded in the page — much more stable
than CSS class selectors which change frequently.
"""

import json
import re
from bs4 import BeautifulSoup
from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash

URLS = [
    ("https://internshala.com/internships/computer-science-internship/", "internship"),
    ("https://internshala.com/internships/web-development-internship/", "internship"),
    ("https://internshala.com/internships/python-internship/", "internship"),
    ("https://internshala.com/jobs/software-developer-jobs/", "full_time"),
]


class InternshalaCollector(BaseCollector):
    source_name = "Internshala"
    source_type = "scrape"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []
        seen: set[str] = set()

        async with self.get_client() as client:
            for url, job_type in URLS:
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")

                    # Strategy 1: JSON-LD structured data
                    extracted = self._extract_jsonld(soup, job_type, seen)
                    if extracted:
                        jobs.extend(extracted)
                        continue

                    # Strategy 2: broad text-based extraction
                    extracted = self._extract_broad(soup, url, job_type, seen)
                    jobs.extend(extracted)

                except Exception as e:
                    self.log.warning("internshala_url_failed", url=url, error=str(e))

        return jobs

    def _extract_jsonld(self, soup, job_type: str, seen: set) -> list[JobCreate]:
        jobs = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") not in ("JobPosting", "Internship"):
                        continue
                    title = item.get("title", "")
                    company = item.get("hiringOrganization", {}).get("name", "")
                    location_data = item.get("jobLocation", {})
                    if isinstance(location_data, list):
                        location_data = location_data[0] if location_data else {}
                    location = location_data.get("address", {}).get("addressLocality", "India")
                    url = item.get("url", "")

                    key = f"{company}|{title}"
                    if not title or key in seen:
                        continue
                    seen.add(key)

                    job_hash = make_job_hash(company, title, location)
                    jobs.append(JobCreate(
                        title=title[:255],
                        company=company[:255],
                        location=location[:255],
                        url=url,
                        source_type="scrape",
                        job_hash=job_hash,
                        country="India",
                        job_type=job_type,
                    ))
            except (json.JSONDecodeError, AttributeError):
                continue
        return jobs

    def _extract_broad(self, soup, page_url: str, job_type: str, seen: set) -> list[JobCreate]:
        jobs = []
        # Look for any container with a link that has internship/job in href
        links = soup.find_all("a", href=re.compile(r"/(internship|job)-detail/"))
        for link in links[:30]:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            url = href if href.startswith("http") else f"https://internshala.com{href}"

            # Walk up to find company name in sibling/parent text
            parent = link.find_parent(["div", "li", "article"])
            company = "Company"
            if parent:
                text_nodes = [t.strip() for t in parent.stripped_strings if t.strip()]
                company = text_nodes[1] if len(text_nodes) > 1 else "Company"

            key = f"{company}|{title}"
            if not title or key in seen:
                continue
            seen.add(key)

            job_hash = make_job_hash(company, title, "India")
            jobs.append(JobCreate(
                title=title[:255],
                company=company[:255],
                location="India",
                url=url,
                source_type="scrape",
                job_hash=job_hash,
                country="India",
                job_type=job_type,
            ))
        return jobs