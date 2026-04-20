"""
6a_clustering_pca.py
Production clustering script (PCA-Reduced Version).

Pipeline:
1. Loads 768D meta embeddings and 500D TF-IDF review features
2. Applies 100D PCA reduction to the combined features
3. Performs K-Means clustering (K=50)
4. Computes true 768D centroids for similarity search compatibility
5. Outputs final artifacts to results/clustering/
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

DATA_DIR = "data/processed"
RESULTS_DIR = "results/clustering"
K_CLUSTERS = 50

def restore_filtered_meta():
    meta_df = pd.read_parquet(f"{DATA_DIR}/meta-NYC-restaurant.parquet")
    review_filtered_path = f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet"
    
    # Strictly align with the restaurants that actually have embeddings
    review_df = pd.read_parquet(review_filtered_path, columns=["gmap_id"])
    valid_gmap_ids = review_df["gmap_id"].unique()
    
    # Filter meta to only those in the final review set
    meta_df = meta_df[meta_df["gmap_id"].isin(valid_gmap_ids)].reset_index(drop=True)
    return meta_df

def build_features_meta():
    # Load meta embeddings (already aligned with the filtered meta entries)
    meta_emb = np.load(f"{DATA_DIR}/meta_embeddings.npy").astype(np.float32)
    meta_normed = normalize(meta_emb, norm="l2")
    return meta_normed

def build_features_combined(meta_normed, restaurant_ids):
    review_df = pd.read_parquet(
        f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet",
        columns=["gmap_id", "text_for_embedding"],
    )
    review_df["text_for_embedding"] = review_df["text_for_embedding"].fillna("")
    agg = review_df.groupby("gmap_id")["text_for_embedding"].apply(" ".join).reset_index()
    agg.columns = ["gmap_id", "all_text"]

    id_order = pd.DataFrame({"gmap_id": restaurant_ids, "_order": range(len(restaurant_ids))})
    agg = id_order.merge(agg, on="gmap_id", how="left").sort_values("_order")
    agg["all_text"] = agg["all_text"].fillna("")

    custom_stop_words = [
        "good", "great", "nice", "delicious", "amazing", "excellent",
        "bad", "food", "place", "restaurant", "came", "got", "went",
        "time", "really", "just", "ordered", "staff", "service", "definitely",
    ]
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    stop_words = list(ENGLISH_STOP_WORDS | set(custom_stop_words))

    vectorizer = TfidfVectorizer(
        max_features=500, min_df=5, max_df=0.3,
        ngram_range=(1, 2), stop_words=stop_words,
    )
    tfidf_matrix = vectorizer.fit_transform(agg["all_text"]).toarray().astype(np.float32)
    tfidf_normed = normalize(tfidf_matrix, norm="l2")

    combined = np.hstack([meta_normed, tfidf_normed])
    return combined

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # 1. Load Data
    print("Loading data...")
    meta_df = restore_filtered_meta()
    restaurant_ids = meta_df["gmap_id"].tolist()
    
    # 2. Build Features
    print("Building features...")
    meta_normed = build_features_meta()
    combined = build_features_combined(meta_normed, restaurant_ids)
    
    # 3. PCA Reduction
    print("Applying PCA (100 components)...")
    pca = PCA(n_components=100, random_state=42)
    pca_combined = pca.fit_transform(combined)
    
    # 4. K-Means
    print(f"Running KMeans (K={K_CLUSTERS})...")
    model = KMeans(n_clusters=K_CLUSTERS, random_state=42, n_init=10)
    labels = model.fit_predict(pca_combined)
    
    # 5. Generate Artifacts
    print("Generating production artifacts...")
    
    # Artifact 1: restaurant_clusters.csv
    clusters_out = meta_df[["gmap_id", "name", "latitude", "longitude", "avg_rating", "borough"]].copy()
    clusters_out["cluster"] = labels
    clusters_out = clusters_out.dropna(subset=["latitude", "longitude"])
    csv_path = f"{RESULTS_DIR}/restaurant_clusters.csv"
    clusters_out.to_csv(csv_path, index=False)
    print(f"Saved -> {csv_path} ({len(clusters_out)} rows)")
    
    # Artifact 2: cluster_centroids.npy (computed on 768D meta space for similarity search!)
    raw_meta_emb = np.load(f"{DATA_DIR}/meta_embeddings.npy")
    centroids = np.zeros((K_CLUSTERS, raw_meta_emb.shape[1]), dtype=np.float32)
    
    for k in range(K_CLUSTERS):
        mask = (labels == k)
        if np.any(mask):
            centroids[k] = raw_meta_emb[mask].mean(axis=0)
            
    npy_path = f"{RESULTS_DIR}/cluster_centroids.npy"
    np.save(npy_path, centroids)
    print(f"Saved -> {npy_path} (shape: {centroids.shape})")

if __name__ == "__main__":
    main()
