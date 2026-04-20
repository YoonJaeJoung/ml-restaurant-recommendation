"""
5_search_test_pca.py
Semantic search using PCA-reduced embeddings.

This script mirrors 3_search_test_embedding.py but operates in the lower-
dimensional PCA space produced by 4_pca.py.  Because the vectors are smaller
(e.g. 128-d vs 768-d), similarity computation is significantly faster and
requires less memory.

Prerequisites
  - data/processed/review_embeddings_pca.npy   (from 4_pca.py)
  - data/processed/pca_model.pkl               (from 4_pca.py)
  - data/processed/review-NYC-restaurant-filtered.parquet  (from 1_data_processing.py)
  - data/processed/meta-NYC-restaurant.parquet
"""

import os
import tempfile
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# --------------- Configuration ---------------
MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
PCA_MODEL_PATH = "data/processed/pca_model.pkl"
PCA_EMBEDDINGS_PATH = "data/processed/review_embeddings_pca.npy"
REVIEWS_PATH = "data/processed/review-NYC-restaurant-filtered.parquet"
META_PATH = "data/processed/meta-NYC-restaurant.parquet"
# ------------------------------------------------


def load_model():
    """Load the sentence embedding model."""
    model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    return model


def embed_query_pca(query: str, model: SentenceTransformer, pca) -> np.ndarray:
    """
    Embed a user query and project it into the PCA-reduced space.
    Returns shape (1, n_components).
    """
    prefixed = f"search_query: {query}"
    full_embedding = model.encode([prefixed], convert_to_numpy=True)  # (1, 768)
    reduced = pca.transform(full_embedding).astype(np.float32)        # (1, n_components)
    return reduced


def get_top_k_reviews(
    query_embedding: np.ndarray,
    review_embeddings: np.ndarray,
    reviews_df: pd.DataFrame,
    k: int = 50,
    chunk_size: int = 100_000,
) -> pd.DataFrame:
    """
    Find the top-k most similar reviews to a query embedding in PCA space.
    Uses disk-backed temporary storage to cap RAM usage.
    """
    n_reviews = review_embeddings.shape[0]

    fd, temp_path = tempfile.mkstemp(suffix=".dat")
    os.close(fd)

    try:
        scores_memmap = np.memmap(temp_path, dtype="float32", mode="w+", shape=(n_reviews,))

        for i in range(0, n_reviews, chunk_size):
            end_idx = min(i + chunk_size, n_reviews)
            chunk = review_embeddings[i:end_idx]
            scores_memmap[i:end_idx] = cosine_similarity(query_embedding, chunk)[0]

        scores_memmap.flush()

        k_actual = min(k, n_reviews)
        if k_actual < n_reviews:
            top_indices = np.argpartition(scores_memmap, -k_actual)[-k_actual:]
            top_indices = top_indices[np.argsort(scores_memmap[top_indices])[::-1]]
        else:
            top_indices = np.argsort(scores_memmap)[::-1]

        top_reviews = reviews_df.iloc[top_indices].copy()
        top_reviews["similarity_score"] = scores_memmap[top_indices]

    finally:
        del scores_memmap
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return top_reviews


def aggregate_to_restaurants(
    top_reviews: pd.DataFrame,
    meta_df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Aggregate review-level scores to restaurant level.
    Returns top_n restaurants ranked by average similarity score.
    """
    restaurant_scores = (
        top_reviews.groupby("gmap_id")["similarity_score"]
        .mean()
        .reset_index()
        .rename(columns={"similarity_score": "avg_similarity"})
    )
    results = restaurant_scores.merge(meta_df, on="gmap_id", how="left")
    results = results.sort_values("avg_similarity", ascending=False).head(top_n)
    return results[["name", "avg_similarity", "avg_rating", "borough", "latitude", "longitude", "gmap_id"]]


def search(
    query: str,
    model: SentenceTransformer,
    pca,
    review_embeddings: np.ndarray,
    reviews_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    k: int = 50,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    Main search function using PCA-reduced embeddings.
    Takes a natural language query and returns top_n recommended restaurants.
    """
    query_embedding = embed_query_pca(query, model, pca)
    top_reviews = get_top_k_reviews(query_embedding, review_embeddings, reviews_df, k=k)
    results = aggregate_to_restaurants(top_reviews, meta_df, top_n=top_n)
    return results


if __name__ == "__main__":
    print("Loading data ...")
    reviews = pd.read_parquet(REVIEWS_PATH)
    meta = pd.read_parquet(META_PATH)
    review_embeddings = np.load(PCA_EMBEDDINGS_PATH, mmap_mode="r")

    print("Loading PCA model ...")
    pca = joblib.load(PCA_MODEL_PATH)
    print(f"  PCA components: {pca.n_components_}, explained variance: {pca.explained_variance_ratio_.sum()*100:.2f}%")

    print("Loading embedding model ...")
    model = load_model()

    print("Searching (PCA space) ...")
    results = search("cozy italian restaurant for a date night", model, pca, review_embeddings, reviews, meta)
    print(results)
