"""
step1_precompute.py  —  Step 1: precompute ABSA aspect scores (offline, ~1-2h)

Run from project root:
    python src/ranking/scripts/step1_precompute.py

Output:
    data/processed/aspect_scores.parquet   (21k restaurants × 4 aspects)
    data/validation/sample_sentences.csv   (100 sentences for manual labeling)

After running: label sample_sentences.csv (add 'aspects' column),
then run step2_validation.py.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import time
import pandas as pd
from src.ranking.absa import precompute_all_aspect_scores

REVIEWS_PATH  = "data/processed/review-NYC-restaurant-filtered.parquet"
SCORES_OUT    = "data/processed/aspect_scores.parquet"
SENTENCES_OUT = "data/validation/sample_sentences.csv"

print(f"Loading reviews from {REVIEWS_PATH} ...")
reviews_df = pd.read_parquet(REVIEWS_PATH)
print(f"Loaded {len(reviews_df):,} reviews for {reviews_df['gmap_id'].nunique():,} restaurants.\n")

print("Starting precompute_all_aspect_scores()  (this will take ~1-2 hours) ...")
t0 = time.time()
aspect_scores_df, priors = precompute_all_aspect_scores(reviews_df, save_path=SCORES_OUT)
elapsed = time.time() - t0
print(f"Done in {elapsed/60:.1f} min — {len(aspect_scores_df):,} restaurants scored.")

os.makedirs("data/validation", exist_ok=True)
print(f"\nSampling 100 sentences → {SENTENCES_OUT}")
sample_sentences = reviews_df["text"].dropna().sample(100, random_state=42).tolist()
pd.DataFrame({"sentence": sample_sentences}).to_csv(SENTENCES_OUT, index=False)
print("Done. Open the CSV, add a column 'aspects' (comma-separated, e.g. food,service).")
print("Label BEFORE looking at system output to avoid confirmation bias.")
print("\nNext: hand labeled CSV back, then run step2_validation.py.")
