from __future__ import annotations

from Analytics.analytics_tools import (
    AnalyticsTools,
)

from Analytics.semantic_search import (
    search,
)


async def build_trend_context():

    return {
        "overview":
            await AnalyticsTools.get_overview(),

        "emerging_clusters":
            await AnalyticsTools.get_emerging_clusters(),

        "cluster_growth":
            await AnalyticsTools.get_cluster_growth(),
    }


async def build_cluster_context():

    return {
        "clusters":
            await AnalyticsTools.get_cluster_info()
    }


async def build_country_context():

    return {
        "countries":
            await AnalyticsTools.get_country_distribution(),

        "problem_domains":
            await AnalyticsTools.get_problem_domain_distribution(),
    }


async def build_hybrid_context(
    query: str,
):

    companies = await search(
        query
    )

    return {
        "companies": companies,

        "country_distribution":
            await AnalyticsTools.get_country_distribution(),

        "cluster_growth":
            await AnalyticsTools.get_cluster_growth(),

        "emerging_clusters":
            await AnalyticsTools.get_emerging_clusters(),
    }