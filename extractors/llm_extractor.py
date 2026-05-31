import os
import requests
import json


def extract_structured_llm(text: str, metadata: dict | None = None) -> dict:
    """Attempt to use OpenAI chat completion for structured extraction if OPENAI_API_KEY present.

    Falls back to a simple heuristic if no key is available.
    """
    if not os.getenv("OPENAI_API_KEY"):
        # Basic heuristic fallback
        from .mock_extractor import extract_structured

        return extract_structured(text)

    # Example prompt — adjust schema as needed
    prompt = f"Extract startup_name, funding_stage, problem_domain, tech_stack (list), target_market, key_differentiator, sentiment_score from this text. Return JSON only. Text:\n{text[:3000]}"
    api_key = os.getenv("OPENAI_API_KEY")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": "You output only JSON."}, {"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 512,
    }
    r = requests.post(url, headers=headers, data=json.dumps(body), timeout=20)
    r.raise_for_status()
    data = r.json()
    # Get assistant content
    content = data["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except Exception:
        # fallback to heuristic
        from .mock_extractor import extract_structured

        return extract_structured(text)
