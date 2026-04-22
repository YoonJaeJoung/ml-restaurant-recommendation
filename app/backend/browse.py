"""
browse.py — returns all restaurants in NYC for the browse-all map view.

This endpoint is large but read-only: ~19k restaurants with coordinates.
Returned once per session, then cached client-side.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.similarity import has_valid_nyc_zip

from .schemas import BrowsePoint, BrowseResponse
from .state   import STATE


def _opt_float(v) -> float | None:
    try:
        f = float(v)
        if np.isnan(f):
            return None
        return f
    except Exception:
        return None


def _opt_str(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    s = str(v)
    return s if s else None


def get_all_points() -> BrowseResponse:
    meta = STATE.meta
    has_coords   = meta["latitude"].notna() & meta["longitude"].notna()
    has_nyc_zip  = meta["address"].map(has_valid_nyc_zip)
    # The "≥15 reviews" gate uses the FILTERED (English-only) review count,
    # matching src/1_data_processing.py which drops Chinese-only reviews and
    # keeps only restaurants with >15 remaining English reviews. Since
    # reviews_full is already the filtered parquet, membership alone is enough.
    qualifying_ids = set(STATE.reviews_full["gmap_id"].unique())
    has_en_reviews = meta["gmap_id"].isin(qualifying_ids)
    mask = has_coords & has_nyc_zip & has_en_reviews
    subset = meta.loc[mask, [
        "gmap_id", "name", "latitude", "longitude", "borough", "avg_rating", "price"
    ]]
    points: list[BrowsePoint] = []
    for _, r in subset.iterrows():
        lat = _opt_float(r.get("latitude"))
        lon = _opt_float(r.get("longitude"))
        if lat is None or lon is None:
            continue
        points.append(BrowsePoint(
            gmap_id=str(r["gmap_id"]),
            name=str(r.get("name", "")),
            latitude=lat,
            longitude=lon,
            borough=_opt_str(r.get("borough")),
            avg_rating=_opt_float(r.get("avg_rating")),
            price=_opt_str(r.get("price")) if isinstance(r.get("price"), str) else None,
        ))
    return BrowseResponse(total=len(points), points=points)
