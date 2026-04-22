"""
search.py — end-to-end search orchestration.

Flow:
    build_query(toggles, free_text)
    → embed_query + cluster-aware PCA search (similarity.search_pca_within_clusters)
    → location filter (geo.filter_by_location)
    → time filter (hours.is_open_at)
    → ranking formula (ranking.rank_candidates)
    → slice top N
"""
from __future__ import annotations

import time as _time
from typing import Optional

import numpy as np
import pandas as pd

from src.absa       import get_aspect_prefs
from src.ranking    import PRICE_TIER_BLEND, rank_candidates, tier_to_score
from src.similarity import has_valid_nyc_zip, search_pca_within_clusters

from .geo           import filter_by_location
from .hours         import is_open_at
from .query_builder import build_query
from .schemas       import (
    MatchedCluster,
    RestaurantSummary,
    SearchRequest,
    SearchResponse,
)
from .state         import STATE


# Retrieval pool sizes. Bigger pool = better coverage when the location
# filter is strict, at the cost of some latency.
TOP_N_CLUSTERS       = 5
K_REVIEWS_PER_SEARCH = 500
RETRIEVAL_POOL       = 500        # restaurants out of the semantic stage


def _matched_clusters(best_clusters: list[int]) -> list[MatchedCluster]:
    out = []
    for cid in best_clusters:
        info = STATE.cluster_info.get(cid) or STATE.cluster_info.get(str(cid))
        kws  = (info or {}).get("top_keywords", [])[:5]
        out.append(MatchedCluster(id=int(cid), top_keywords=kws))
    return out


def _summary_rows(df: pd.DataFrame, limit: int) -> list[RestaurantSummary]:
    out: list[RestaurantSummary] = []
    for rank, (_, r) in enumerate(df.head(limit).iterrows(), 1):
        # Aspect scores may or may not be present on the ranked row depending
        # on whether src/ranking merged them in. If missing, fall back to the
        # canonical meta so the sidebar always has something to sort by.
        food    = _float_or_none(r.get("aspect_food"))
        service = _float_or_none(r.get("aspect_service"))
        price_r = _float_or_none(r.get("aspect_price"))
        waitt   = _float_or_none(r.get("aspect_wait_time"))
        price_tier_str = r.get("price") if isinstance(r.get("price"), str) else None
        price_blend = None
        if price_r is not None:
            price_blend = PRICE_TIER_BLEND * price_r + (1 - PRICE_TIER_BLEND) * tier_to_score(price_tier_str)

        out.append(RestaurantSummary(
            gmap_id=str(r["gmap_id"]),
            name=str(r.get("name", "")),
            borough=_none_if_nan(r.get("borough")),
            avg_rating=_float_or_none(r.get("avg_rating")),
            num_of_reviews=_int_or_none(r.get("num_of_reviews")),
            price=_none_if_nan(r.get("price")) if isinstance(r.get("price"), str) else None,
            latitude=_float_or_none(r.get("latitude")),
            longitude=_float_or_none(r.get("longitude")),
            final_score=float(r["final_score"]),
            rank=rank,
            aspect_food=food,
            aspect_service=service,
            aspect_price=price_r,
            aspect_price_blended=price_blend,
            aspect_wait_time=waitt,
        ))
    return out


def _float_or_none(v):
    try:
        f = float(v)
        if np.isnan(f):
            return None
        return f
    except Exception:
        return None


def _int_or_none(v):
    try:
        f = float(v)
        if np.isnan(f):
            return None
        return int(f)
    except Exception:
        return None


def _none_if_nan(v):
    if v is None:
        return None
    if isinstance(v, float) and np.isnan(v):
        return None
    return v


def do_search(req: SearchRequest) -> SearchResponse:
    if not STATE.loaded:
        raise RuntimeError("state not loaded")

    # 1. Compose query string
    query = build_query(req.toggles, req.query)
    if not query.strip():
        raise ValueError("empty query — provide 'query' or toggles")

    # 2. Detect aspect preferences
    prefs = get_aspect_prefs(query)

    # 3. Semantic retrieval
    t0 = _time.time()
    candidates, best_clusters = search_pca_within_clusters(
        query, STATE.model, STATE.pca, STATE.embeddings_pca,
        STATE.reviews_gmap_ids, STATE.meta,
        STATE.centroids, STATE.clusters,
        top_n_clusters=TOP_N_CLUSTERS,
        k=K_REVIEWS_PER_SEARCH,
        top_n=RETRIEVAL_POOL,
    )
    retrieval_ms = (_time.time() - t0) * 1000.0
    total_candidates = len(candidates)
    if total_candidates == 0:
        return SearchResponse(
            query_effective=query, user_prefs=prefs,
            alpha=req.alpha, beta=req.beta, gamma=req.gamma,
            matched_clusters=_matched_clusters(best_clusters),
            results=[], total_candidates=0, filtered_candidates=0,
            retrieval_ms=retrieval_ms, rank_ms=0.0,
        )

    # 4. Merge full meta (for lat/lon/hours/etc.) onto candidates if missing.
    merge_cols = [c for c in ["address", "latitude", "longitude", "hours"]
                  if c not in candidates.columns and c in STATE.meta.columns]
    if merge_cols:
        candidates = candidates.merge(
            STATE.meta[["gmap_id", *merge_cols]], on="gmap_id", how="left"
        )

    # 4b. NYC ZIP-prefix filter. Redundant with the guard inside
    # search_pca_within_clusters, but kept explicit here so future reviewers can
    # see that the backend never emits results from restaurants outside NYC,
    # regardless of how the retrieval layer is swapped out.
    candidates = candidates[candidates["address"].map(has_valid_nyc_zip)].copy()

    # 5. Location filter (mask via meta, then align to candidates)
    if req.location.mode != "all":
        meta_mask = filter_by_location(STATE.meta, req.location)
        allowed_ids = set(STATE.meta.loc[meta_mask, "gmap_id"])
        candidates = candidates[candidates["gmap_id"].isin(allowed_ids)].copy()

    # 6. Time filter
    if not req.time.any_time and req.time.at is not None:
        visit = req.time.at
        is_open = candidates["hours"].apply(lambda h: is_open_at(h, visit))
        # Only drop rows where we *know* they're closed; unknown stays in.
        candidates = candidates[is_open.fillna(True) == True].copy()

    filtered_candidates = len(candidates)
    if filtered_candidates == 0:
        return SearchResponse(
            query_effective=query, user_prefs=prefs,
            alpha=req.alpha, beta=req.beta, gamma=req.gamma,
            matched_clusters=_matched_clusters(best_clusters),
            results=[],
            total_candidates=total_candidates,
            filtered_candidates=0,
            retrieval_ms=retrieval_ms, rank_ms=0.0,
        )

    # 7. Rank
    t0 = _time.time()
    result = rank_candidates(
        candidates, STATE.meta, prefs,
        alpha=req.alpha, beta=req.beta, gamma=req.gamma,
        log_reviews_max=STATE.log_reviews_max,
    )
    rank_ms = (_time.time() - t0) * 1000.0

    return SearchResponse(
        query_effective=query,
        user_prefs=result.user_prefs,
        alpha=result.alpha, beta=result.beta, gamma=result.gamma,
        matched_clusters=_matched_clusters(best_clusters),
        results=_summary_rows(result.ranked, req.limit),
        total_candidates=total_candidates,
        filtered_candidates=filtered_candidates,
        retrieval_ms=retrieval_ms,
        rank_ms=rank_ms,
    )
