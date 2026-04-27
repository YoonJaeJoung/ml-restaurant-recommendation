"""
detail.py — restaurant detail endpoint logic.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.ranking import PRICE_TIER_BLEND, tier_to_score

from .schemas import (
    AspectBreakdown,
    RestaurantDetail,
    ReviewItem,
    ReviewsPage,
)
from .state import STATE


# ── Photo URL extraction ────────────────────────────────────────────────────
# The `pics` column is stored as an array of dicts:
#   [ {"url": array(["https://..."], dtype=object)}, ... ]
# Some reviews have no photos, some have multiple. We flatten to a list of
# URL strings.
def _extract_photos(pics: Any) -> list[str]:
    if pics is None:
        return []
    if isinstance(pics, float) and pd.isna(pics):
        return []
    urls: list[str] = []
    try:
        for entry in pics:
            u = entry.get("url") if isinstance(entry, dict) else None
            if u is None:
                continue
            if isinstance(u, (list, tuple, np.ndarray)):
                for uu in u:
                    if uu:
                        urls.append(str(uu))
            else:
                urls.append(str(u))
    except Exception:
        pass
    return urls


def _row_to_optional_str(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    return str(v)


def _row_to_optional_float(v) -> float | None:
    try:
        f = float(v)
        if np.isnan(f):
            return None
        return f
    except Exception:
        return None


def _row_to_optional_int(v) -> int | None:
    f = _row_to_optional_float(v)
    return int(f) if f is not None else None


def _list_or_none(v):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, np.ndarray):
        return [str(x) for x in v.tolist()]
    if isinstance(v, list):
        return [str(x) for x in v]
    return None


def _misc_to_dict(v) -> dict | None:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, dict):
        # Convert numpy arrays inside to lists so pydantic is happy.
        out = {}
        for k, x in v.items():
            if isinstance(x, np.ndarray):
                out[str(k)] = [str(i) for i in x.tolist()]
            elif isinstance(x, (list, tuple)):
                out[str(k)] = [str(i) for i in x]
            else:
                out[str(k)] = x
        return out
    return None


def get_detail(gmap_id: str) -> RestaurantDetail | None:
    meta = STATE.meta
    hit = meta[meta["gmap_id"] == gmap_id]
    if hit.empty:
        return None
    r = hit.iloc[0]

    absa_price_raw  = _row_to_optional_float(r.get("aspect_price"))
    price_tier_str  = _row_to_optional_str(r.get("price"))
    price_blended   = None
    if absa_price_raw is not None:
        ts = tier_to_score(price_tier_str)
        price_blended = PRICE_TIER_BLEND * absa_price_raw + (1 - PRICE_TIER_BLEND) * ts

    aspects = AspectBreakdown(
        food=_row_to_optional_float(r.get("aspect_food")),
        service=_row_to_optional_float(r.get("aspect_service")),
        price=absa_price_raw,
        price_blended=price_blended,
        wait_time=_row_to_optional_float(r.get("aspect_wait_time")),
        price_pct=_row_to_optional_int(r.get("aspect_price_pct")),
        wait_time_pct=_row_to_optional_int(r.get("aspect_wait_time_pct")),
    )

    return RestaurantDetail(
        gmap_id=str(r["gmap_id"]),
        name=str(r.get("name", "")),
        address=_row_to_optional_str(r.get("address")),
        borough=_row_to_optional_str(r.get("borough")),
        state=_row_to_optional_str(r.get("state")),
        latitude=_row_to_optional_float(r.get("latitude")),
        longitude=_row_to_optional_float(r.get("longitude")),
        description=_row_to_optional_str(r.get("description")),
        category=_list_or_none(r.get("category")),
        price=price_tier_str,
        url=_row_to_optional_str(r.get("url")),
        hours=_list_or_none(r.get("hours")),
        misc=_misc_to_dict(r.get("MISC")),
        avg_rating=_row_to_optional_float(r.get("avg_rating")),
        num_of_reviews=_row_to_optional_int(r.get("num_of_reviews")),
        aspects=aspects,
    )


def get_reviews(gmap_id: str, page: int = 1, page_size: int = 10) -> ReviewsPage:
    reviews = STATE.reviews_full
    subset = reviews[reviews["gmap_id"] == gmap_id]

    # Sort: reviews that have photos first (more useful in UI), then by time desc.
    has_photos = subset["pics"].apply(lambda p: bool(_extract_photos(p)))
    subset = subset.assign(_has_photos=has_photos)
    if "time" in subset.columns:
        subset = subset.sort_values(["_has_photos", "time"], ascending=[False, False])
    else:
        subset = subset.sort_values("_has_photos", ascending=False)

    total = len(subset)
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    offset = (page - 1) * page_size
    page_df = subset.iloc[offset : offset + page_size]

    items: list[ReviewItem] = []
    for _, r in page_df.iterrows():
        # Prefer the translated/English-only text (stripped by
        # `select_english_text` in src/1_data_processing.py) so reviewers that
        # Google translated don't double-render with the original.
        text_en = _row_to_optional_str(r.get("text_for_embedding"))
        items.append(ReviewItem(
            user_id=_row_to_optional_str(r.get("user_id")),
            reviewer_name=_row_to_optional_str(r.get("name")),
            rating=_row_to_optional_float(r.get("rating")),
            time=_row_to_optional_int(r.get("time")),
            text=text_en or _row_to_optional_str(r.get("text")),
            photos=_extract_photos(r.get("pics")),
        ))

    return ReviewsPage(
        gmap_id=gmap_id,
        total=total,
        page=page,
        page_size=page_size,
        reviews=items,
    )
