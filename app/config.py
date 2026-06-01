from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Description:
Store the project configuration loaded from environment variables.
Input Description:
No runtime inputs; values come from the process environment.
Output Description:
Provides immutable settings fields for database, vector store, and LLM access.
"""
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/startups")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "startups")
    yc_url: str = os.getenv("YC_URL", "https://www.ycombinator.com/companies")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    extraction_mode: str = os.getenv("EXTRACTION_MODE", "groq")
    cluster_min_size: int = int(os.getenv("CLUSTER_MIN_SIZE", "5"))
    admin_token: str = os.getenv("ADMIN_TOKEN", "")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Description:
Return the cached Settings instance.
Input Description:
No direct inputs.
Output Description:
Returns a Settings object loaded once per process.
"""
    return Settings()
