"""
Wellfound collector — uses __NEXT_DATA__ JSON embedded in page.
Much more stable than CSS class selectors.
"""

import json
from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash
from bs4 import BeautifulSoup


class WellfoundCollector(BaseCollector):
    source_name = "Wellfound"
    source_type = "scrape"
    URL = "https://wellfound.com/role/r/software-engineer"

    async def collect(self) -> list[JobCreate]:
        jobs: list[JobCreate] = []

        async with self.get_client() as client:
            try:
                resp = await client.get(self.URL)
                if resp.status_code != 200:
                    self.log.warning("wellfound_blocked", status=resp.status_code)
                    return []

                soup = BeautifulSoup(resp.text, "lxml")

                # Try __NEXT_DATA__ first
                next_data = soup.find("script", id="__NEXT_DATA__")
                if next_data:
                    try:
                        data = json.loads(next_data.string or "")
                        # Walk the props tree to find job listings
                        listings = self._find_jobs_in_tree(data)
                        for item in listings[:50]:
                            title = item.get("title", "") or item.get("role", "")
                            company = item.get("company", {})
                            if isinstance(company, dict):
                                company = company.get("name", "")
                            location = item.get("locationNames", ["Remote"])
                            if isinstance(location, list):
                                location = location[0] if location else "Remote"
                            url = item.get("jobUrl", "") or item.get("url", "")
                            if not url.startswith("http"):
                                url = f"https://wellfound.com{url}"
                            if not title:
                                continue
                            job_hash = make_job_hash(str(company), title, str(location))
                            jobs.append(JobCreate(
                                title=title[:255],
                                company=str(company)[:255],
                                location=str(location),
                                url=url,
                                source_type="scrape",
                                job_hash=job_hash,
                                is_remote="remote" in str(location).lower(),
                            ))
                    except (json.JSONDecodeError, Exception):
                        pass

                # Fallback: any link with /jobs/ in href
                if not jobs:
                    for link in soup.find_all("a", href=lambda h: h and "/jobs/" in h)[:40]:
                        title = link.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue
                        href = link["href"]
                        url = href if href.startswith("http") else f"https://wellfound.com{href}"
                        job_hash = make_job_hash("", title, "Remote")
                        jobs.append(JobCreate(
                            title=title[:255], company="", location="Remote",
                            url=url, source_type="scrape",
                            job_hash=job_hash, is_remote=True,
                        ))

            except Exception as e:
                self.log.warning("wellfound_parse_failed", error=str(e))

        return jobs

    def _find_jobs_in_tree(self, obj, depth=0) -> list:
        """Recursively search JSON tree for job listing arrays."""
        if depth > 8:
            return []
        if isinstance(obj, list) and obj and isinstance(obj[0], dict):
            if any(k in obj[0] for k in ("title", "role", "jobUrl")):
                return obj
        if isinstance(obj, dict):
            for v in obj.values():
                result = self._find_jobs_in_tree(v, depth + 1)
                if result:
                    return result
        return []