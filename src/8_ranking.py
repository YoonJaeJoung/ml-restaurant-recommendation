"""
8_ranking.py  —  Offline precompute of ABSA aspect scores.

Writes four per-aspect columns (aspect_food, aspect_service, aspect_price,
aspect_wait_time) directly into data/processed/meta-NYC-restaurant.parquet,
globally min-max normalized to [0,1] across the ~19.5k restaurants that
pass the ≥15-review filter. Restaurants without reviews get NaN in those
columns. Price is stored UNBLENDED; blending with the Google Maps tier
($/$$/$$$/$$$$) happens at query-time inside the ranker so the two signals
stay separately inspectable.

Run from project root:
    python src/8_ranking.py
"""
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.absa import precompute_all_aspect_scores

REVIEWS_PATH = "data/processed/review-NYC-restaurant-filtered.parquet"
META_PATH    = "data/processed/meta-NYC-restaurant.parquet"


def main() -> None:
    print(f"Loading reviews from {REVIEWS_PATH} ...")
    reviews_df = pd.read_parquet(REVIEWS_PATH)
    print(f"Loaded {len(reviews_df):,} reviews "
          f"for {reviews_df['gmap_id'].nunique():,} restaurants.\n")

    print("Starting precompute_all_aspect_scores() — this takes ~1–2 h on a laptop.\n")
    t0 = time.time()
    priors, n_scored = precompute_all_aspect_scores(reviews_df, meta_path=META_PATH)
    elapsed = time.time() - t0

    print(f"\nDone in {elapsed/60:.1f} min — {n_scored:,} restaurants scored.")
    print(f"Global priors: { {k: round(v, 4) for k, v in priors.items()} }")
    print(f"Aspect columns appended in-place to {META_PATH}.")


if __name__ == "__main__":
    main()
