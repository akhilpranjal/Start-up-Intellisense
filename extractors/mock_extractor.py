import re

def extract_structured(text: str) -> dict:
    """Very small deterministic extractor for demos.

    It tries to find a startup name line like 'Startup: NAME' or the first Title-case phrase.
    """
    # Try simple pattern
    m = re.search(r"Startup[:\-]\s*(?P<name>[A-Z][A-Za-z0-9 &+-]{2,})", text)
    if m:
        name = m.group("name").strip()
    else:
        # fallback: first line up to 60 chars
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        name = first_line.strip()[:60]

    return {
        "startup_name": name,
        "funding_stage": "unknown",
        "problem_domain": "unspecified",
        "tech_stack": [],
        "target_market": None,
        "key_differentiator": None,
        "sentiment_score": 0.0,
    }
