"""
step2_validation.py  —  Step 2: validate ABSA + query detection + sensitivity analysis

Run from project root:
    python src/ranking/scripts/step2_validation.py

Prerequisites:
    data/processed/aspect_scores.parquet      (from step1_precompute.py)
    data/validation/sample_sentences_labeled.csv  (manually labeled)

Output:
    results/sensitivity_analysis.csv
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pandas as pd
import numpy as np
from src.ranking.absa import validate_absa_accuracy, validate_vader_clause_length, get_aspect_prefs
from src.ranking import validate_query_detection, sensitivity_analysis, TEST_CASES

REVIEWS_PATH       = "data/processed/review-NYC-restaurant-filtered.parquet"
LABELS_PATH        = "data/validation/sample_sentences_labeled.csv"
ASPECT_SCORES_PATH = "data/processed/aspect_scores.parquet"
CLUSTERS_PATH      = "results/clustering/restaurant_clusters.csv"

print("Loading data...")
reviews_df       = pd.read_parquet(REVIEWS_PATH)
aspect_scores_df = pd.read_parquet(ASPECT_SCORES_PATH)
labels_df        = pd.read_csv(LABELS_PATH, keep_default_na=False)
clusters_df      = pd.read_csv(CLUSTERS_PATH)

# ── A: VADER clause-length validation ─────────────────────────────────────────
print("\n" + "="*60)
print("A  VADER Clause-Length Validation (sample 500 reviews)")
print("="*60)
validate_vader_clause_length(reviews_df, sample_n=500)

# ── B: ABSA keyword precision / recall ────────────────────────────────────────
print("\n" + "="*60)
print("B  ABSA Keyword Precision / Recall (labeled sentences)")
print("="*60)
sample_sentences = labels_df["sentence"].tolist()
human_labels = []
for raw in labels_df["aspects"].tolist():
    if str(raw).strip().lower() in ("", "none", "nan"):
        human_labels.append(set())
    else:
        human_labels.append({t.strip().lower() for t in str(raw).split(",")})
validate_absa_accuracy(sample_sentences, human_labels)

# ── C: Query detection validation ─────────────────────────────────────────────
print("\n" + "="*60)
print("C  Query Detection Validation (Standard B: must rank top-2)")
print("="*60)
validate_query_detection(TEST_CASES, get_aspect_prefs)

# ── D: Sensitivity analysis ───────────────────────────────────────────────────
print("\n" + "="*60)
print("D  Sensitivity Analysis  (α/β/γ grid search, proxy metric)")
print("="*60)

num_reviews = reviews_df.groupby("gmap_id").size().rename("num_reviews").reset_index()
candidates_df = (
    clusters_df[["gmap_id", "avg_rating"]]
    .merge(num_reviews, on="gmap_id", how="left")
    .fillna({"num_reviews": 0})
)

user_pref = get_aspect_prefs("cozy restaurant with great food and reasonable price")
print(f"Query prefs used: { {k: round(v,3) for k,v in user_pref.items()} }\n")

results_df = sensitivity_analysis(candidates_df, aspect_scores_df, user_pref)

print(f"{'alpha':>6} {'beta':>6} {'gamma':>6} {'metric':>10}")
print("-" * 35)
for _, row in results_df.head(15).iterrows():
    print(f"{row['alpha']:>6.1f} {row['beta']:>6.1f} {row['gamma']:>6.1f} {row['metric']:>10.4f}")

OUT = "results/sensitivity_analysis.csv"
os.makedirs("results", exist_ok=True)
results_df.to_csv(OUT, index=False)
print(f"\nFull results saved → {OUT}")

best = results_df.iloc[0]
print(f"\nBest combination: α={best['alpha']}, β={best['beta']}, γ={best['gamma']}  (metric={best['metric']:.4f})")
print("\nNext: choose α/β/γ and run step3_sensitivity_demo.py.")
