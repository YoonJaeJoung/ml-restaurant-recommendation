"""
similarity.py
Cosine similarity computation and restaurant retrieval.
"""

import os
import tempfile
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"

def load_model():
    """Load the sentence embedding model."""
    model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
    return model

def embed_query(query: str, model: SentenceTransformer) -> np.ndarray:
    """
    Embed a user's search query into a vector.
    Note: queries use 'search_query' prefix (asymmetric search).
    """
    prefixed = f"search_query: {query}"
    embedding = model.encode([prefixed], convert_to_numpy=True)
    return embedding

def load_embeddings(embeddings_path: str) -> np.ndarray:
    """Load precomputed review embeddings from a .npy file using memory mapping."""
    return np.load(embeddings_path, mmap_mode='r')

def get_top_k_reviews(
    query_embedding: np.ndarray,
    review_embeddings: np.ndarray,
    reviews_df: pd.DataFrame,
    k: int = 50,
    chunk_size: int = 50000
) -> pd.DataFrame:
    """
    Find the top-k most similar reviews to a query embedding.
    Processes in chunks and stores scores on disk to avoid RAM overflow.
    """
    n_reviews = review_embeddings.shape[0]
    fd, temp_path = tempfile.mkstemp(suffix='.dat')
    os.close(fd)

    try:
        scores_memmap = np.memmap(temp_path, dtype='float32', mode='w+', shape=(n_reviews,))

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
    top_n: int = 10
) -> pd.DataFrame:
    """
    Aggregate review-level scores up to restaurant level.
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

def find_best_cluster(
    query_embedding: np.ndarray,
    centroids: np.ndarray,
    top_n_clusters: int = 3
) -> list:
    """
    Find the most relevant clusters for a query by comparing to centroids.
    Returns indices of top_n_clusters most similar clusters.
    """
    scores = cosine_similarity(query_embedding, centroids)[0]
    top_cluster_indices = np.argsort(scores)[::-1][:top_n_clusters]
    return top_cluster_indices.tolist()

def search_within_clusters(
    query: str,
    model: SentenceTransformer,
    review_embeddings: np.ndarray,
    reviews_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    centroids: np.ndarray,
    restaurant_clusters: pd.DataFrame,
    top_n_clusters: int = 3,
    k: int = 50,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Fast cluster-aware search. First finds the most relevant clusters,
    then runs similarity search only within those clusters' restaurants.
    """
    query_embedding = embed_query(query, model)

    # Step 1: find best clusters
    best_clusters = find_best_cluster(query_embedding, centroids, top_n_clusters)
    print(f"Searching clusters: {best_clusters}")

    # Step 2: get gmap_ids in those clusters
    mask = restaurant_clusters["cluster"].isin(best_clusters)
    relevant_gmap_ids = set(restaurant_clusters[mask]["gmap_id"])

    # Step 3: filter reviews to only those restaurants
    relevant_mask = reviews_df["gmap_id"].isin(relevant_gmap_ids)
    relevant_reviews = reviews_df[relevant_mask].copy()
    relevant_indices = np.where(relevant_mask)[0]
    relevant_embeddings = review_embeddings[relevant_indices]

    print(f"Searching {len(relevant_reviews)} reviews across {len(relevant_gmap_ids)} restaurants")

    # Step 4: cosine similarity on the subset
    scores = cosine_similarity(query_embedding, relevant_embeddings)[0]
    top_k = min(k, len(scores))
    top_indices = np.argsort(scores)[::-1][:top_k]

    top_reviews = relevant_reviews.iloc[top_indices].copy()
    top_reviews["similarity_score"] = scores[top_indices]

    results = aggregate_to_restaurants(top_reviews, meta_df, top_n=top_n)
    return results

def search(
    query: str,
    model: SentenceTransformer,
    review_embeddings: np.ndarray,
    reviews_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    k: int = 50,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Full search across all reviews using chunked processing to avoid RAM overflow.
    """
    query_embedding = embed_query(query, model)
    top_reviews = get_top_k_reviews(query_embedding, review_embeddings, reviews_df, k=k)
    results = aggregate_to_restaurants(top_reviews, meta_df, top_n=top_n)
    return results

import joblib

def load_pca_model(pca_path: str):
    """Load the fitted PCA model for query projection."""
    return joblib.load(pca_path)

def embed_query_pca(query: str, model: SentenceTransformer, pca) -> np.ndarray:
    """Embed a query and project it into PCA-reduced space."""
    query_embedding = embed_query(query, model)
    return pca.transform(query_embedding).astype('float32')

def search_pca(
    query: str,
    model: SentenceTransformer,
    pca,
    review_embeddings_pca: np.ndarray,
    reviews_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    k: int = 50,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Fast search using PCA-reduced embeddings (128-dim instead of 768-dim).
    99x speedup over full embedding search.
    """
    query_embedding = embed_query_pca(query, model, pca)
    top_reviews = get_top_k_reviews(query_embedding, review_embeddings_pca, reviews_df, k=k)
    results = aggregate_to_restaurants(top_reviews, meta_df, top_n=top_n)
    return results

def search_pca_within_clusters(
    query: str,
    model: SentenceTransformer,
    pca,
    review_embeddings_pca: np.ndarray,
    reviews_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    centroids: np.ndarray,
    restaurant_clusters: pd.DataFrame,
    top_n_clusters: int = 3,
    k: int = 50,
    top_n: int = 10
) -> pd.DataFrame:
    """
    Best of both worlds: cluster filtering + PCA-reduced search.
    First narrows to top_n_clusters, then searches in 128-dim PCA space.
    """
    query_embedding = embed_query(query, model)
    
    # Stage 1: find best clusters using full 768-dim query
    best_clusters = find_best_cluster(query_embedding, centroids, top_n_clusters)
    print(f"Searching clusters: {best_clusters}")
    
    # Stage 2: filter reviews to those clusters
    mask = restaurant_clusters["cluster"].isin(best_clusters)
    relevant_gmap_ids = set(restaurant_clusters[mask]["gmap_id"])
    relevant_mask = reviews_df["gmap_id"].isin(relevant_gmap_ids)
    relevant_reviews = reviews_df[relevant_mask].copy()
    relevant_indices = np.where(relevant_mask)[0]
    relevant_embeddings_pca = review_embeddings_pca[relevant_indices]
    
    print(f"Searching {len(relevant_reviews)} reviews across {len(relevant_gmap_ids)} restaurants")
    
    # Stage 3: project query to PCA space and search
    query_pca = pca.transform(query_embedding).astype('float32')
    scores = cosine_similarity(query_pca, relevant_embeddings_pca)[0]
    top_k = min(k, len(scores))
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    top_reviews = relevant_reviews.iloc[top_indices].copy()
    top_reviews["similarity_score"] = scores[top_indices]
    
    results = aggregate_to_restaurants(top_reviews, meta_df, top_n=top_n)
    return results
    
"""
To test search_pca_within_clusters:

python -c "
import pandas as pd
import numpy as np
from src.7_similarity import load_model, load_pca_model, search_pca_within_clusters

reviews = pd.read_parquet('data/processed/review-NYC-restaurant-filtered.parquet')
meta = pd.read_parquet('data/processed/meta-NYC-restaurant.parquet')
embeddings_pca = np.load('data/processed/review_embeddings_pca.npy', mmap_mode='r')
pca = load_pca_model('data/processed/pca_model.pkl')
centroids = np.load('results/clustering/cluster_centroids.npy')
clusters = pd.read_csv('results/clustering/restaurant_clusters.csv')

model = load_model()
results = search_pca_within_clusters('cozy italian restaurant for a date night', model, pca, embeddings_pca, reviews, meta, centroids, clusters)
print(results)
"
"""
