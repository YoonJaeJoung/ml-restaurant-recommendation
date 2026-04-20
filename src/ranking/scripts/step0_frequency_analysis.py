"""
step0_frequency_analysis.py  —  Step 0: word-frequency analysis

Run from project root:
    python src/ranking/scripts/step0_frequency_analysis.py

Output:
    data/processed/word_frequency_top500.csv
    data/processed/aspect_keyword_frequency.csv

After reviewing output: update ASPECT_KEYWORDS in src/ranking/absa.py,
then proceed to step1_precompute.py.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pandas as pd
from src.ranking.absa import frequency_analysis, ASPECT_KEYWORDS

REVIEWS_PATH = "data/processed/review-NYC-restaurant-filtered.parquet"

print(f"Loading reviews from {REVIEWS_PATH} ...")
reviews_df = pd.read_parquet(REVIEWS_PATH)
print(f"Loaded {len(reviews_df):,} reviews for {reviews_df['gmap_id'].nunique():,} restaurants.\n")

freq = frequency_analysis(reviews_df, top_n=30)

FREQ_OUT = "data/processed/word_frequency_top500.csv"
top500 = pd.DataFrame(freq.most_common(500), columns=["word", "count"])
top500.to_csv(FREQ_OUT, index=False)
print(f"\nTop-500 word frequencies saved → {FREQ_OUT}")

rows = []
for aspect, keywords in ASPECT_KEYWORDS.items():
    for kw in keywords:
        rows.append({"aspect": aspect, "keyword": kw, "count": freq.get(kw, 0)})
KW_OUT = "data/processed/aspect_keyword_frequency.csv"
pd.DataFrame(rows).to_csv(KW_OUT, index=False)
print(f"Aspect keyword frequencies saved → {KW_OUT}")

print("\nStep 0 complete.")
print("Next: review output, update ASPECT_KEYWORDS in src/ranking/absa.py if needed,")
print("then run step1_precompute.py.")
