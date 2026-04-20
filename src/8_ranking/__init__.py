"""
src/8_ranking/
Ranking pipeline: formula, price-tier blending, sensitivity analysis,
and query-detection validation.

Run order (from project root):
  Step 0  python src/8_ranking/scripts/step0_frequency_analysis.py
  Step 1  python src/8_ranking/scripts/step1_precompute.py
  Step 2  python src/8_ranking/scripts/step2_validation.py
  Step 3  python src/8_ranking/scripts/step3_sensitivity_demo.py
"""
import itertools
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.8_ranking.absa import ASPECT_KEYWORDS

# Google Maps price tier → affordability score (higher = more affordable)
PRICE_TIER_MAP   = {"$": 1.0, "$$": 0.75, "$$$": 0.25, "$$$$": 0.0}
PRICE_TIER_BLEND = 0.5   # fraction given to ABSA; remainder to tier score


def add_price_tier_score(candidates_df, meta_df):
    """
    Merge Google Maps price tier ($/$$/$$$/$$$$) into candidates as a [0,1] score.
    Restaurants without a tier get 0.5 (neutral).
    Call this before rank_candidates so the tier is available for blending.
    """
    tier = meta_df[["gmap_id", "price"]].copy()
    tier["price_tier_score"] = tier["price"].map(PRICE_TIER_MAP).fillna(0.5)
    return candidates_df.merge(
        tier[["gmap_id", "price_tier_score"]], on="gmap_id", how="left"
    ).fillna({"price_tier_score": 0.5})


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Ranking Formula
# ─────────────────────────────────────────────────────────────────────────────

def rank_candidates(candidates_df, aspect_scores_df, user_pref, alpha, beta, gamma):
    """
    Re-rank similarity-search candidates using a weighted scoring formula.

    candidates_df    : output of search_pca_within_clusters() with num_reviews added
                       required columns: gmap_id, avg_rating, num_reviews
                       optional column : price_tier_score (from add_price_tier_score)
    aspect_scores_df : precomputed aspect scores (data/processed/aspect_scores.parquet)
    user_pref        : get_aspect_prefs(query) output — aspect weight dict
    alpha/beta/gamma : hyper-parameters (auto-normalized in demo_search.py)

    final_score = α × avg_rating_norm
               + β × aspect_weighted_norm
               + γ × log(1 + num_reviews)_norm

    Each aspect is independently min-max normalized within the candidate set
    before weighting, so user weights reflect true relative importance regardless
    of different baseline means across aspects (e.g. wait_time is systematically
    lower than price due to negativity bias in reviews).

    Price blending: when price_tier_score is present, ABSA price is replaced by
    PRICE_TIER_BLEND * absa_price_01 + (1-PRICE_TIER_BLEND) * tier_score,
    giving cheap restaurants ($ tier) a bonus independent of review mentions.
    """
    df = candidates_df.merge(aspect_scores_df, on="gmap_id", how="left")

    # Blend ABSA price with Google Maps tier when available
    if "price_tier_score" in df.columns:
        absa_lo, absa_hi = df["price"].min(), df["price"].max()
        absa_01 = (df["price"] - absa_lo) / (absa_hi - absa_lo + 1e-9)
        df["price"] = (PRICE_TIER_BLEND * absa_01 +
                       (1 - PRICE_TIER_BLEND) * df["price_tier_score"])

    def _norm(s):
        lo, hi = s.min(), s.max()
        return (s - lo) / (hi - lo + 1e-9) if hi > lo else pd.Series(0.5, index=s.index)

    # Normalize each aspect to [0,1] within candidates before weighting
    for aspect in ASPECT_KEYWORDS:
        df[aspect] = _norm(df[aspect])

    df["aspect_weighted"] = sum(
        df[aspect] * user_pref[aspect]
        for aspect in ASPECT_KEYWORDS
    )

    rating_norm   = _norm(df["avg_rating"])
    aspect_norm   = _norm(df["aspect_weighted"])
    log_reviews   = _norm(np.log1p(df["num_reviews"]))

    df["final_score"] = (
        alpha * rating_norm  +
        beta  * aspect_norm  +
        gamma * log_reviews
    )

    return df.sort_values("final_score", ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Sensitivity Analysis
# ─────────────────────────────────────────────────────────────────────────────

def sensitivity_analysis(candidates_df, aspect_scores_df, user_pref,
                          human_scores_dict=None):
    """
    Grid-search α/β/γ combinations and rank by a quality metric.

    human_scores_dict : {gmap_id: relevance_score} from manual evaluation.
                        If None, uses Spearman correlation with avg_rating rank
                        as a proxy (lower correlation = more independent of rating).
    """
    weight_candidates = [0.1, 0.2, 0.3, 0.4, 0.5]
    results = []

    for alpha, beta, gamma in itertools.product(weight_candidates, repeat=3):
        if abs(alpha + beta + gamma - 1.0) > 0.01:
            continue
        ranked = rank_candidates(candidates_df, aspect_scores_df,
                                  user_pref, alpha, beta, gamma)
        if human_scores_dict:
            ranked["human"] = ranked["gmap_id"].map(human_scores_dict).fillna(0)
            metric = ranked["human"].mean()
        else:
            rating_rank = ranked["avg_rating"].rank(ascending=False)
            final_rank  = ranked["final_score"].rank(ascending=False)
            metric, _   = spearmanr(rating_rank, final_rank)

        results.append({"alpha": alpha, "beta": beta, "gamma": gamma, "metric": metric})

    return pd.DataFrame(results).sort_values("metric", ascending=False)


# ─────────────────────────────────────────────────────────────────────────────
# Step 5.4 — Query Detection Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_query_detection(test_cases, get_aspect_prefs_fn):
    """
    Standard B: a detected aspect must rank in the top-2 to count.

    test_cases : list of dicts with keys:
        query, expected_boosted (list), expected_suppressed (list, optional)
    """
    correct, total = 0, 0

    print(f"\n{'Query':<45} {'Result'}")
    print("-" * 75)

    for case in test_cases:
        query    = case["query"]
        detected = get_aspect_prefs_fn(query)

        sorted_aspects = sorted(detected.items(), key=lambda x: x[1], reverse=True)
        top2    = {a for a, _ in sorted_aspects[:2]}
        bottom2 = {a for a, _ in sorted_aspects[-2:]}

        boosted    = case.get("expected_boosted",    [])
        suppressed = case.get("expected_suppressed", [])
        case_results = []

        for aspect in boosted:
            total += 1
            ok     = aspect in top2
            correct += int(ok)
            case_results.append(f"{aspect}↑{'✅' if ok else '❌'}")

        for aspect in suppressed:
            total += 1
            ok     = aspect in bottom2
            correct += int(ok)
            case_results.append(f"{aspect}↓{'✅' if ok else '❌'}")

        print(f"{query:<45} {', '.join(case_results)}")

    accuracy = correct / total if total > 0 else 0.0
    print(f"\nQuery Detection Accuracy: {correct}/{total} = {accuracy:.1%}")
    return accuracy


TEST_CASES = [
    {"query": "I want something cheap",
     "expected_boosted": ["price"]},
    {"query": "looking for fast service",
     "expected_boosted": ["wait_time", "service"]},
    {"query": "best ramen with amazing food",
     "expected_boosted": ["food"]},
    {"query": "quick affordable chinese lunch",
     "expected_boosted": ["wait_time", "price"]},
    {"query": "great burger not overpriced",
     "expected_boosted": ["food", "price"]},
]


print("src/8_ranking loaded.")
