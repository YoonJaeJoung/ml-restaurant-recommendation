"""
6d_clustering_experiments_full.py
Runs a systematic grid search for optimal clustering (K and Feature Scheme).
Generates clustering_scores.csv for use in analysis notebooks.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score

DATA_DIR = "data/processed"
RESULTS_DIR = "results/clustering"

def restore_filtered_meta():
    meta_df = pd.read_parquet(f"{DATA_DIR}/meta-NYC-restaurant.parquet")
    review_filtered_path = f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet"
    review_df = pd.read_parquet(review_filtered_path, columns=["gmap_id"])
    valid_gmap_ids = review_df["gmap_id"].unique()
    return meta_df[meta_df["gmap_id"].isin(valid_gmap_ids)].reset_index(drop=True)

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
        "good", "great", "nice", "delicious", "amazing", "excellent", "best",
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
    return np.hstack([meta_normed, tfidf_normed])

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    print("🚀 Loading data and building features...")
    meta_df = restore_filtered_meta()
    restaurant_ids = meta_df["gmap_id"].tolist()
    
    # Meta Features
    raw_meta_emb = np.load(f"{DATA_DIR}/meta_embeddings.npy").astype(np.float32)
    meta_normed = normalize(raw_meta_emb, norm="l2")
    
    # Combined Features
    combined = build_features_combined(meta_normed, restaurant_ids)
    
    # PCA to 100D for both (as per experiments)
    print("Applying PCA (100 components)...")
    pca_meta = PCA(n_components=100, random_state=42).fit_transform(meta_normed)
    pca_combined = PCA(n_components=100, random_state=42).fit_transform(combined)

    k_values = [5, 8, 10, 15, 20, 25, 30, 40, 50]
    feature_map = {"meta": pca_meta, "combined": pca_combined}
    results = []

    print("Running Grid Search (4 schemes x 9 K-values)...")
    for feat_name, X in feature_map.items():
        for algo in ["kmeans", "gmm"]:
            scheme = f"{feat_name}+{algo}"
            print(f"\n--- Scheme: {scheme} ---")
            for k in k_values:
                if algo == "kmeans":
                    model = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = model.fit_predict(X)
                else:
                    model = GaussianMixture(n_components=k, covariance_type="diag", random_state=42)
                    labels = model.fit(X).predict(X)

                # Consistent with previous experiments, use sampled silhouette for speed
                score = silhouette_score(X, labels, sample_size=3000, random_state=42)
                results.append({"scheme": scheme, "k": k, "silhouette": round(float(score), 4)})
                print(f"  k={k}: silhouette={score:.4f}")

    # Output to results/clustering/clustering_scores.csv
    out_path = f"{RESULTS_DIR}/clustering_scores.csv"
    pd.DataFrame(results).to_csv(out_path, index=False)
    print(f"\n✅ All experiments complete. Scores saved to: {out_path}")

if __name__ == "__main__":
    main()
