"""
geo.py — geographic filtering for restaurant candidates.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from shapely.geometry import Point, Polygon

from .schemas import LocationFilter


EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Vectorized haversine: one query point → array of distances."""
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = np.radians(lat2)
    lon2_r = np.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2) ** 2 + math.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return EARTH_RADIUS_KM * c


def filter_by_location(meta: pd.DataFrame, loc: LocationFilter) -> pd.Series:
    """
    Return a boolean mask over `meta` indicating which restaurants pass the
    location filter. Missing lat/lon are always excluded for non-'all' modes.
    """
    if loc.mode == "all":
        return pd.Series(True, index=meta.index)

    if loc.mode == "borough":
        if not loc.boroughs:
            raise ValueError("borough mode requires at least one borough")
        return meta["borough"].isin(loc.boroughs)

    has_coords = meta["latitude"].notna() & meta["longitude"].notna()

    if loc.mode == "radius":
        if not loc.center or loc.radius_km is None:
            raise ValueError("radius mode requires center and radius_km")
        lat0, lon0 = loc.center
        dist = _haversine_km(
            lat0, lon0,
            meta["latitude"].fillna(0).to_numpy(),
            meta["longitude"].fillna(0).to_numpy(),
        )
        return has_coords & (pd.Series(dist, index=meta.index) <= loc.radius_km)

    if loc.mode == "bbox":
        if not loc.bbox:
            raise ValueError("bbox mode requires bbox=[[s,w],[n,e]]")
        (s, w), (n, e) = loc.bbox
        in_box = (
            (meta["latitude"] >= s) & (meta["latitude"] <= n)
            & (meta["longitude"] >= w) & (meta["longitude"] <= e)
        )
        return has_coords & in_box

    if loc.mode == "polygon":
        if not loc.polygon or len(loc.polygon) < 3:
            raise ValueError("polygon mode requires >=3 vertices")
        poly = Polygon([(lon, lat) for lat, lon in loc.polygon])   # shapely uses (x=lon, y=lat)
        # shapely's contains is Python-level per point; meta has ~28k rows which is fine.
        mask = has_coords.copy()
        coords = meta[["latitude", "longitude"]].to_numpy()
        hits = np.zeros(len(meta), dtype=bool)
        for i, (lat, lon) in enumerate(coords):
            if np.isnan(lat) or np.isnan(lon):
                continue
            if poly.contains(Point(lon, lat)):
                hits[i] = True
        return mask & pd.Series(hits, index=meta.index)

    raise ValueError(f"unknown location mode {loc.mode!r}")
