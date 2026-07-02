"""
Match Engine — Day 5.

Computes:
  - match_score   : how well user skills match a job description
  - skill_gap     : skills the user is missing for a specific job
  - priority_score: weighted composite = (match×0.50) + (trust×0.30) + (freshness×0.20)

Skill extraction uses a curated keyword list. No ML required.
Fast, explainable, and accurate enough for Day 5.
"""

import re
from typing import Sequence

# ── Curated tech skill keyword list ───────────────────────────────
# Lowercase. Matched case-insensitively with word boundaries.
SKILL_KEYWORDS: set[str] = {
    # Languages
    "python", "javascript", "typescript", "java", "golang", "go",
    "rust", "c++", "c#", "ruby", "php", "swift", "kotlin", "scala",
    "r", "matlab", "perl", "elixir", "clojure", "haskell",
    # Web frameworks
    "react", "vue", "angular", "next.js", "nextjs", "svelte",
    "fastapi", "django", "flask", "express", "spring", "rails",
    "laravel", "nestjs", "nuxt",
    # Data / ML
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "spark", "kafka", "airflow", "dbt", "mlflow", "hugging face",
    "langchain", "openai", "llm", "machine learning", "deep learning",
    "nlp", "computer vision", "data science",
    # Databases
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "neo4j", "bigquery",
    "snowflake", "clickhouse",
    # Cloud / DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "ansible", "ci/cd", "github actions", "jenkins", "helm",
    "linux", "bash", "shell", "nginx", "prometheus", "grafana",
    # API / Architecture
    "rest", "graphql", "grpc", "microservices", "event-driven",
    "rabbitmq", "celery", "websocket",
    # Mobile
    "ios", "android", "flutter", "react native",
    # Testing
    "pytest", "jest", "selenium", "cypress", "unit testing",
    # Security
    "oauth", "jwt", "ssl", "tls",
    # Methodologies
    "agile", "scrum", "git",
}


def _extract_skills_from_text(text: str) -> set[str]:
    """
    Find all known skill keywords present in the given text.
    Case-insensitive, whole-word matching.
    Returns lowercase skill names.
    """
    if not text:
        return set()

    text_lower = text.lower()
    found: set[str] = set()

    for skill in SKILL_KEYWORDS:
        # Build a regex pattern that matches the skill as a whole word/phrase
        pattern = r"(?<![a-z0-9\-])" + re.escape(skill) + r"(?![a-z0-9\-])"
        if re.search(pattern, text_lower):
            found.add(skill)

    return found


def compute_match_score(
    user_skills: Sequence[str],
    job_description: str | None,
) -> float:
    """
    Compute how well the user's skills match a job posting.

    Score = matched_skills / required_skills_in_description

    Returns:
      0.5  — if no description (neutral / unknown)
      0.0  — if description has skills but user has none matching
      1.0  — if user has all skills mentioned in the description
    """
    if not job_description or not job_description.strip():
        return 0.5  # No data → neutral

    required = _extract_skills_from_text(job_description)

    if not required:
        return 0.5  # Description exists but no recognised skills → neutral

    user_set = {s.lower().strip() for s in user_skills}
    matched = required & user_set

    score = len(matched) / len(required)
    return round(min(max(score, 0.0), 1.0), 4)


def compute_skill_gap(
    user_skills: Sequence[str],
    job_description: str | None,
) -> list[str]:
    """
    Return skills found in the job description that the user does NOT have.
    Sorted alphabetically for consistent output.
    """
    if not job_description:
        return []

    required = _extract_skills_from_text(job_description)
    user_set = {s.lower().strip() for s in user_skills}

    gap = required - user_set
    return sorted(gap)


def compute_priority_score(
    match_score: float,
    trust_score: float,
    freshness_score: float,
) -> float:
    """
    Weighted priority score combining all three signals.

    Formula: (match × 0.50) + (trust × 0.30) + (freshness × 0.20)

    Weights rationale:
      Match (50%)     — most important: relevant to user's actual skills
      Trust (30%)     — source reliability: LinkedIn > random scraper
      Freshness (20%) — recency: recent jobs more likely still open

    Returns float in [0.0, 1.0].
    """
    raw = (match_score * 0.50) + (trust_score * 0.30) + (freshness_score * 0.20)
    return round(min(max(raw, 0.0), 1.0), 4)
