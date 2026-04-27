"""
schemas.py — Pydantic request/response models for the backend API.
"""
from __future__ import annotations

from datetime import datetime, time
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Location filter ─────────────────────────────────────────────────────────
LatLon = tuple[float, float]


class LocationFilter(BaseModel):
    """
    Five supported modes:
      * all      — entire NYC (no geographic filter)
      * borough  — one or more of the 5 NYC boroughs
      * radius   — circle of `radius_km` around `center`
      * bbox     — axis-aligned viewport rectangle [[south, west], [north, east]]
      * polygon  — arbitrary closed shape (freeform polygon of >=3 lat/lon vertices)
    """
    mode: Literal["all", "borough", "radius", "bbox", "polygon"] = "all"
    boroughs: Optional[list[str]] = None
    center: Optional[LatLon] = None
    radius_km: Optional[float] = None
    bbox: Optional[tuple[LatLon, LatLon]] = None
    polygon: Optional[list[LatLon]] = None


class TimeFilter(BaseModel):
    """
    at: local date+time the user intends to visit (ISO string).
    any_time: when true, skip hours-based filtering entirely ("search all time").

    NOTE: this field used to be called `datetime` but that shadowed the imported
    `datetime` type in the class body, so Pydantic resolved the annotation to
    a self-reference and rejected any value other than None with "Input should
    be None" (422 Unprocessable Entity).
    """
    at: Optional[datetime] = None
    any_time: bool = False


# ── Query structure ─────────────────────────────────────────────────────────
class ToggleSelection(BaseModel):
    """Mirrors the 4 questions in src/10_query_construction.py."""
    occasion: Optional[str] = None
    vibe: Optional[str] = None
    cuisine: Optional[str] = None    # "No preference" treated as None
    priority: Optional[list[str]] = None   # multi-select, "None" treated as None


class SearchRequest(BaseModel):
    query: Optional[str] = None
    toggles: Optional[ToggleSelection] = None
    location: LocationFilter = Field(default_factory=LocationFilter)
    time: TimeFilter = Field(default_factory=TimeFilter)
    limit: int = 30
    alpha: float = 0.4
    beta: float = 0.5
    gamma: float = 0.1


# ── Response: summary card in the result list ───────────────────────────────
class MatchedCluster(BaseModel):
    id: int
    top_keywords: list[str]


class RestaurantSummary(BaseModel):
    gmap_id: str
    name: str
    borough: Optional[str] = None
    avg_rating: Optional[float] = None
    num_of_reviews: Optional[int] = None
    price: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    final_score: float
    rank: int
    # ABSA aspect scores (precomputed in the meta parquet; used by the
    # Results sidebar to sort client-side without extra requests).
    aspect_food: Optional[float] = None
    aspect_service: Optional[float] = None
    aspect_price: Optional[float] = None                 # raw ABSA
    aspect_price_blended: Optional[float] = None         # 50/50 ABSA + $ tier
    aspect_wait_time: Optional[float] = None


class SearchResponse(BaseModel):
    query_effective: str                    # the string actually sent to the model
    user_prefs: dict[str, float]            # normalized 4-way aspect weights
    alpha: float
    beta: float
    gamma: float
    matched_clusters: list[MatchedCluster]
    results: list[RestaurantSummary]
    total_candidates: int                   # before the location filter
    filtered_candidates: int                # after the location/time filter
    retrieval_ms: float
    rank_ms: float


# ── Response: detail view ───────────────────────────────────────────────────
class AspectBreakdown(BaseModel):
    food: Optional[float] = None
    service: Optional[float] = None
    price: Optional[float] = None                # raw ABSA (not blended)
    price_blended: Optional[float] = None        # blended (ABSA + $$ tier)
    wait_time: Optional[float] = None


class ReviewItem(BaseModel):
    user_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    rating: Optional[float] = None
    time: Optional[int] = None                   # unix ms
    text: Optional[str] = None
    photos: list[str] = []                       # URL list (may be empty)


class RestaurantDetail(BaseModel):
    gmap_id: str
    name: str
    address: Optional[str] = None
    borough: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    category: Optional[list[str]] = None
    price: Optional[str] = None
    url: Optional[str] = None
    hours: Optional[list[str]] = None
    misc: Optional[dict] = None
    avg_rating: Optional[float] = None
    num_of_reviews: Optional[int] = None
    aspects: AspectBreakdown
    # Scores from the last search, passed back via query params for display
    last_search_score: Optional[dict] = None


class ReviewsPage(BaseModel):
    gmap_id: str
    total: int
    page: int
    page_size: int
    reviews: list[ReviewItem]


# ── Browse-all response ─────────────────────────────────────────────────────
class BrowsePoint(BaseModel):
    gmap_id: str
    name: str
    latitude: float
    longitude: float
    borough: Optional[str] = None
    avg_rating: Optional[float] = None
    price: Optional[str] = None


class BrowseResponse(BaseModel):
    total: int
    points: list[BrowsePoint]
