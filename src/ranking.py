"""
ranking.py — query-time ranking formula.

Combines four signals to produce a [0,1] final_score per candidate:

  final_score = α · rating_01
              + β · aspect_weighted
              + γ · log_reviews_01

Where:
  rating_01        = avg_rating / 5
  aspect_weighted  = Σ_i  w_i · aspect_i
                     — aspect_i already in [0,1] (globally normalized in meta parquet)
                     — for price, aspect_i is blended with the Google Maps tier:
                         price_blended = 0.5·aspect_price + 0.5·tier_score
                       so a cheap restaurant ($) gets a bonus independent of review sentiment.
                     — w_i are user aspect preferences, auto-normalized to sum to 1
  log_reviews_01   = log1p(num_reviews) / log1p(max_reviews_global)
                     — global normalization keeps scores comparable across queries

α/β/γ are auto-normalized to sum to 1, so final_score lives in [0,1].
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd


# Google Maps price tier → affordability score (higher = cheaper)
PRICE_TIER_MAP: dict[str, float] = {"$": 1.0, "$$": 0.75, "$$$": 0.25, "$$$$": 0.0}
PRICE_TIER_NEUTRAL = 0.5       # for missing tier
PRICE_TIER_BLEND   = 0.5       # weight given to ABSA; remainder goes to tier

ASPECTS: tuple[str, ...] = ("food", "service", "price", "wait_time")
ASPECT_COLS: tuple[str, ...] = tuple(f"aspect_{a}" for a in ASPECTS)

DEFAULT_ALPHA = 0.4
DEFAULT_BETA  = 0.5
DEFAULT_GAMMA = 0.1


def tier_to_score(tier: str | None) -> float:
    """Map '$', '$$', ... → affordability score in [0,1]. Unknown → neutral 0.5."""
    if tier is None or (isinstance(tier, float) and np.isnan(tier)):
        return PRICE_TIER_NEUTRAL
    return PRICE_TIER_MAP.get(str(tier).strip(), PRICE_TIER_NEUTRAL)


def normalize_prefs(prefs: dict[str, float]) -> dict[str, float]:
    """Auto-normalize user aspect weights so they sum to 1."""
    total = sum(max(0.0, prefs.get(a, 0.0)) for a in ASPECTS)
    if total <= 0:
        return {a: 0.25 for a in ASPECTS}
    return {a: max(0.0, prefs.get(a, 0.0)) / total for a in ASPECTS}


def normalize_abg(alpha: float, beta: float, gamma: float) -> tuple[float, float, float]:
    total = max(0.0, alpha) + max(0.0, beta) + max(0.0, gamma)
    if total <= 0:
        return (DEFAULT_ALPHA, DEFAULT_BETA, DEFAULT_GAMMA)
    return (max(0.0, alpha) / total, max(0.0, beta) / total, max(0.0, gamma) / total)


@dataclass
class RankingResult:
    ranked: pd.DataFrame
    alpha: float
    beta: float
    gamma: float
    user_prefs: dict[str, float]
    log_reviews_max: float


def rank_candidates(
    candidates: pd.DataFrame,
    meta: pd.DataFrame,
    user_prefs: dict[str, float],
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
    log_reviews_max: float | None = None,
) -> RankingResult:
    """
    Rank search candidates using the ABSA-weighted ranking formula.

    candidates
        DataFrame from similarity search. Must contain at least:
        gmap_id, avg_rating, num_of_reviews (or num_reviews).
    meta
        Full meta DataFrame with aspect_* cols + 'price' (Google tier).
        Only the rows matching candidate gmap_ids are used.
    user_prefs
        Dict of 4 aspect weights (food/service/price/wait_time), any
        magnitude — auto-normalized to sum to 1.
    alpha/beta/gamma
        Ranking-formula weights, auto-normalized to sum to 1.
    log_reviews_max
        Global max of log1p(num_reviews) used to scale review-count influence.
        Pass the cached value from state to keep ranking comparable across
        queries; if None, falls back to the max within the candidate set
        (degrades comparability slightly).
    """
    alpha, beta, gamma = normalize_abg(alpha, beta, gamma)
    prefs = normalize_prefs(user_prefs)

    df = candidates.copy()

    # Reconcile review-count column name between similarity.search_* outputs
    # (they expose num_of_reviews from meta) and any callers that pre-merge.
    if "num_reviews" not in df.columns:
        if "num_of_reviews" in df.columns:
            df["num_reviews"] = df["num_of_reviews"].fillna(0)
        else:
            df["num_reviews"] = 0

    # Attach aspect columns + price tier from meta (only if not already present).
    needed = ["price", *ASPECT_COLS]
    to_merge = [c for c in needed if c not in df.columns and c in meta.columns]
    if to_merge:
        df = df.merge(meta[["gmap_id", *to_merge]], on="gmap_id", how="left")

    # Blended price aspect: 50/50 ABSA + Google tier
    tier_score = df["price"].map(tier_to_score).astype(float)
    price_blended = (PRICE_TIER_BLEND * df["aspect_price"].fillna(0.5).astype(float)
                     + (1 - PRICE_TIER_BLEND) * tier_score)
    df["aspect_price_blended"] = price_blended

    # Weighted aspect combination (user prefs × already-normalized aspect scores)
    df["aspect_weighted"] = (
        prefs["food"]      * df["aspect_food"].fillna(0.5).astype(float)
        + prefs["service"] * df["aspect_service"].fillna(0.5).astype(float)
        + prefs["price"]   * price_blended
        + prefs["wait_time"] * df["aspect_wait_time"].fillna(0.5).astype(float)
    )

    # Rating on fixed [0,1] scale (divide by the known 5-point ceiling)
    df["rating_01"] = df["avg_rating"].fillna(0).clip(0, 5) / 5.0

    # Review-count on global log scale (fallback to local max if not passed)
    log_reviews = np.log1p(df["num_reviews"].fillna(0).clip(lower=0))
    denom = float(log_reviews_max) if log_reviews_max is not None else float(max(log_reviews.max(), 1.0))
    df["log_reviews_01"] = (log_reviews / denom).clip(0, 1) if denom > 0 else 0.0

    df["final_score"] = (
        alpha * df["rating_01"]
        + beta  * df["aspect_weighted"]
        + gamma * df["log_reviews_01"]
    )

    df = df.sort_values("final_score", ascending=False).reset_index(drop=True)

    return RankingResult(
        ranked=df,
        alpha=alpha, beta=beta, gamma=gamma,
        user_prefs=prefs,
        log_reviews_max=denom,
    )
