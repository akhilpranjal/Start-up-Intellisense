from __future__ import annotations

import json
from collections import Counter
from typing import Any

from groq import Groq

from .config import get_settings


def _clean_list(values: Any) -> list[str]:
    """Description:
Normalize loose list-like values into a list of strings.
Input Description:
values may be a list, comma-separated string, or empty value.
Output Description:
Returns a cleaned list of non-empty strings.
"""
    if isinstance(values, list):
        return [str(value).strip() for value in values if str(value).strip()]
    if isinstance(values, str) and values.strip():
        return [item.strip() for item in values.split(",") if item.strip()]
    return []


def _load_json(content: str) -> dict[str, Any]:
    """Description:
Extract and parse a JSON object from model output.
Input Description:
content is the raw text returned by the model.
Output Description:
Returns a dictionary when parsing succeeds, otherwise an empty dict.
"""
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _fallback_extraction(name: str, description: str, tags: list[str]) -> dict[str, Any]:
    """Description:
Build a simple structured fallback when LLM extraction is unavailable.
Input Description:
name, description, and tags come from the scraped company row.
Output Description:
Returns a dictionary with starter structured fields.
"""
    words = [word.strip(".,:;()[]{}") for word in (description or name).split() if word.strip()]
    summary = " ".join(words[:18]).strip()
    if len(words) > 18:
        summary += "..."
    return {
        "problem_domain": tags[0] if tags else "",
        "tech_stack": tags[:5],
        "target_market": "",
        "one_line_summary": summary or name,
        "skills": tags[:5],
        "terms": tags[:5],
        "insights": [],
    }


def extract_company_fields(name: str, description: str, tags: list[str]) -> dict[str, Any]:
    """Description:
Extract structured company fields from a YC description.
Input Description:
name, description, and tags identify the startup text to analyze.
Output Description:
Returns normalized structured fields for storage.
"""
    settings = get_settings()
    if settings.extraction_mode.lower() == "mock" or not settings.groq_api_key:
        return _fallback_extraction(name, description, tags)

    client = Groq(api_key=settings.groq_api_key)
    prompt = f"""
Return JSON only.

Extract these fields for a YC startup:
- problem_domain: short string
- tech_stack: array of strings
- target_market: short string
- one_line_summary: one simple sentence
- skills: array of strings
- terms: array of strings
- insights: array of short bullet-like strings

Company name: {name}
Tags: {', '.join(tags)}
Description: {description}
""".strip()

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": "You extract structured startup data and always return valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    data = _load_json(content)
    return {
        "problem_domain": str(data.get("problem_domain", "")).strip(),
        "tech_stack": _clean_list(data.get("tech_stack")),
        "target_market": str(data.get("target_market", "")).strip(),
        "one_line_summary": str(data.get("one_line_summary", "")).strip() or name,
        "skills": _clean_list(data.get("skills")),
        "terms": _clean_list(data.get("terms")),
        "insights": data.get("insights", []),
    }


def name_cluster(members: list[dict[str, Any]], cluster_label: int) -> str:
    """Description:
Generate a short human-friendly cluster name.
Input Description:
members contains example companies and cluster_label identifies the cluster.
Output Description:
Returns a concise cluster name string.
"""
    settings = get_settings()
    if cluster_label < 0:
        return "Noise"

    names = [member.get("name", "") for member in members[:8]]
    summaries = [member.get("one_line_summary", "") for member in members[:8]]
    domains = [member.get("problem_domain", "") for member in members[:8]]

    if not settings.groq_api_key or settings.extraction_mode.lower() == "mock":
        counts = Counter(value for value in domains + names if value)
        if counts:
            return counts.most_common(1)[0][0][:40]
        return f"Cluster {cluster_label}"

    client = Groq(api_key=settings.groq_api_key)
    prompt = f"""
Name this startup cluster in 2 to 4 words.
Return JSON only with key: name.

Members:
{json.dumps([{"name": name, "summary": summary, "domain": domain} for name, summary, domain in zip(names, summaries, domains)], ensure_ascii=True)}
""".strip()

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": "You name startup clusters in short, clear language."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    data = _load_json(content)
    name = str(data.get("name", "")).strip()
    return name or f"Cluster {cluster_label}"
