from __future__ import annotations

import os
import json
import asyncpg

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


class AnalyticsTools:

    @staticmethod
    async def _get_metric(
        metric_name: str,
    ):
        conn = await asyncpg.connect(
            DATABASE_URL
        )

        try:

            row = await conn.fetchrow(
                """
                SELECT metric_value
                FROM analytics_metrics
                WHERE metric_name = $1
                """,
                metric_name,
            )

            if not row:
                return None

            return row["metric_value"]

        finally:
            await conn.close()

    @staticmethod
    async def get_overview():
        return await AnalyticsTools._get_metric(
            "overview"
        )

    @staticmethod
    async def get_emerging_clusters():
        return await AnalyticsTools._get_metric(
            "emerging_clusters"
        )

    @staticmethod
    async def get_cluster_growth():
        return await AnalyticsTools._get_metric(
            "cluster_growth"
        )

    @staticmethod
    async def get_country_distribution():
        return await AnalyticsTools._get_metric(
            "country_distribution"
        )

    @staticmethod
    async def get_problem_domain_distribution():
        return await AnalyticsTools._get_metric(
            "problem_domain_distribution"
        )

    @staticmethod
    async def get_target_market_distribution():
        return await AnalyticsTools._get_metric(
            "target_market_distribution"
        )

    @staticmethod
    async def get_cluster_distribution():
        return await AnalyticsTools._get_metric(
            "cluster_distribution"
        )

    @staticmethod
    async def get_cluster_info():

        conn = await asyncpg.connect(
            DATABASE_URL
        )

        try:

            rows = await conn.fetch(
                """
                SELECT
                    cluster_id,
                    cluster_name,
                    description,
                    keywords,
                    company_count
                FROM startup_clusters
                ORDER BY company_count DESC
                """
            )

            return [
                dict(r)
                for r in rows
            ]

        finally:
            await conn.close()

    @staticmethod
    async def get_representative_companies(
        cluster_id: int,
        limit: int = 5,
    ):
        conn = await asyncpg.connect(
            DATABASE_URL
        )

        try:

            rows = await conn.fetch(
                """
                SELECT
                    name,
                    website,
                    one_liner,
                    problem_domain,
                    target_market,
                    country
                FROM yc_companies
                WHERE cluster_id = $1
                LIMIT $2
                """,
                cluster_id,
                limit,
            )

            return [
                dict(r)
                for r in rows
            ]

        finally:
            await conn.close()