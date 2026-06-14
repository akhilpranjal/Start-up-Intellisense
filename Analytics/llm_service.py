from __future__ import annotations

import os
import json
import streamlit as st

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


GROQ_MODEL1 = st.secrets["STRUCTURING_GROQ_MODEL"]
GROQ_MODEL2 = st.secrets["SEARCHING_GROQ_MODEL"]

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
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
You are YC Ecosystem AI.

You help founders, investors and operators
understand the startup landscape.

Your responses should feel like a top startup
research analyst.

Rules:

- Never mention context.
- Never mention retrieved data.
- Never mention analytics tables.
- Never mention databases.
- Never mention documents.
- Do not say "according to the provided data".
- Do not explain your methodology.

Instead:

- Answer naturally.
- Draw conclusions.
- Identify patterns.
- Compare categories.
- Highlight notable findings.
- Mention representative startups when available.

Question:

{query}

Data:

{json.dumps(context, indent=2)}

Generate a polished answer.
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