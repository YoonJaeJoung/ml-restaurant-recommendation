"""
state.py — module-level singleton holding heavy ML artifacts.

All artifacts (sentence-transformer, PCA model, 2.1M review embeddings memmap,
centroids, cluster assignments, meta, review metadata) are loaded exactly once
on app startup and reused across every request. This is intentional for a
single-process dev server; if we ever horizontally scale, swap to a shared
cache or process pool that loads each on fork.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# Allow `from src.xxx import ...` — the backend lives in app/backend/, source in ../../src/
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.absa       import ASPECT_COLS
from src.similarity import load_model, load_pca_model, load_embeddings_raw


# ── Artifact paths (relative to repo root) ──────────────────────────────────
REVIEW_PATH         = REPO_ROOT / "data/processed/review-NYC-restaurant-filtered.parquet"
META_PATH           = REPO_ROOT / "data/processed/meta-NYC-restaurant.parquet"
PCA_EMBEDDINGS_PATH = REPO_ROOT / "results/pca/review_embeddings_pca.npy"
PCA_MODEL_PATH      = REPO_ROOT / "results/pca/pca_model.pkl"
CENTROIDS_PATH      = REPO_ROOT / "results/clustering/cluster_centroids.npy"
CLUSTERS_PATH       = REPO_ROOT / "results/clustering/restaurant_clusters.csv"
CLUSTER_SUMMARY     = REPO_ROOT / "results/clustering/evaluation/cluster_summary.json"

PCA_DIM = 128


@dataclass
class AppState:
    model:              object | None          = None
    pca:                object | None          = None
    embeddings_pca:     np.ndarray | None      = None
    reviews_gmap_ids:   pd.DataFrame | None    = None    # minimal: only gmap_id col
    reviews_full:       pd.DataFrame | None    = None    # full reviews for detail endpoint
    meta:               pd.DataFrame | None    = None
    centroids:          np.ndarray | None      = None
    clusters:           pd.DataFrame | None    = None
    cluster_info:       dict = field(default_factory=dict)   # cluster_id → summary dict
    log_reviews_max:    float = 1.0
    loaded: bool = False


STATE = AppState()


def _verify_paths() -> list[str]:
    required = [REVIEW_PATH, META_PATH, PCA_EMBEDDINGS_PATH,
                PCA_MODEL_PATH, CENTROIDS_PATH, CLUSTERS_PATH]
    return [str(p) for p in required if not p.exists()]


def load_all() -> None:
    """Idempotent loader. Call once at FastAPI startup."""
    if STATE.loaded:
        return

    missing = _verify_paths()
    if missing:
        raise FileNotFoundError(
            "Missing required artifacts:\n  - " + "\n  - ".join(missing)
            + "\n\nRun the pipeline scripts (1→8) first."
        )

    print("[state] loading sentence-transformer + PCA model...")
    STATE.model = load_model()
    STATE.pca   = load_pca_model(str(PCA_MODEL_PATH))

    print("[state] memmap'ing 2.1M review embeddings (128-dim)...")
    STATE.embeddings_pca = load_embeddings_raw(str(PCA_EMBEDDINGS_PATH), PCA_DIM)

    print("[state] loading review gmap_id column (for search) + full review text (for detail)...")
    STATE.reviews_gmap_ids = pd.read_parquet(str(REVIEW_PATH), columns=["gmap_id"])
    # Full review text needed by the detail endpoint. Keep as a single load since
    # we memmap embeddings parallel to reviews_gmap_ids order.
    STATE.reviews_full = pd.read_parquet(str(REVIEW_PATH))

    print("[state] loading meta (with aspect columns)...")
    STATE.meta = pd.read_parquet(str(META_PATH))
    missing_cols = [c for c in ASPECT_COLS if c not in STATE.meta.columns]
    if missing_cols:
        raise RuntimeError(
            f"meta parquet is missing aspect columns {missing_cols}. "
            "Run `python src/8_ranking.py` first."
        )

    print("[state] loading cluster centroids + assignments + summary...")
    STATE.centroids = np.load(str(CENTROIDS_PATH))
    STATE.clusters  = pd.read_csv(str(CLUSTERS_PATH))
    if CLUSTER_SUMMARY.exists():
        import json
        with open(CLUSTER_SUMMARY) as f:
            STATE.cluster_info = {c["cluster_id"]: c for c in json.load(f)}

    # Cache the global log-reviews max for stable ranking across queries.
    counts = STATE.reviews_gmap_ids.groupby("gmap_id").size()
    STATE.log_reviews_max = float(np.log1p(counts.max()))

    STATE.loaded = True
    print(f"[state] ready — "
          f"{len(STATE.meta):,} meta rows, "
          f"{len(STATE.reviews_full):,} reviews, "
          f"log_reviews_max={STATE.log_reviews_max:.2f}")
