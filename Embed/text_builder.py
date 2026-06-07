# Build the embedding text
# Compute SHA256 hash
# Generate deterministic Qdrant point IDs from slug

import hashlib
from typing import Dict, Any


def clean_text(value: str | None) -> str:
    """
    Convert None values to empty strings
    and remove extra whitespace.
    """

    if value is None:
        return ""

    return str(value).strip()


def build_embedding_text(company: Dict[str, Any]) -> str:
    """
    Create the text that will actually be embedded.
    """

    name = clean_text(company.get("name"))
    one_liner = clean_text(company.get("one_liner"))
    problem_domain = clean_text(company.get("problem_domain"))
    target_market = clean_text(company.get("target_market"))
    description = clean_text(company.get("description"))

    parts = [
        f"Company: {name}",
        "",
        "One-line Summary:",
        one_liner,
        "",
        "Problem Domain:",
        problem_domain,
        "",
        "Target Market:",
        target_market,
        "",
        "Description:",
        description,
    ]

    return "\n".join(parts).strip()


def compute_embedding_hash(text: str) -> str:
    """
    SHA256 hash used to detect changes.
    """

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def generate_qdrant_point_id(slug: str) -> int:
    """
    Qdrant point IDs should be deterministic.

    Same slug => same point ID forever.
    """

    digest = hashlib.md5(
        slug.encode("utf-8")
    ).hexdigest()

    return int(
        digest[:15],
        16,
    )