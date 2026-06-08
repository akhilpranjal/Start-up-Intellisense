from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    PayloadSchemaType,
)

from typing import List, Dict, Any


COLLECTION_NAME = "yc_startups"


class QdrantService:
    def __init__(
        self,
        url: str,
        api_key: str,
    ):
        self.url = url
        self.api_key = api_key

        self.client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=60,
        )

    def ensure_payload_indexes(self):
        """
        Optional but useful later for filtering.
        """

        indexes = [
            ("batch", PayloadSchemaType.KEYWORD),
            ("country", PayloadSchemaType.KEYWORD),
            ("location", PayloadSchemaType.KEYWORD),
        ]

        for field_name, schema in indexes:
            try:
                self.client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=schema,
                )

                print(
                    f"Created payload index: {field_name}"
                )

            except Exception:
                # Index probably already exists
                pass

    def build_points(
        self,
        companies: List[Dict[str, Any]],
        vectors: List[List[float]],
        hashes: List[str],
        point_ids: List[int],
    ) -> List[PointStruct]:

        points = []

        for company, vector, embedding_hash, point_id in zip(
            companies,
            vectors,
            hashes,
            point_ids,
        ):
            payload = {
                "slug": company["slug"],
                "name": company["name"],
                "website": company["website"],
                "batch": company["batch"],
                "location": company["location"],
                "country": company["country"],
                "one_liner": company["one_liner"],
                "problem_domain": company["problem_domain"],
                "target_market": company["target_market"],
                "description": company["description"],
                "embedding_model": "bge-base-en-v1.5",
                "embedding_hash": embedding_hash,
            }

            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        return points

    def upsert_points(
        self,
        points: List[PointStruct],
    ):
        """
        Batch upload vectors.
        """

        if not points:
            return

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            wait=True,
            points=points,
        )

        print(
            f"Uploaded {len(points)} vectors to Qdrant."
        )