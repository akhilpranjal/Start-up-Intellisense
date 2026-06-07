import json
import asyncpg

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS yc_companies (
    slug TEXT PRIMARY KEY,

    name TEXT,
    one_liner TEXT,
    description TEXT,
    website TEXT,

    batch TEXT,
    batch_code TEXT,

    founded_year INTEGER,
    team_size INTEGER,

    status TEXT,

    location TEXT,
    city TEXT,
    country TEXT,

    linkedin_url TEXT,
    twitter_url TEXT,
    github_url TEXT,

    primary_partner TEXT,

    yc_url TEXT,

    founders_json JSONB,
    tags_json JSONB,

    problem_domain TEXT,
    target_market TEXT,

    enrichment_completed BOOLEAN DEFAULT FALSE,

    embedding_completed BOOLEAN DEFAULT FALSE,
    embedding_hash TEXT,
    last_embedded_at TIMESTAMPTZ,

    raw_json JSONB,

    scraped_at TIMESTAMPTZ DEFAULT NOW()
);
"""


UPSERT_SQL = """
INSERT INTO yc_companies (
    slug,
    name,
    one_liner,
    description,
    website,

    batch,
    batch_code,

    founded_year,
    team_size,

    status,

    location,
    city,
    country,

    linkedin_url,
    twitter_url,
    github_url,

    primary_partner,

    yc_url,

    founders_json,
    tags_json,

    raw_json,

    scraped_at
)
VALUES (
    $1,$2,$3,$4,$5,
    $6,$7,
    $8,$9,
    $10,
    $11,$12,$13,
    $14,$15,$16,
    $17,
    $18,
    $19,$20,
    $21,
    NOW()
)
ON CONFLICT (slug)
DO UPDATE SET
    name = EXCLUDED.name,
    one_liner = EXCLUDED.one_liner,
    description = EXCLUDED.description,
    website = EXCLUDED.website,

    batch = EXCLUDED.batch,
    batch_code = EXCLUDED.batch_code,

    founded_year = EXCLUDED.founded_year,
    team_size = EXCLUDED.team_size,

    status = EXCLUDED.status,

    location = EXCLUDED.location,
    city = EXCLUDED.city,
    country = EXCLUDED.country,

    linkedin_url = EXCLUDED.linkedin_url,
    twitter_url = EXCLUDED.twitter_url,
    github_url = EXCLUDED.github_url,

    primary_partner = EXCLUDED.primary_partner,

    yc_url = EXCLUDED.yc_url,

    founders_json = EXCLUDED.founders_json,
    tags_json = EXCLUDED.tags_json,

    raw_json = EXCLUDED.raw_json,

    scraped_at = NOW();
"""


class YCCompanyDB:

    def __init__(self, database_url):
        self.database_url = database_url
        self.conn = None

    async def connect(self):
        self.conn = await asyncpg.connect(
            self.database_url
        )

    async def close(self):
        if self.conn:
            await self.conn.close()

    async def create_schema(self):
        await self.conn.execute(
            CREATE_TABLE_SQL
        )

    async def load_existing_slugs(self):
        rows = await self.conn.fetch(
            "SELECT slug FROM yc_companies"
        )

        return {
            row["slug"]
            for row in rows
        }

    async def save_company(
        self,
        record
    ):
        await self.conn.execute(
            UPSERT_SQL,

            record["slug"],
            record["name"],
            record["one_liner"],
            record["description"],
            record["website"],

            record["batch"],
            record["batch_code"],

            record["founded_year"],
            record["team_size"],

            record["status"],

            record["location"],
            record["city"],
            record["country"],

            record["linkedin_url"],
            record["twitter_url"],
            record["github_url"],

            record["primary_partner"],

            record["yc_url"],

            json.dumps(
                record["founders_json"]
            ),

            json.dumps(
                record["tags_json"]
            ),

            json.dumps(
                record["raw_json"]
            ),
        )