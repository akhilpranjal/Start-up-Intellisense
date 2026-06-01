from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .config import get_settings


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    id BIGSERIAL PRIMARY KEY,
    yc_slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    tags TEXT[] NOT NULL DEFAULT '{}',
    batch TEXT,
    website TEXT,
    location TEXT,
    company_url TEXT,
    raw_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    problem_domain TEXT,
    tech_stack TEXT[] NOT NULL DEFAULT '{}',
    target_market TEXT,
    one_line_summary TEXT,
    skills TEXT[] NOT NULL DEFAULT '{}',
    terms TEXT[] NOT NULL DEFAULT '{}',
    insights JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding JSONB,
    cluster_label INTEGER,
    cluster_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies (name);
CREATE INDEX IF NOT EXISTS idx_companies_batch ON companies (batch);
CREATE INDEX IF NOT EXISTS idx_companies_cluster_label ON companies (cluster_label);
"""


@contextmanager
def get_connection() -> Iterator[Any]:
    """Description:
Open a PostgreSQL connection for the current settings.
Input Description:
No direct inputs.
Output Description:
Yields a live psycopg connection with dict rows and autocommit enabled.
"""
    settings = get_settings()
    with connect(settings.database_url, autocommit=True, row_factory=dict_row) as connection:
        yield connection


def ensure_schema() -> None:
    """Description:
Create the database schema if it does not already exist.
Input Description:
No direct inputs.
Output Description:
Returns nothing after running the schema statements.
"""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in SCHEMA_SQL.strip().split(";"):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)


def fetch_all(query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    """Description:
Fetch all rows for a SQL query.
Input Description:
query is the SQL string and params is the optional parameter tuple.
Output Description:
Returns a list of row dictionaries.
"""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return list(cursor.fetchall())


def fetch_one(query: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
    """Description:
Fetch a single row for a SQL query.
Input Description:
query is the SQL string and params is the optional parameter tuple.
Output Description:
Returns one row dictionary or None when no row exists.
"""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            return dict(row) if row else None


def execute(query: str, params: tuple[Any, ...] | None = None) -> None:
    """Description:
Run a write query without returning rows.
Input Description:
query is the SQL string and params is the optional parameter tuple.
Output Description:
Returns nothing after the statement finishes.
"""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())


def upsert_scraped_company(company: dict[str, Any]) -> None:
    """Description:
Insert or update the scraped company record.
Input Description:
company is the scraped company dictionary.
Output Description:
Returns nothing after persisting the row.
"""
    execute(
        """
        INSERT INTO companies (
            yc_slug, name, description, tags, batch, website, location, company_url, raw_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (yc_slug) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            tags = EXCLUDED.tags,
            batch = EXCLUDED.batch,
            website = EXCLUDED.website,
            location = EXCLUDED.location,
            company_url = EXCLUDED.company_url,
            raw_json = EXCLUDED.raw_json,
            updated_at = NOW()
        """,
        (
            company.get("yc_slug"),
            company.get("name"),
            company.get("description"),
            company.get("tags") or [],
            company.get("batch"),
            company.get("website"),
            company.get("location"),
            company.get("company_url"),
            Jsonb(company),
        ),
    )


def update_extracted_fields(yc_slug: str, extracted: dict[str, Any]) -> None:
    """Description:
Update extracted structured fields for a company.
Input Description:
yc_slug identifies the row and extracted contains parsed fields.
Output Description:
Returns nothing after updating the row.
"""
    execute(
        """
        UPDATE companies SET
            problem_domain = %s,
            tech_stack = %s,
            target_market = %s,
            one_line_summary = %s,
            skills = %s,
            terms = %s,
            insights = %s,
            updated_at = NOW()
        WHERE yc_slug = %s
        """,
        (
            extracted.get("problem_domain"),
            extracted.get("tech_stack") or [],
            extracted.get("target_market"),
            extracted.get("one_line_summary"),
            extracted.get("skills") or [],
            extracted.get("terms") or [],
            Jsonb(extracted),
            yc_slug,
        ),
    )


def update_embedding(yc_slug: str, embedding: list[float]) -> None:
    """Description:
Store the embedding vector for a company.
Input Description:
yc_slug identifies the row and embedding is the vector list.
Output Description:
Returns nothing after saving the embedding.
"""
    execute(
        """
        UPDATE companies SET
            embedding = %s,
            updated_at = NOW()
        WHERE yc_slug = %s
        """,
        (Jsonb(embedding), yc_slug),
    )


def update_cluster(yc_slug: str, cluster_label: int, cluster_name: str) -> None:
    """Description:
Store the cluster label and name for a company.
Input Description:
yc_slug identifies the row, cluster_label is the numeric cluster, and cluster_name is the label.
Output Description:
Returns nothing after updating the row.
"""
    execute(
        """
        UPDATE companies SET
            cluster_label = %s,
            cluster_name = %s,
            updated_at = NOW()
        WHERE yc_slug = %s
        """,
        (cluster_label, cluster_name, yc_slug),
    )


def count_companies() -> int:
    """Description:
Count all stored companies.
Input Description:
No direct inputs.
Output Description:
Returns the total number of company rows.
"""
    row = fetch_one("SELECT COUNT(*) AS count FROM companies")
    return int(row["count"]) if row else 0


def latest_companies(limit: int = 15) -> list[dict[str, Any]]:
    """Description:
Return the newest company rows.
Input Description:
limit controls how many rows to fetch.
Output Description:
Returns a list of the most recently updated companies.
"""
    return fetch_all(
        """
        SELECT yc_slug, name, description, tags, batch, website, location,
               problem_domain, tech_stack, target_market, one_line_summary,
               skills, terms, cluster_label, cluster_name, updated_at
        FROM companies
        ORDER BY updated_at DESC, id DESC
        LIMIT %s
        """,
        (limit,),
    )


def companies_missing_extraction() -> list[dict[str, Any]]:
    """Description:
Return companies that still need extraction.
Input Description:
No direct inputs.
Output Description:
Returns a list of rows missing one_line_summary.
"""
    return fetch_all(
        """
        SELECT yc_slug, name, description, tags, batch, website, location, company_url
        FROM companies
        WHERE one_line_summary IS NULL OR one_line_summary = ''
        ORDER BY id ASC
        """
    )


def companies_missing_embedding() -> list[dict[str, Any]]:
    """Description:
Return companies that still need embeddings.
Input Description:
No direct inputs.
Output Description:
Returns a list of rows whose embedding column is empty.
"""
    return fetch_all(
        """
        SELECT yc_slug, name, description, one_line_summary, tags, batch, website, location,
               problem_domain, tech_stack, target_market, skills, terms
        FROM companies
        WHERE embedding IS NULL
        ORDER BY id ASC
        """
    )


def search_text(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Description:
Search companies with a simple text match.
Input Description:
query is the search text and limit controls the result count.
Output Description:
Returns a list of matching company rows.
"""
    return fetch_all(
        """
        SELECT yc_slug, name, description, tags, batch, website, location,
               problem_domain, tech_stack, target_market, one_line_summary,
               skills, terms, cluster_label, cluster_name
        FROM companies
        WHERE name ILIKE %s OR description ILIKE %s OR one_line_summary ILIKE %s
        ORDER BY updated_at DESC
        LIMIT %s
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%", limit),
    )


def top_values(column_name: str, limit: int = 10) -> list[dict[str, Any]]:
    """Description:
Return the most common values from an array column.
Input Description:
column_name selects the text array column and limit controls the result count.
Output Description:
Returns ranked label/count rows.
"""
    return fetch_all(
        f"""
        SELECT value AS label, COUNT(*)::int AS count
        FROM companies, unnest(COALESCE({column_name}, '{{}}'::text[])) AS value
        WHERE value IS NOT NULL AND value <> ''
        GROUP BY value
        ORDER BY count DESC, label ASC
        LIMIT %s
        """,
        (limit,),
    )


def cluster_groups() -> list[dict[str, Any]]:
    """Description:
Group companies by cluster label and name.
Input Description:
No direct inputs.
Output Description:
Returns cluster summary rows with counts and member names.
"""
    return fetch_all(
        """
        SELECT COALESCE(cluster_label, -1) AS cluster_label,
               COALESCE(cluster_name, 'Unclustered') AS cluster_name,
               COUNT(*)::int AS count,
               ARRAY_AGG(name ORDER BY name) AS members
        FROM companies
        GROUP BY COALESCE(cluster_label, -1), COALESCE(cluster_name, 'Unclustered')
        ORDER BY count DESC, cluster_label ASC
        """
    )
