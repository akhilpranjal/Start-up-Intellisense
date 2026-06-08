from __future__ import annotations

import os
import json
import asyncio
import asyncpg

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def save_metric(
    conn,
    metric_name: str,
    metric_value,
):
    await conn.execute(
        """
        INSERT INTO analytics_metrics (
            metric_name,
            metric_value,
            updated_at
        )
        VALUES (
            $1,
            $2::jsonb,
            NOW()
        )
        ON CONFLICT (metric_name)
        DO UPDATE SET
            metric_value = EXCLUDED.metric_value,
            updated_at = NOW()
        """,
        metric_name,
        json.dumps(metric_value),
    )



# OVERVIEW KPIs
async def compute_overview(conn):

    total_startups = await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM yc_companies
        """
    )

    countries = await conn.fetchval(
        """
        SELECT COUNT(DISTINCT country)
        FROM yc_companies
        WHERE country IS NOT NULL
        """
    )

    clusters = await conn.fetchval(
        """
        SELECT COUNT(*)
        FROM startup_clusters
        """
    )

    avg_team_size = await conn.fetchval(
        """
        SELECT AVG(team_size)
        FROM yc_companies
        WHERE team_size IS NOT NULL
        """
    )

    result = {
        "total_startups": total_startups,
        "countries": countries,
        "clusters": clusters,
        "avg_team_size": round(
            float(avg_team_size or 0),
            2,
        ),
    }

    await save_metric(
        conn,
        "overview",
        result,
    )




# FOUNDING YEAR TREND
async def founding_year_trend(conn):

    rows = await conn.fetch(
        """
        SELECT
            founded_year,
            COUNT(*) AS count
        FROM yc_companies
        WHERE founded_year IS NOT NULL
        GROUP BY founded_year
        ORDER BY founded_year
        """
    )

    await save_metric(
        conn,
        "founding_year_trend",
        [dict(r) for r in rows],
    )



# COUNTRY DISTRIBUTION
async def country_distribution(conn):

    rows = await conn.fetch(
        """
        SELECT
            country,
            COUNT(*) AS count
        FROM yc_companies
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY count DESC
        LIMIT 30
        """
    )

    await save_metric(
        conn,
        "country_distribution",
        [dict(r) for r in rows],
    )



# PROBLEM DOMAIN DISTRIBUTION
async def problem_domain_distribution(conn):

    rows = await conn.fetch(
        """
        SELECT
            problem_domain,
            COUNT(*) AS count
        FROM yc_companies
        WHERE problem_domain IS NOT NULL
        GROUP BY problem_domain
        ORDER BY count DESC
        LIMIT 30
        """
    )

    await save_metric(
        conn,
        "problem_domain_distribution",
        [dict(r) for r in rows],
    )



# TARGET MARKET DISTRIBUTION
async def target_market_distribution(conn):

    rows = await conn.fetch(
        """
        SELECT
            target_market,
            COUNT(*) AS count
        FROM yc_companies
        WHERE target_market IS NOT NULL
        GROUP BY target_market
        ORDER BY count DESC
        LIMIT 30
        """
    )

    await save_metric(
        conn,
        "target_market_distribution",
        [dict(r) for r in rows],
    )



# STARTUP STATUS
async def status_distribution(conn):

    rows = await conn.fetch(
        """
        SELECT
            status,
            COUNT(*) AS count
        FROM yc_companies
        WHERE status IS NOT NULL
        GROUP BY status
        ORDER BY count DESC
        """
    )

    await save_metric(
        conn,
        "status_distribution",
        [dict(r) for r in rows],
    )




# TEAM SIZE HISTOGRAM
async def team_size_distribution(conn):

    rows = await conn.fetch(
        """
        SELECT team_size
        FROM yc_companies
        WHERE team_size IS NOT NULL
        """
    )

    values = [r["team_size"] for r in rows]

    await save_metric(
        conn,
        "team_size_distribution",
        values,
    )




# CLUSTER DISTRIBUTION
async def cluster_distribution(conn):

    rows = await conn.fetch(
        """
        SELECT
            sc.cluster_name,
            sc.cluster_id,
            COUNT(*) AS count
        FROM yc_companies yc
        JOIN startup_clusters sc
        ON yc.cluster_id = sc.cluster_id
        GROUP BY
            sc.cluster_id,
            sc.cluster_name
        ORDER BY count DESC
        """
    )

    await save_metric(
        conn,
        "cluster_distribution",
        [dict(r) for r in rows],
    )



# CLUSTER GROWTH TRENDS
async def cluster_growth(conn):

    rows = await conn.fetch(
        """
        SELECT
            yc.cluster_id,
            sc.cluster_name,
            yc.founded_year,
            COUNT(*) AS count
        FROM yc_companies yc
        JOIN startup_clusters sc
        ON yc.cluster_id = sc.cluster_id
        WHERE founded_year IS NOT NULL
        GROUP BY
            yc.cluster_id,
            sc.cluster_name,
            yc.founded_year
        ORDER BY
            yc.cluster_id,
            yc.founded_year
        """
    )

    await save_metric(
        conn,
        "cluster_growth",
        [dict(r) for r in rows],
    )




# EMERGING CLUSTERS
async def emerging_clusters(conn):

    rows = await conn.fetch(
        """
        SELECT
            sc.cluster_name,
            COUNT(*) FILTER (
                WHERE founded_year >= 2023
            ) AS recent_count,

            COUNT(*) AS total_count

        FROM yc_companies yc
        JOIN startup_clusters sc
        ON yc.cluster_id = sc.cluster_id

        GROUP BY sc.cluster_name
        """
    )

    result = []

    for r in rows:

        total = r["total_count"]

        if total == 0:
            continue

        score = (
            r["recent_count"] / total
        )

        result.append(
            {
                "cluster_name": r["cluster_name"],
                "growth_score": round(
                    score,
                    4,
                ),
                "recent_count": r["recent_count"],
                "total_count": total,
            }
        )

    result.sort(
        key=lambda x: x["growth_score"],
        reverse=True,
    )

    await save_metric(
        conn,
        "emerging_clusters",
        result[:20],
    )



# MAIN
async def main():

    conn = await asyncpg.connect(
        DATABASE_URL
    )

    try:

        await compute_overview(conn)

        await founding_year_trend(conn)

        await country_distribution(conn)

        await problem_domain_distribution(conn)

        await target_market_distribution(conn)

        await status_distribution(conn)

        await team_size_distribution(conn)

        await cluster_distribution(conn)

        await cluster_growth(conn)

        await emerging_clusters(conn)

        print(
            "Analytics generated."
        )

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())