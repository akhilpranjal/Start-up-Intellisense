from __future__ import annotations

import os
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


GROQ_MODEL1 = os.getenv("STRUCTURING_GROQ_MODEL")
GROQ_MODEL2 = os.getenv("SEARCHING_GROQ_MODEL")

client = Groq(
    api_key=os.getenv(
        "GROQ_API_KEY"
    )
)


def classify_query(
    query: str,
):

    prompt = f"""
Classify the query.

Return JSON only.

Possible intents:

company_search
trend_analysis
cluster_analysis
country_analysis
hybrid_analysis

Query:
{query}
"""

    response = client.chat.completions.create(
        model=f"{GROQ_MODEL1}",
        temperature=0,
        response_format={
            "type":"json_object"
        },
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return json.loads(
        response
        .choices[0]
        .message
        .content
    )


def synthesize_answer(
    query: str,
    context,
):

    prompt = f"""
You are a startup ecosystem analyst.

Answer ONLY from the context.

If information is missing,
say so.

QUESTION:

{query}

CONTEXT:

{json.dumps(
    context,
    indent=2,
    default=str
)}
"""

    response = client.chat.completions.create(
        model=f"{GROQ_MODEL2}",
        temperature=0.1,
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return (
        response
        .choices[0]
        .message
        .content
    )