from __future__ import annotations

from Analytics.semantic_search import (
    search,
)

from Analytics.llm_service import (
    classify_query,
    synthesize_answer,
)

from Analytics.context_builders import (
    build_trend_context,
    build_cluster_context,
    build_country_context,
    build_hybrid_context,
)


async def ask_ecosystem(
    query: str,
):

    routing = classify_query(
        query
    )

    intent = routing[
        "intent"
    ]

    if intent == "company_search":

        results = await search(
            query
        )

        return {
            "intent":
                intent,

            "results":
                results,
        }

    if intent == "trend_analysis":

        context = await build_trend_context()

    elif intent == "cluster_analysis":

        context = await build_cluster_context()

    elif intent == "country_analysis":

        context = await build_country_context()

    else:

        context = await build_hybrid_context(
            query
        )

    answer = synthesize_answer(
        query,
        context,
    )

    return {
        "intent":
            intent,

        "answer":
            answer,

        "sources":
            context,
    }