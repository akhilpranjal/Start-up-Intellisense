import os
import json
from groq import Groq


def extract_structured_llm(text: str, metadata: dict | None = None) -> dict:
    """Use Groq for structured extraction, with a heuristic fallback if Groq is unavailable."""

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        # Basic heuristic fallback
        from .mock_extractor import extract_structured

        return extract_structured(text)

    prompt = f"Extract startup_name, funding_stage, problem_domain, tech_stack (list), target_market, key_differentiator, sentiment_score from this text. Return JSON only. Text:\n{text[:3000]}"
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    client = Groq(api_key=groq_api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You output only JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=512,
    )
    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except Exception:
        # fallback to heuristic
        from .mock_extractor import extract_structured

        return extract_structured(text)
