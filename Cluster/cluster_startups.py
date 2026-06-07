from __future__ import annotations

import os
from collections import defaultdict
from typing import List

import numpy as np
import asyncpg
import hdbscan
import umap

from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

COLLECTION_NAME = "yc_startups"

DATABASE_URL = os.getenv("DATABASE_URL")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def load_vectors():
    """
    Load all startup vectors from Qdrant.
    """

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    points = []
    offset = None

    while True:

        records, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,
            with_vectors=True,
            with_payload=True,
            offset=offset,
        )

        points.extend(records)

        if offset is None:
            break

    slugs: List[str] = []
    vectors: List[List[float]] = []

    for point in points:

        slug = point.payload.get("slug")

        if not slug:
            continue

        slugs.append(slug)
        vectors.append(point.vector)

    return slugs, np.array(vectors, dtype=np.float32)


def build_umap(vectors: np.ndarray):
    reducer = umap.UMAP(
        n_neighbors=15,
        min_dist=0.0,
        n_components=15,
        metric="cosine",
    )

    return reducer.fit_transform(vectors)


def run_hdbscan(vectors: np.ndarray):

    vectors = normalize(vectors)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=8,
        min_samples=3,
        metric="euclidean",
        prediction_data=True,
    )

    labels = clusterer.fit_predict(vectors)

    return labels, clusterer.probabilities_


def build_cluster_centroids(
    vectors: np.ndarray,
    labels: np.ndarray,
):
    """
    Build centroid for each non-outlier cluster
    using original embedding vectors.
    """

    buckets = defaultdict(list)

    for vector, label in zip(vectors, labels):

        if label == -1:
            continue

        buckets[int(label)].append(vector)

    centroids = {}

    for cluster_id, cluster_vectors in buckets.items():

        centroid = np.mean(
            cluster_vectors,
            axis=0,
        )

        centroid = normalize(
            centroid.reshape(1, -1)
        )[0]

        centroids[cluster_id] = centroid

    return centroids


def find_nearest_cluster(
    vector: np.ndarray,
    centroids: dict[int, np.ndarray],
):
    """
    Returns:
        cluster_id,
        similarity_score
    """

    vector = normalize(
        vector.reshape(1, -1)
    )[0]

    best_cluster = None
    best_score = -1.0

    for cluster_id, centroid in centroids.items():

        score = cosine_similarity(
            vector.reshape(1, -1),
            centroid.reshape(1, -1),
        )[0][0]

        if score > best_score:
            best_score = score
            best_cluster = cluster_id

    return best_cluster, float(best_score)


def assign_outliers(
    vectors: np.ndarray,
    labels: np.ndarray,
):
    """
    For every outlier, find nearest cluster centroid.

    Returns:
        nearest_cluster_ids
        nearest_cluster_scores
    """

    centroids = build_cluster_centroids(
        vectors,
        labels,
    )

    nearest_cluster_ids = []
    nearest_cluster_scores = []

    for vector, label in zip(vectors, labels):

        if label == -1:

            cluster_id, score = find_nearest_cluster(
                vector,
                centroids,
            )

            nearest_cluster_ids.append(cluster_id)
            nearest_cluster_scores.append(score)

        else:

            nearest_cluster_ids.append(int(label))
            nearest_cluster_scores.append(1.0)

    return (
        nearest_cluster_ids,
        nearest_cluster_scores,
    )


async def save_results(
    slugs,
    labels,
    probabilities,
    coords,
    nearest_cluster_ids,
    nearest_cluster_scores,
):

    conn = await asyncpg.connect(DATABASE_URL)

    try:

        unique_clusters = sorted(
            int(label)
            for label in set(labels)
            if label != -1
        )

        for cluster_id in unique_clusters:

            await conn.execute(
                """
                INSERT INTO startup_clusters (
                    cluster_id,
                    company_count
                )
                VALUES ($1, 0)
                ON CONFLICT (cluster_id)
                DO NOTHING
                """,
                cluster_id,
            )

        for (
            slug,
            label,
            prob,
            coord,
            nearest_cluster_id,
            nearest_cluster_score,
        ) in zip(
            slugs,
            labels,
            probabilities,
            coords,
            nearest_cluster_ids,
            nearest_cluster_scores,
        ):

            await conn.execute(
                """
                UPDATE yc_companies
                SET
                    cluster_id = $1,
                    cluster_confidence = $2,
                    is_outlier = $3,
                    nearest_cluster_id = $4,
                    nearest_cluster_score = $5,
                    umap_x = $6,
                    umap_y = $7
                WHERE slug = $8
                """,
                None if label == -1 else int(label),
                float(prob),
                bool(label == -1),
                int(nearest_cluster_id)
                if nearest_cluster_id is not None
                else None,
                float(nearest_cluster_score)
                if nearest_cluster_score is not None
                else None,
                float(coord[0]),
                float(coord[1]),
                slug,
            )

    finally:
        await conn.close()


async def main():

    print("Loading vectors from Qdrant...")

    slugs, vectors = load_vectors()

    print(f"Loaded {len(vectors)} vectors")
    print(vectors.shape)
    print(vectors.dtype)

    print("Building UMAP coordinates...")

    coords = build_umap(vectors)

    print("Running HDBSCAN clustering...")

    labels, probabilities = run_hdbscan(coords)

    clusters = len(set(labels)) - (
        1 if -1 in labels else 0
    )

    print(f"Clusters discovered: {clusters}")

    print("Unique labels:", set(labels))
    print("Noise points:", np.sum(labels == -1))
    print("Total points:", len(labels))

    print("Assigning outliers...")

    (
        nearest_cluster_ids,
        nearest_cluster_scores,
    ) = assign_outliers(
        vectors,
        labels,
    )

    print(
        f"Assigned {np.sum(labels == -1)} outliers"
    )

    print("Saving results...")

    await save_results(
        slugs,
        labels,
        probabilities,
        coords,
        nearest_cluster_ids,
        nearest_cluster_scores,
    )

    print("Done")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())