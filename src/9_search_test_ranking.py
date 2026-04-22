"""
9_search_test_ranking.py  —  CLI end-to-end search + ranking test.

Pipeline:
    user query
      → similarity.search_pca_within_clusters (cluster-aware semantic retrieval)
      → ranking.rank_candidates (α·rating + β·aspect-weighted + γ·log-reviews)
      → print top-N with all score components

Requires the aspect columns that src/8_ranking.py writes into
data/processed/meta-NYC-restaurant.parquet.

Run from project root:
    python src/9_search_test_ranking.py
"""
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.absa     import get_aspect_prefs, ASPECT_COLS
from src.similarity import (
    load_model, load_pca_model, load_embeddings_raw,
    search_pca_within_clusters, valid_nyc_gmap_ids,
)
from src.ranking  import rank_candidates, DEFAULT_ALPHA, DEFAULT_BETA, DEFAULT_GAMMA

# ── Paths ─────────────────────────────────────────────────────────────────────
REVIEW_PATH         = "data/processed/review-NYC-restaurant-filtered.parquet"
META_PATH           = "data/processed/meta-NYC-restaurant.parquet"
PCA_EMBEDDINGS_PATH = "results/pca/review_embeddings_pca.npy"
PCA_MODEL_PATH      = "results/pca/pca_model.pkl"
CENTROIDS_PATH      = "results/clustering/cluster_centroids.npy"
CLUSTERS_PATH       = "results/clustering/restaurant_clusters.csv"

PCA_DIM = 128


def main() -> None:
    print("\n" + "=" * 70)
    print(" NYC RESTAURANT SEARCH + ABSA-WEIGHTED RANKING  (CLI)")
    print("=" * 70)

    # ── Sanity check ──
    for p in (REVIEW_PATH, META_PATH, PCA_EMBEDDINGS_PATH, PCA_MODEL_PATH,
              CENTROIDS_PATH, CLUSTERS_PATH):
        if not os.path.exists(p):
            print(f"Missing required file: {p}")
            return

    print("Loading model, PCA, embeddings...")
    t0 = time.time()
    model           = load_model()
    pca             = load_pca_model(PCA_MODEL_PATH)
    embeddings_pca  = load_embeddings_raw(PCA_EMBEDDINGS_PATH, PCA_DIM)

    print("Loading review ids, meta (with aspect cols), centroids, clusters...")
    reviews_df  = pd.read_parquet(REVIEW_PATH, columns=['gmap_id'])
    meta_df     = pd.read_parquet(META_PATH)
    centroids   = np.load(CENTROIDS_PATH)
    clusters_df = pd.read_csv(CLUSTERS_PATH)

    # Verify aspect cols exist (written by src/8_ranking.py)
    missing = [c for c in ASPECT_COLS if c not in meta_df.columns]
    if missing:
        print(f"Missing aspect columns in {META_PATH}: {missing}")
        print("Run `python src/8_ranking.py` first.")
        return

    # Global stats for stable cross-query ranking
    num_reviews_global = reviews_df.groupby("gmap_id").size()
    log_reviews_max = float(np.log1p(num_reviews_global.max()))

    # Precompute NYC ZIP-valid gmap_id set. The stale meta parquet admits a few
    # hundred upstate NY restaurants (Clinton 13323, Schuylerville 12871, etc.)
    # whose neighborhood names match NYC ones. Filter them out of every query.
    nyc_ids = valid_nyc_gmap_ids(meta_df)
    print(f"NYC ZIP filter: {len(nyc_ids):,} of {len(meta_df):,} meta rows pass.")

    # For ranking we need num_of_reviews; meta has it already
    print(f"Ready ({time.time() - t0:.1f}s).")
    print("-" * 70)
    print("Type a query (e.g. 'cheap ramen quick service').  'exit' to quit.")

    while True:
        try:
            query = input("\nquery> ").strip()
        except EOFError:
            break
        if not query or query.lower() in {"exit", "quit"}:
            break

        # Detect aspect preferences from query text
        prefs = get_aspect_prefs(query)

        # Semantic retrieval (cluster-aware, PCA space)
        t0 = time.time()
        candidates, best_clusters = search_pca_within_clusters(
            query, model, pca, embeddings_pca,
            reviews_df, meta_df, centroids, clusters_df,
            top_n_clusters=5, k=500, top_n=100,
        )
        ret_elapsed = time.time() - t0
        if len(candidates) == 0:
            print("No candidates.")
            continue

        # Defensive NYC ZIP filter on candidates (search_pca_within_clusters
        # already filters, but keeping it explicit here makes the guarantee
        # visible at the script level).
        candidates = candidates[candidates["gmap_id"].isin(nyc_ids)].reset_index(drop=True)
        if len(candidates) == 0:
            print("No NYC candidates after ZIP filter.")
            continue

        # Rank
        t0 = time.time()
        result = rank_candidates(
            candidates, meta_df, prefs,
            alpha=DEFAULT_ALPHA, beta=DEFAULT_BETA, gamma=DEFAULT_GAMMA,
            log_reviews_max=log_reviews_max,
        )
        rnk_elapsed = time.time() - t0

        # Display
        top = result.ranked.head(10)
        print(f"\nDetected aspect prefs: { {k: round(v, 2) for k, v in result.user_prefs.items()} }")
        print(f"α={result.alpha:.2f}  β={result.beta:.2f}  γ={result.gamma:.2f}")
        print(f"retrieval {ret_elapsed*1000:>6.0f} ms | rank {rnk_elapsed*1000:>5.0f} ms")
        print()
        print(f"{'#':<3}{'name':<35}{'boro':<14}{'★':>4}{'$$':>6}{'food':>7}"
              f"{'svc':>7}{'prc':>7}{'wait':>7}{'final':>7}")
        print("-" * 99)
        for i, (_, r) in enumerate(top.iterrows(), 1):
            print(f"{i:<3}"
                  f"{str(r['name'])[:33]:<35}"
                  f"{str(r['borough'])[:12]:<14}"
                  f"{r['avg_rating']:>4.1f}"
                  f"{(r['price'] if isinstance(r['price'], str) else '?'):>6}"
                  f"{r['aspect_food']:>7.2f}"
                  f"{r['aspect_service']:>7.2f}"
                  f"{r['aspect_price_blended']:>7.2f}"
                  f"{r['aspect_wait_time']:>7.2f}"
                  f"{r['final_score']:>7.3f}")


if __name__ == "__main__":
    main()
