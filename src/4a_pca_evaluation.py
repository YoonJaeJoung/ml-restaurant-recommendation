"""
4a_pca_evaluation.py
Evaluate PCA dimensionality reduction across multiple component counts.

For each candidate n_components value this script:
  1. Fits PCA on the review embeddings.
  2. Measures explained variance retained.
  3. Transforms review embeddings and runs a set of benchmark queries.
  4. Compares search results to the full 768-d baseline (ranking overlap).
  5. Measures per-query search latency.
  6. Estimates memory footprint of the reduced embedding matrix.
  7. Saves a summary table and tradeoff plots to results/.

The "best" component count is chosen using a composite score:
    score = α · recall@k  +  (1-α) · compression_ratio
where α controls how much weight goes to accuracy vs. size reduction.

Usage:
    python src/4a_pca_evaluation.py
"""

import os
import time
import json
import tempfile
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")          # headless backend – safe for scripts
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import torch
import importlib

# Attempt to load cuML for GPU-accelerated PCA
CUML_AVAILABLE = False
try:
    import cuml
    CUML_AVAILABLE = True
except ImportError:
    pass

class TorchPCA:
    """Fallback GPU PCA implementation using PyTorch linalg.svd."""
    def __init__(self, n_components, random_state=42):
        self.n_components = n_components
        self.components_ = None
        self.explained_variance_ratio_ = None

    def fit(self, X):
        # Move to GPU in chunks if X is numpy memmap
        n, d = X.shape
        X_torch = torch.from_numpy(X).to("cuda", non_blocking=True)
        # Center the data
        self.mean_ = X_torch.mean(dim=0)
        X_centered = X_torch - self.mean_
        
        # SVD on the GPU
        U, S, V = torch.linalg.svd(X_centered, full_matrices=False)
        self.components_ = V[:self.n_components].cpu().numpy()
        
        # Calculate explained variance
        variances = (S**2) / (n - 1)
        total_var = variances.sum()
        self.explained_variance_ratio_ = (variances[:self.n_components] / total_var).cpu().numpy()
        return self

    def transform(self, X):
        n, d = X.shape
        X_torch = torch.from_numpy(X).to("cuda", non_blocking=True)
        X_centered = X_torch - self.mean_
        V = torch.from_numpy(self.components_).to("cuda", non_blocking=True).T
        return (X_centered @ V).cpu().numpy()

def get_pca_model(n_components):
    if CUML_AVAILABLE:
        print(f"  [GPU] Using cuML.PCA(n_components={n_components})")
        return cuml.PCA(n_components=n_components)
    else:
        print(f"  [GPU] cuML not found. Using TorchPCA fallback.")
        return TorchPCA(n_components=n_components)

# ─────────────────── Configuration ───────────────────
INPUT_DIR       = "./data/processed"
OUTPUT_DIR      = "./results/pca/evaluation"
MODEL_NAME      = "nomic-ai/nomic-embed-text-v1.5"
CHUNK_SIZE      = 100_000       # rows per PCA-transform batch
SEARCH_K        = 50            # top-k reviews to retrieve
TOP_N           = 10            # top-n restaurants to show
ALPHA           = 0.6           # weight toward accuracy in composite score

# Component counts to evaluate (ascending order)
COMPONENT_CANDIDATES = [16, 32, 64, 128, 256, 384, 512]

# Benchmark queries to test (covers different restaurant-search intents)
BENCHMARK_QUERIES = [
    "cozy italian restaurant for a date night",
    "best ramen noodles in Manhattan",
    "family friendly brunch with outdoor seating",
    "cheap fast food near Times Square",
    "upscale sushi omakase experience",
]
# ─────────────────────────────────────────────────────

def load_data():
    """Load review embeddings, review df, meta df."""
    print("Loading review parquet for shape detection...")
    review_path = os.path.join(INPUT_DIR, "review-NYC-restaurant-filtered.parquet")
    reviews = pd.read_parquet(review_path)
    n_reviews = len(reviews)
    dim = 768

    print(f"Loading review embeddings (raw memmap, {n_reviews:,} rows) ...")
    emb_path = os.path.join(INPUT_DIR, "review_embeddings.npy")
    # review_embeddings.npy is headerless raw binary saved via memmap
    review_embeddings = np.memmap(emb_path, dtype='float32', mode="r", shape=(n_reviews, dim))
    print(f"  shape: {review_embeddings.shape}")

    print("Loading meta parquet ...")
    meta = pd.read_parquet(os.path.join(INPUT_DIR, "meta-NYC-restaurant.parquet"))
    print(f"  {len(meta):,} restaurants\n")
    return review_embeddings, reviews, meta


def embed_query(query: str, model: SentenceTransformer) -> np.ndarray:
    """Embed a single query → (1, 768)."""
    return model.encode([f"search_query: {query}"], convert_to_numpy=True)


def search_top_k(query_emb: np.ndarray, review_embs: np.ndarray,
                 reviews_df: pd.DataFrame, meta_df: pd.DataFrame,
                 k: int = 50, top_n: int = 10, chunk_size: int = 100_000):
    """
    Return (top_restaurant_gmap_ids, elapsed_seconds).
    Uses disk-backed temp file for scores to keep RAM low.
    """
    n = review_embs.shape[0]
    fd, temp_path = tempfile.mkstemp(suffix=".dat")
    os.close(fd)

    t0 = time.perf_counter()
    try:
        scores = np.memmap(temp_path, dtype="float32", mode="w+", shape=(n,))
        for i in range(0, n, chunk_size):
            end = min(i + chunk_size, n)
            scores[i:end] = cosine_similarity(query_emb, review_embs[i:end])[0]
        scores.flush()

        k_actual = min(k, n)
        if k_actual < n:
            top_idx = np.argpartition(scores, -k_actual)[-k_actual:]
            top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]
        else:
            top_idx = np.argsort(scores)[::-1]

        top_reviews = reviews_df.iloc[top_idx].copy()
        top_reviews["similarity_score"] = scores[top_idx]
    finally:
        del scores
        if os.path.exists(temp_path):
            os.remove(temp_path)

    elapsed = time.perf_counter() - t0

    # Aggregate to restaurant level
    rest_scores = (
        top_reviews.groupby("gmap_id")["similarity_score"]
        .mean().reset_index()
        .rename(columns={"similarity_score": "avg_sim"})
    )
    rest_scores = rest_scores.merge(meta_df[["gmap_id", "name"]], on="gmap_id", how="left")
    rest_scores = rest_scores.sort_values("avg_sim", ascending=False).head(top_n)
    gmap_ids = rest_scores["gmap_id"].tolist()
    return gmap_ids, elapsed


def recall_at_k(baseline_ids: list, candidate_ids: list) -> float:
    """Fraction of baseline items found in candidate list (order-agnostic)."""
    if not baseline_ids:
        return 0.0
    return len(set(baseline_ids) & set(candidate_ids)) / len(baseline_ids)


def rank_correlation(baseline_ids: list, candidate_ids: list) -> float:
    """
    Simple positional-overlap score:
    For each item in both lists, measure how close its rank is to the baseline rank.
    Returns 1.0 for perfect match, lower for worse.
    """
    if not baseline_ids:
        return 0.0
    common = set(baseline_ids) & set(candidate_ids)
    if not common:
        return 0.0
    baseline_rank = {gid: i for i, gid in enumerate(baseline_ids)}
    candidate_rank = {gid: i for i, gid in enumerate(candidate_ids)}
    max_displacement = len(baseline_ids) - 1
    if max_displacement == 0:
        return 1.0
    total = 0.0
    for gid in common:
        disp = abs(baseline_rank[gid] - candidate_rank[gid])
        total += 1.0 - disp / max_displacement
    return total / len(baseline_ids)


def transform_chunked(pca, embeddings, chunk_size):
    """Project embeddings through PCA in chunks."""
    n = embeddings.shape[0]
    out = np.empty((n, pca.n_components_), dtype=np.float32)
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        out[start:end] = pca.transform(embeddings[start:end]).astype(np.float32)
    return out


# ─────────────────── Main ───────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    review_embeddings, reviews, meta = load_data()
    n_reviews, original_dim = review_embeddings.shape
    original_size_mb = (n_reviews * original_dim * 4) / (1024 ** 2)

    print("Loading embedding model ...")
    model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)

    # ── Step 1: Compute baseline (full 768-d) search results ──
    print("=" * 60)
    print("BASELINE: Full 768-d search")
    print("=" * 60)
    baseline_results = {}
    baseline_times = []
    for q in BENCHMARK_QUERIES:
        q_emb = embed_query(q, model)
        gids, elapsed = search_top_k(
            q_emb, review_embeddings, reviews, meta,
            k=SEARCH_K, top_n=TOP_N, chunk_size=CHUNK_SIZE,
        )
        baseline_results[q] = gids
        baseline_times.append(elapsed)
        print(f"  [{elapsed:.2f}s] {q}")
    baseline_avg_time = np.mean(baseline_times)
    print(f"  Avg baseline query time: {baseline_avg_time:.2f}s\n")

    # ── Step 2: Evaluate each PCA component count ──
    records = []
    for n_comp in COMPONENT_CANDIDATES:
        print("=" * 60)
        print(f"PCA n_components = {n_comp}")
        print("=" * 60)

        # Fit PCA
        t_fit_start = time.perf_counter()
        pca = get_pca_model(n_comp)
        pca.fit(review_embeddings)
        t_fit = time.perf_counter() - t_fit_start
        explained_var = pca.explained_variance_ratio_.sum() * 100

        print(f"  Fit time:          {t_fit:.1f}s")
        print(f"  Explained var:     {explained_var:.2f}%")

        # Transform review embeddings
        t_transform_start = time.perf_counter()
        reduced_embeddings = transform_chunked(pca, review_embeddings, CHUNK_SIZE)
        t_transform = time.perf_counter() - t_transform_start
        print(f"  Transform time:    {t_transform:.1f}s")

        reduced_size_mb = (n_reviews * n_comp * 4) / (1024 ** 2)
        compression = reduced_size_mb / original_size_mb

        # Run benchmark queries
        query_times = []
        recalls = []
        rank_corrs = []
        for q in BENCHMARK_QUERIES:
            q_emb_full = embed_query(q, model)
            q_emb_pca = pca.transform(q_emb_full).astype(np.float32)
            gids, elapsed = search_top_k(
                q_emb_pca, reduced_embeddings, reviews, meta,
                k=SEARCH_K, top_n=TOP_N, chunk_size=CHUNK_SIZE,
            )
            r = recall_at_k(baseline_results[q], gids)
            rc = rank_correlation(baseline_results[q], gids)
            recalls.append(r)
            rank_corrs.append(rc)
            query_times.append(elapsed)
            print(f"  [{elapsed:.2f}s] recall={r:.0%}  rank_corr={rc:.2f}  {q}")

        avg_recall = np.mean(recalls)
        avg_rank_corr = np.mean(rank_corrs)
        avg_query_time = np.mean(query_times)
        speedup = baseline_avg_time / avg_query_time if avg_query_time > 0 else float("inf")

        # Composite score:  α * accuracy  +  (1-α) * (1 - compression)
        composite = ALPHA * avg_recall + (1 - ALPHA) * (1 - compression)

        records.append({
            "n_components": n_comp,
            "explained_var_pct": round(explained_var, 2),
            "avg_recall@10": round(avg_recall, 4),
            "avg_rank_corr": round(avg_rank_corr, 4),
            "avg_query_time_s": round(avg_query_time, 3),
            "speedup_vs_768d": round(speedup, 2),
            "size_mb": round(reduced_size_mb, 1),
            "compression_ratio": round(compression, 4),
            "composite_score": round(composite, 4),
            "fit_time_s": round(t_fit, 1),
            "transform_time_s": round(t_transform, 1),
        })

        print(f"  Avg recall@{TOP_N}: {avg_recall:.2%}")
        print(f"  Avg rank corr:     {avg_rank_corr:.2f}")
        print(f"  Avg query time:    {avg_query_time:.3f}s  (speedup {speedup:.2f}×)")
        print(f"  Reduced size:      {reduced_size_mb:.1f} MB  ({compression:.1%} of original)")
        print(f"  Composite score:   {composite:.4f}\n")

        # Free memory for next iteration
        del reduced_embeddings, pca

    # ── Step 3: Summarise & pick best ──
    df = pd.DataFrame(records)
    best_idx = df["composite_score"].idxmax()
    best = df.loc[best_idx]

    print("\n" + "=" * 72)
    print("EVALUATION SUMMARY")
    print("=" * 72)
    print(df.to_string(index=False))
    print(f"\n★ Best component count: {int(best['n_components'])}  "
          f"(composite={best['composite_score']:.4f}, "
          f"recall={best['avg_recall@10']:.2%}, "
          f"compression={best['compression_ratio']:.1%})")

    # Save table
    csv_path = os.path.join(OUTPUT_DIR, "pca_evaluation_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nSaved evaluation table → {csv_path}")

    # Save as JSON too for easy programmatic use
    json_path = os.path.join(OUTPUT_DIR, "pca_evaluation_results.json")
    # Convert numpy types to native python types for JSON serialization
    serialized_records = []
    for r in records:
        serialized_records.append({k: (float(v) if isinstance(v, (np.float32, np.float64)) else v) for k, v in r.items()})
    
    with open(json_path, "w") as f:
        json.dump({
            "baseline_avg_query_time_s": round(float(baseline_avg_time), 3),
            "original_dim": int(original_dim),
            "original_size_mb": round(float(original_size_mb), 1),
            "alpha": float(ALPHA),
            "best_n_components": int(best["n_components"]),
            "results": serialized_records,
        }, f, indent=2)
    print(f"Saved evaluation JSON  → {json_path}")

    # ── Step 4: Plot tradeoff charts ──
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("PCA Dimensionality Reduction — Tradeoff Analysis", fontsize=16, fontweight="bold")

    comps = df["n_components"].values

    # 4a: Explained variance
    ax = axes[0, 0]
    ax.plot(comps, df["explained_var_pct"], "o-", color="#4C72B0", linewidth=2, markersize=8)
    ax.set_xlabel("n_components")
    ax.set_ylabel("Explained Variance (%)")
    ax.set_title("Explained Variance Retained")
    ax.set_xticks(comps)
    ax.grid(True, alpha=0.3)
    for x, y in zip(comps, df["explained_var_pct"]):
        ax.annotate(f"{y:.1f}%", (x, y), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=8)

    # 4b: Recall@10 vs compression
    ax = axes[0, 1]
    ax.plot(comps, df["avg_recall@10"] * 100, "s-", color="#DD8452", linewidth=2, markersize=8, label="Recall@10")
    ax2 = ax.twinx()
    ax2.bar(comps, (1 - df["compression_ratio"]) * 100, width=15, alpha=0.25, color="#55A868", label="Size Reduction %")
    ax.set_xlabel("n_components")
    ax.set_ylabel("Recall@10 (%)", color="#DD8452")
    ax2.set_ylabel("Size Reduction (%)", color="#55A868")
    ax.set_title("Accuracy vs. Size Reduction")
    ax.set_xticks(comps)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    ax2.legend(loc="center right")

    # 4c: Query time
    ax = axes[1, 0]
    ax.bar(comps, df["avg_query_time_s"], width=15, color="#8172B3", alpha=0.8)
    ax.axhline(y=baseline_avg_time, color="red", linestyle="--", linewidth=1.5, label=f"Baseline 768-d ({baseline_avg_time:.2f}s)")
    ax.set_xlabel("n_components")
    ax.set_ylabel("Avg Query Time (s)")
    ax.set_title("Search Latency")
    ax.set_xticks(comps)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4d: Composite score
    ax = axes[1, 1]
    colors = ["#C44E52" if i != best_idx else "#4C72B0" for i in range(len(df))]
    bars = ax.bar(comps, df["composite_score"], width=15, color=colors, alpha=0.85)
    ax.set_xlabel("n_components")
    ax.set_ylabel(f"Composite Score (α={ALPHA})")
    ax.set_title("Composite Score (higher = better)")
    ax.set_xticks(comps)
    ax.grid(True, alpha=0.3)
    for bar, val in zip(bars, df["composite_score"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plot_path = os.path.join(OUTPUT_DIR, "pca_tradeoff_analysis.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"Saved tradeoff plot    → {plot_path}")
    plt.close()

    # ── Individual explained-variance-per-component curve ──
    # Fit once with max components to show the scree / elbow curve
    print("\nFitting PCA with max components for scree plot ...")
    max_comp = min(512, original_dim, n_reviews)
    pca_full = get_pca_model(max_comp)
    pca_full.fit(review_embeddings)
    cumvar = np.cumsum(pca_full.explained_variance_ratio_) * 100

    fig2, ax = plt.subplots(figsize=(10, 5))
    ax.plot(range(1, max_comp + 1), cumvar, color="#4C72B0", linewidth=2)
    # Mark each candidate
    for nc in COMPONENT_CANDIDATES:
        if nc <= max_comp:
            ax.axvline(x=nc, color="#C44E52", linestyle=":", alpha=0.5)
            ax.annotate(f"n={nc}\n{cumvar[nc-1]:.1f}%",
                        (nc, cumvar[nc-1]),
                        textcoords="offset points", xytext=(8, -15),
                        fontsize=8, color="#C44E52")
    ax.set_xlabel("Number of PCA Components")
    ax.set_ylabel("Cumulative Explained Variance (%)")
    ax.set_title("PCA Scree / Elbow Curve (Cumulative)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    scree_path = os.path.join(OUTPUT_DIR, "pca_scree_curve.png")
    plt.savefig(scree_path, dpi=150, bbox_inches="tight")
    print(f"Saved scree curve      → {scree_path}")
    plt.close()

    print("\n✅ PCA evaluation complete!")
    print(f"\n★ RECOMMENDATION: Use n_components = {int(best['n_components'])}")
    print(f"   Explained variance: {best['explained_var_pct']:.2f}%")
    print(f"   Recall@{TOP_N}: {best['avg_recall@10']:.2%}")
    print(f"   Size: {best['size_mb']:.1f} MB ({best['compression_ratio']:.1%} of {original_size_mb:.0f} MB)")
    print(f"   Speedup: {best['speedup_vs_768d']:.2f}× faster than full embeddings")


if __name__ == "__main__":
    main()
