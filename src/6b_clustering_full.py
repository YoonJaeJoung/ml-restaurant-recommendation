"""
6b_clustering_full.py
Production clustering script (Full-Dimensional Version for external GPU).

Pipeline:
1. Loads 768D meta embeddings and 500D TF-IDF review features
2. Skips PCA reduction to preserve all semantic nuance
3. Performs K-Means clustering (K=50) using a from-scratch implementation
   (k-means++ init + Lloyd iterations + n_init restarts), algorithmically
   equivalent to sklearn.cluster.KMeans with default settings.
4. Computes true 768D centroids for similarity search compatibility
5. Outputs final artifacts to results/clustering/
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

DATA_DIR = "data/processed"
RESULTS_DIR = "results/clustering"
K_CLUSTERS = 50


# ─────────────────────────────────────────────────────────────────────────────
# K-Means from scratch
# ─────────────────────────────────────────────────────────────────────────────
# Mirrors sklearn.cluster.KMeans with default settings:
#   init="k-means++", algorithm="lloyd", n_init=10, max_iter=300, tol=1e-4
# Quality (inertia, silhouette, geometric structure) is comparable to sklearn,
# but cluster ids are arbitrary up to permutation — bit-identical labels are
# not expected because of (a) RNG-call ordering inside k-means++ and (b)
# matmul/sum reduction-order differences vs. sklearn's Cython kernels.

def _squared_euclidean(X, C, x_sq=None, c_sq=None):
    """Pairwise squared distances |x_i − c_j|² as |x|² + |c|² − 2 x·c.
    Returns shape (n, k). Tiny negatives from roundoff are clipped to 0."""
    if x_sq is None:
        x_sq = np.einsum("ij,ij->i", X, X)
    if c_sq is None:
        c_sq = np.einsum("ij,ij->i", C, C)
    d2 = x_sq[:, None] + c_sq[None, :] - 2.0 * X @ C.T
    np.maximum(d2, 0, out=d2)
    return d2


def _kmeans_plusplus(X, k, rng, x_sq):
    """k-means++ seeding. First center is uniform random; each subsequent
    center is chosen from `n_trials = 2 + ⌊log k⌋` candidates sampled with
    probability proportional to D² (squared distance to nearest existing
    center), keeping the candidate that minimises the resulting potential."""
    n, d = X.shape
    n_trials = 2 + int(np.log(k))
    centers = np.empty((k, d), dtype=X.dtype)

    first = rng.randint(n)
    centers[0] = X[first]
    closest_sq = _squared_euclidean(
        X, centers[:1], x_sq=x_sq, c_sq=x_sq[first:first + 1]
    ).ravel()
    current_pot = float(closest_sq.sum())

    for c in range(1, k):
        # Sample n_trials candidate point indices with prob ∝ closest_sq
        rand_vals = rng.random_sample(n_trials) * current_pot
        cand_ids = np.searchsorted(closest_sq.cumsum(), rand_vals)
        np.clip(cand_ids, 0, n - 1, out=cand_ids)

        # For each candidate, compute the new potential if it were chosen
        cand_d2 = _squared_euclidean(
            X, X[cand_ids], x_sq=x_sq, c_sq=x_sq[cand_ids]
        )
        np.minimum(cand_d2, closest_sq[:, None], out=cand_d2)
        cand_pots = cand_d2.sum(axis=0)

        best = int(np.argmin(cand_pots))
        centers[c] = X[cand_ids[best]]
        closest_sq = cand_d2[:, best]
        current_pot = float(cand_pots[best])

    return centers


def _lloyd(X, centers, max_iter, tol_scaled, x_sq):
    """Lloyd iteration: assign → recompute centroid → repeat until the
    sum-of-squared centroid shift falls below `tol_scaled` or `max_iter`
    is reached. Empty clusters are reseeded from the points currently
    farthest from their assigned centroid (matches sklearn's behaviour)."""
    n = X.shape[0]
    k = centers.shape[0]
    centers = centers.copy()

    for it in range(max_iter):
        c_sq = np.einsum("ij,ij->i", centers, centers)
        d2 = _squared_euclidean(X, centers, x_sq=x_sq, c_sq=c_sq)
        labels = d2.argmin(axis=1).astype(np.int32)

        new_centers = np.zeros_like(centers)
        counts = np.bincount(labels, minlength=k)
        np.add.at(new_centers, labels, X)
        nonempty = counts > 0
        new_centers[nonempty] /= counts[nonempty, None]

        if not nonempty.all():
            far_order = np.argsort(d2[np.arange(n), labels])[::-1]
            for slot, j in enumerate(np.where(~nonempty)[0]):
                new_centers[j] = X[far_order[slot]]

        shift_sq = float(((new_centers - centers) ** 2).sum())
        centers = new_centers
        if shift_sq <= tol_scaled:
            break

    # Final reassignment + inertia (sum in float64 for numerical stability)
    c_sq = np.einsum("ij,ij->i", centers, centers)
    d2 = _squared_euclidean(X, centers, x_sq=x_sq, c_sq=c_sq)
    labels = d2.argmin(axis=1).astype(np.int32)
    inertia = float(d2[np.arange(n), labels].astype(np.float64).sum())
    return labels, centers, inertia, it + 1


class KMeansFromScratch:
    """K-Means with k-means++ init and `n_init` random restarts.
    Algorithmically equivalent to sklearn.cluster.KMeans default settings.

    After fit, exposes `labels_`, `cluster_centers_`, `inertia_`, `n_iter_`."""

    def __init__(self, n_clusters, n_init=10, max_iter=300, tol=1e-4, random_state=None):
        self.n_clusters = n_clusters
        self.n_init = n_init
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state

    def fit_predict(self, X):
        X = np.ascontiguousarray(X)
        x_sq = np.einsum("ij,ij->i", X, X)

        # sklearn scales tol by mean per-feature variance so it stays
        # meaningful regardless of the data's absolute magnitude.
        tol_scaled = float(self.tol * np.var(X, axis=0).mean())

        # One master RNG → derive a deterministic seed per restart.
        master_rng = np.random.RandomState(self.random_state)
        seeds = master_rng.randint(np.iinfo(np.int32).max, size=self.n_init)

        best_inertia = np.inf
        best_labels = best_centers = None
        best_n_iter = 0

        for run, seed in enumerate(seeds, 1):
            sub_rng = np.random.RandomState(seed)
            init_centers = _kmeans_plusplus(X, self.n_clusters, sub_rng, x_sq)
            labels, centers, inertia, n_iter = _lloyd(
                X, init_centers, self.max_iter, tol_scaled, x_sq
            )
            print(f"  init {run:>2}/{self.n_init}: "
                  f"inertia={inertia:,.2f}, iter={n_iter}")
            if inertia < best_inertia:
                best_inertia = inertia
                best_labels = labels
                best_centers = centers
                best_n_iter = n_iter

        self.labels_ = best_labels
        self.cluster_centers_ = best_centers
        self.inertia_ = best_inertia
        self.n_iter_ = best_n_iter
        return self.labels_

def restore_filtered_meta():
    meta_df = pd.read_parquet(f"{DATA_DIR}/meta-NYC-restaurant.parquet")
    review_filtered_path = f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet"
    
    # Strictly align with the restaurants that actually have embeddings
    review_df = pd.read_parquet(review_filtered_path, columns=["gmap_id"])
    valid_gmap_ids = review_df["gmap_id"].unique()
    
    # Filter meta to only those in the final review set
    meta_df = meta_df[meta_df["gmap_id"].isin(valid_gmap_ids)].reset_index(drop=True)
    
    # Ensure the order matches what was used during embedding (alignment in 2_embedding.py)
    # 2_embedding.py does: meta_df = meta_df[meta_df["gmap_id"].isin(valid_gmap_ids)].reset_index(drop=True)
    # This matches.
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
    
    # 3. K-Means (from-scratch, direct on full dimensions)
    print(f"Running KMeans-from-scratch on full {combined.shape[1]} dimensions (K={K_CLUSTERS})...")
    print(f"  init=k-means++, n_init=10, max_iter=300, tol=1e-4 (variance-scaled)")
    model = KMeansFromScratch(n_clusters=K_CLUSTERS, n_init=10, random_state=42)
    labels = model.fit_predict(combined)
    print(f"  Best inertia across 10 restarts: {model.inertia_:,.2f} (converged in {model.n_iter_} iters)")
    
    # 4. Generate Artifacts
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
