import asyncio
import os

from dotenv import load_dotenv

from embeddings import EmbeddingService, Database
from qdrant_service import QdrantService
from text_builder import (
    build_embedding_text,
    compute_embedding_hash,
    generate_qdrant_point_id,
)

# Configuration
FETCH_BATCH_SIZE = 100


# Environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL missing")

if not QDRANT_URL:
    raise ValueError("QDRANT_URL missing")

if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY missing")



# Main

async def main():

    print("\nStarting embedding pipeline...\n")


    # PostgreSQL

    db = Database(DATABASE_URL)

    await db.connect()

    print("Connected to PostgreSQL.")


    # Embeddings

    embedding_service = EmbeddingService()

    embedding_service.load()


    # Qdrant

    qdrant = QdrantService(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    qdrant.ensure_collection()

    qdrant.ensure_payload_indexes()

    print("Connected to Qdrant.")

    total_processed = 0

    try:

        while True:

            companies = (
                await db.fetch_companies_for_embedding(
                    batch_size=FETCH_BATCH_SIZE
                )
            )

            if not companies:

                print(
                    "\nNo more companies left to embed."
                )

                break

            print(
                f"\nFetched {len(companies)} companies."
            )

            embedding_texts = []
            hashes = []
            point_ids = []

            for company in companies:

                embedding_text = build_embedding_text(
                    company
                )

                embedding_hash = (
                    compute_embedding_hash(
                        embedding_text
                    )
                )

                point_id = (
                    generate_qdrant_point_id(
                        company["slug"]
                    )
                )

                embedding_texts.append(
                    embedding_text
                )

                hashes.append(
                    embedding_hash
                )

                point_ids.append(
                    point_id
                )

            print(
                "Generating embeddings..."
            )

            vectors = (
                embedding_service.embed_documents(
                    embedding_texts,
                    batch_size=64,
                )
            )

            print(
                f"Generated {len(vectors)} embeddings."
            )

            points = qdrant.build_points(
                companies=companies,
                vectors=vectors,
                hashes=hashes,
                point_ids=point_ids,
            )

            qdrant.upsert_points(points)

            updates = [
                (
                    company["slug"],
                    embedding_hash,
                )
                for company, embedding_hash
                in zip(companies, hashes)
            ]

            await db.mark_companies_embedded(
                updates
            )

            total_processed += len(companies)

            print(
                f"Total processed: {total_processed}"
            )

    finally:

        await db.close()

        print(
            "\nDatabase connection closed."
        )

    print(
        f"\nEmbedding pipeline finished."
    )

    print(
        f"Total companies embedded: "
        f"{total_processed}"
    )


if __name__ == "__main__":
    asyncio.run(main())