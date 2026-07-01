"""
HackerNews Who's Hiring collector.

HN "Who is Hiring?" threads are posted monthly.
We fetch via the official HN API — completely public, no ToS issues.

Strategy:
  1. Find the latest "Ask HN: Who is Hiring?" post
  2. Fetch all top-level comments (each is one job posting)
  3. Parse company, role, location from comment text
"""

import re
from datetime import datetime, timezone

import httpx

from app.collectors.base import BaseCollector
from app.schemas.job import JobCreate
from app.utils.hashing import make_job_hash

HN_SEARCH_URL = (
    "https://hn.algolia.com/api/v1/search?"
    "query=Ask+HN+Who+is+Hiring&tags=story,ask_hn&hitsPerPage=1"
)
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


class HNHiringCollector(BaseCollector):
    source_name = "HackerNews"
    source_type = "api"  # Uses public API — not a scraper

    async def collect(self) -> list[JobCreate]:
        async with self.get_client() as client:
            # Step 1: Find latest hiring thread
            resp = await client.get(HN_SEARCH_URL)
            resp.raise_for_status()
            hits = resp.json().get("hits", [])

            if not hits:
                return []

            thread_id = hits[0]["objectID"]

            # Step 2: Fetch thread to get comment IDs
            resp = await client.get(HN_ITEM_URL.format(thread_id))
            resp.raise_for_status()
            thread = resp.json()

            kids = thread.get("kids", [])[:100]  # top 100 comments

            # Step 3: Fetch comments in batches
            jobs = []
            for kid_id in kids:
                try:
                    resp = await client.get(HN_ITEM_URL.format(kid_id))
                    if resp.status_code != 200:
                        continue

                    comment = resp.json()
                    if comment.get("deleted") or comment.get("dead"):
                        continue

                    text = comment.get("text", "")
                    job = self._parse_comment(text, comment)
                    if job:
                        jobs.append(job)

                except Exception:
                    continue

            return jobs

    def _parse_comment(self, text: str, comment: dict) -> JobCreate | None:
        """
        HN comments follow a loose format:
        Company | Role | Location | Remote/Onsite | ...description
        """
        if not text or len(text) < 20:
            return None

        # Strip HTML tags
        clean = re.sub(r"<[^>]+>", " ", text)
        clean = re.sub(r"&amp;", "&", clean)
        clean = re.sub(r"&lt;", "<", clean)
        clean = re.sub(r"&gt;", ">", clean)
        clean = clean.strip()

        # Try pipe-delimited first line
        first_line = clean.split("\n")[0]
        parts = [p.strip() for p in first_line.split("|")]

        company = parts[0] if parts else "Unknown"
        title = parts[1] if len(parts) > 1 else "Software Engineer"
        location = parts[2] if len(parts) > 2 else "Remote"

        is_remote = any(
            kw in clean.lower()
            for kw in ["remote", "distributed", "anywhere"]
        )

        posted_at = None
        ts = comment.get("time")
        if ts:
            try:
                posted_at = datetime.fromtimestamp(ts, tz=timezone.utc)
            except (ValueError, TypeError):
                pass

        url = f"https://news.ycombinator.com/item?id={comment.get('id', '')}"
        job_hash = make_job_hash(company, title, location)

        return JobCreate(
            title=title[:255],
            company=company[:255],
            location=location[:255],
            url=url,
            description=clean[:500],
            source_type="api",
            job_hash=job_hash,
            posted_at=posted_at,
            is_remote=is_remote,
        )