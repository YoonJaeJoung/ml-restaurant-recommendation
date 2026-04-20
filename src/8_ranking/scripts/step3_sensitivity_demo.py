"""
step3_sensitivity_demo.py  —  Step 3: compare α/β/γ weight sets across test queries

Run from project root:
    python src/8_ranking/scripts/step3_sensitivity_demo.py

Output:
    results/sensitivity_latest.csv        (full results with weight_set column)
    results/sensitivity_latest_blind.csv  (for human scoring — weight_set hidden)

Scoring: fill in relevance_score (0/1/2) in the blind CSV, then report back
to compute per-weight-set average.
  2 = relevant to query AND matches aspect preference
  1 = relevant to query but doesn't match aspect preference
  0 = irrelevant
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import numpy as np
import pandas as pd
from src.7_similarity import load_model, load_pca_model, search_pca_within_clusters
from src.8_ranking.absa import get_aspect_prefs
from src.8_ranking import rank_candidates

REVIEWS_PATH   = "data/processed/review-NYC-restaurant-filtered.parquet"
META_PATH      = "data/processed/meta-NYC-restaurant.parquet"
EMB_PCA_PATH   = "results/pca/review_embeddings_pca.npy"
PCA_MODEL_PATH = "results/pca/pca_model.pkl"
CENTROIDS_PATH = "results/clustering/cluster_centroids.npy"
CLUSTERS_PATH  = "results/clustering/restaurant_clusters.csv"
SCORES_PATH    = "data/processed/aspect_scores.parquet"
OUT_PATH       = "results/sensitivity_latest.csv"
BLIND_PATH     = "results/sensitivity_latest_blind.csv"

WEIGHT_SETS = {
    "A: α=0.5 β=0.4 γ=0.1 (rating-driven)": (0.5, 0.4, 0.1),
    "B: α=0.4 β=0.5 γ=0.1 (aspect-driven)": (0.4, 0.5, 0.1),
    "C: α=0.3 β=0.5 γ=0.2 (balanced)":   (0.3, 0.5, 0.2),
}

TEST_QUERIES = [
    "cheap ramen no long wait",
    "best sushi with attentive service",
    "quick affordable chinese lunch",
    "great burger not overpriced",
    "fast breakfast good coffee",
    "good value tacos fast service",
    "best pizza in brooklyn not expensive",
]

print("Loading model and data...")
model          = load_model()
pca            = load_pca_model(PCA_MODEL_PATH)
embeddings_pca = np.load(EMB_PCA_PATH, mmap_mode='r')
centroids      = np.load(CENTROIDS_PATH)
reviews_df     = pd.read_parquet(REVIEWS_PATH)
meta_df        = pd.read_parquet(META_PATH)
clusters_df    = pd.read_csv(CLUSTERS_PATH)
aspect_scores  = pd.read_parquet(SCORES_PATH)

num_reviews = reviews_df.groupby("gmap_id").size().rename("num_reviews").reset_index()
records = []

for query in TEST_QUERIES:
    print(f"\n{'='*65}")
    print(f"Query: \"{query}\"")
    user_pref = get_aspect_prefs(query)
    print(f"Detected prefs: { {k: round(v,2) for k,v in user_pref.items()} }")

    candidates = search_pca_within_clusters(
        query, model, pca, embeddings_pca,
        reviews_df, meta_df, centroids, clusters_df,
        top_n=100, top_n_clusters=5, k=500
    )
    candidates = candidates.merge(num_reviews, on="gmap_id", how="left").fillna({"num_reviews": 0})

    for label, (alpha, beta, gamma) in WEIGHT_SETS.items():
        ranked = rank_candidates(candidates, aspect_scores, user_pref, alpha, beta, gamma)
        top5   = ranked.head(5)[["name", "borough", "avg_rating", "final_score",
                                  "food", "service", "price", "wait_time"]]

        print(f"\n  [{label}]")
        print(f"  {'#':<3} {'Restaurant':<35} {'Borough':<12} {'★':>4}  food  svc   prc   wt")
        print(f"  {'-'*80}")
        for rank, (_, row) in enumerate(top5.iterrows(), 1):
            print(f"  {rank:<3} {str(row['name']):<35} {str(row['borough']):<12} "
                  f"{row['avg_rating']:>4.1f}  "
                  f"{row['food']:>4.2f} {row['service']:>4.2f} "
                  f"{row['price']:>4.2f} {row['wait_time']:>4.2f}")

            records.append({
                "query":          query,
                "weight_set":     label,
                "rank":           rank,
                "name":           row["name"],
                "borough":        row["borough"],
                "avg_rating":     row["avg_rating"],
                "final_score":    round(row["final_score"], 4),
                "food":           round(row["food"], 3),
                "service":        round(row["service"], 3),
                "price":          round(row["price"], 3),
                "wait_time":      round(row["wait_time"], 3),
                "relevance_score": "",
            })

os.makedirs("results", exist_ok=True)
df = pd.DataFrame(records)
df.to_csv(OUT_PATH, index=False)
print(f"\n\nFull results saved → {OUT_PATH}")

# Blind CSV: hide weight_set for unbiased scoring
blind = df[["query", "rank", "name", "borough", "avg_rating", "relevance_score"]].copy()
blind.insert(0, "row_id", range(len(blind)))
blind.to_csv(BLIND_PATH, index=False)
print(f"Blind CSV saved → {BLIND_PATH}")
print("Fill in relevance_score (0/1/2), then report back to compute per-weight-set averages.")
