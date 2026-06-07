from sentence_transformers import SentenceTransformer
from typing import List
import asyncpg
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# Create asyncpg pool
# Fetch companies needing embeddings
# Bulk update embedded companies
# Close pool cleanly
class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=1,
            max_size=10,
        )

    async def close(self):
        if self.pool:
            await self.pool.close()

    async def fetch_companies_for_embedding(
        self,
        batch_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch companies that:
        - have enrichment completed
        - are not yet embedded
        """

        query = """
        SELECT
            slug,
            name,
            one_liner,
            description,
            website,
            batch,
            location,
            country,
            problem_domain,
            target_market,
            embedding_hash
        FROM yc_companies
        WHERE
            enrichment_completed = TRUE
            AND COALESCE(embedding_completed, FALSE) = FALSE
        ORDER BY slug
        LIMIT $1
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, batch_size)

        return [dict(row) for row in rows]

    async def mark_companies_embedded(
        self,
        updates: List[tuple[str, str]],
    ):
        """
        updates:
        [
            (slug, embedding_hash),
            ...
        ]
        """

        query = """
        UPDATE yc_companies
        SET
            embedding_completed = TRUE,
            embedding_hash = $2,
            last_embedded_at = NOW()
        WHERE slug = $1
        """

        async with self.pool.acquire() as conn:
            async with conn.transaction():

                await conn.executemany(
                    query,
                    updates,
                )


# Load BGE model once
# Keep model in memory
# Batch encode texts
# Normalize embeddings
# Return Python lists for Qdrant
class EmbeddingService:
    def __init__(
        self,
        model_name: str = f"{EMBEDDING_MODEL}",
    ):
        self.model_name = model_name
        self.model = None

    def load(self):
        """
        Load model once at startup.
        """

        print(
            f"Loading embedding model: {self.model_name}"
        )

        self.model = SentenceTransformer(
            self.model_name
        )

        print("Embedding model loaded.")

    def embed_documents(
        self,
        texts: List[str],
        batch_size: int = 64,
    ) -> List[List[float]]:
        """
        Embed company documents.
        """

        if self.model is None:
            raise RuntimeError(
                "Model not loaded. Call load() first."
            )

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        return embeddings.tolist()

    def embed_query(
        self,
        query: str,
    ) -> List[float]:
        """
        Future semantic search helper.

        BGE performs better when queries
        are prefixed with an instruction.
        """

        if self.model is None:
            raise RuntimeError(
                "Model not loaded. Call load() first."
            )

        formatted_query = (
            "Represent this sentence for searching "
            f"relevant startups: {query}"
        )

        embedding = self.model.encode(
            formatted_query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embedding.tolist()