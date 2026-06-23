"""
Hashing utilities.

job_hash   — SHA256 fingerprint of (company + title + location).
             Used for deduplication. Same job from two sources
             produces the same hash and is stored only once.
"""

import hashlib


def make_job_hash(company: str, title: str, location: str) -> str:
    """
    Deterministic SHA256 fingerprint for a job posting.
    Normalise to lowercase + stripped to survive minor formatting
    differences between sources.
    """
    raw = "|".join([
        company.lower().strip(),
        title.lower().strip(),
        location.lower().strip(),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def make_url_hash(url: str) -> str:
    """
    Secondary fingerprint based on URL.
    Used as fallback when company/title/location are not yet parsed.
    """
    return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()