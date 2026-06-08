from __future__ import annotations

import os
import asyncio
from typing import Any
import streamlit as st
import json
import asyncpg

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment variables")


 
# DATABASE
 

async def _get_connection():
    return await asyncpg.connect(DATABASE_URL)


def run_async(coro):
    return asyncio.run(coro)


 
# ANALYTICS
 

async def _get_metric(metric_name: str):

    conn = await _get_connection()

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

        value = row["metric_value"]

        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        return value

    finally:
        await conn.close()


@st.cache_data(ttl=3600)
def get_metric(metric_name: str):
    return run_async(
        _get_metric(metric_name)
    )


def get_overview():
    return get_metric("overview")


def get_founding_year_trend():
    return get_metric(
        "founding_year_trend"
    )


def get_country_distribution():
    return get_metric(
        "country_distribution"
    )


def get_problem_domain_distribution():
    return get_metric(
        "problem_domain_distribution"
    )


def get_target_market_distribution():
    return get_metric(
        "target_market_distribution"
    )


def get_status_distribution():
    return get_metric(
        "status_distribution"
    )


def get_team_size_distribution():
    return get_metric(
        "team_size_distribution"
    )


def get_cluster_distribution():
    return get_metric(
        "cluster_distribution"
    )


def get_cluster_growth():
    return get_metric(
        "cluster_growth"
    )


def get_emerging_clusters():
    return get_metric(
        "emerging_clusters"
    )


 
# CLUSTERS
 

async def _get_clusters():

    conn = await _get_connection()

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
            dict(row)
            for row in rows
        ]

    finally:
        await conn.close()


def get_clusters():
    return run_async(
        _get_clusters()
    )


async def _get_cluster_members(
    cluster_id: int
):

    conn = await _get_connection()

    try:

        rows = await conn.fetch(
            """
            SELECT
                name,
                website,
                one_liner,
                country,
                city,
                founded_year,
                team_size,
                status,
                cluster_confidence
            FROM yc_companies
            WHERE cluster_id = $1
            ORDER BY cluster_confidence DESC
            LIMIT 200
            """,
            cluster_id,
        )

        return [
            dict(row)
            for row in rows
        ]

    finally:
        await conn.close()


def get_cluster_members(
    cluster_id: int
):
    return run_async(
        _get_cluster_members(
            cluster_id
        )
    )


 
# LANDSCAPE MAP
 

async def _get_landscape_points():

    conn = await _get_connection()

    try:

        rows = await conn.fetch(
            """
            SELECT
                name,
                country,
                city,
                founded_year,
                cluster_id,
                umap_x,
                umap_y
            FROM yc_companies
            WHERE
                umap_x IS NOT NULL
                AND umap_y IS NOT NULL
            """
        )

        return [
            dict(row)
            for row in rows
        ]

    finally:
        await conn.close()


def get_landscape_points():
    return run_async(
        _get_landscape_points()
    )



 
# SEARCH
 

def semantic_search_wrapper(
    query: str
):
    """
    Uses existing semantic_search.py
    """

    from Analytics.semantic_search import search

    return asyncio.run(
        search(query)
    )