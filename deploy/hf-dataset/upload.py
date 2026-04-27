"""
upload.py — one-time push of the six required backend artifacts to an HF Dataset.

Prereqs:
    pip install huggingface_hub
    huggingface-cli login    # with a write-scoped token

Usage:
    python deploy/hf-dataset/upload.py <user>/nyc-restaurant-artifacts [--public|--private]

The Dataset repo must already exist (create it via the HF website or
huggingface_hub.create_repo). Files are uploaded preserving the same relative
paths the backend expects, so on the Space side `ARTIFACTS_DIR` can be pointed
at the downloaded snapshot root and state.py resolves everything unchanged.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi, create_repo
from huggingface_hub.utils import RepositoryNotFoundError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Keep this list in sync with app/backend/state.py:_verify_paths.
ARTIFACTS = [
    "data/processed/review-NYC-restaurant-filtered.parquet",
    "data/processed/meta-NYC-restaurant.parquet",
    "results/pca/review_embeddings_pca.npy",
    "results/pca/pca_model.pkl",
    "results/clustering/cluster_centroids.npy",
    "results/clustering/restaurant_clusters.csv",
    "results/clustering/evaluation/cluster_summary.json",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_id", help="HF Dataset repo id, e.g. <user>/nyc-restaurant-artifacts")
    ap.add_argument("--private", action="store_true", help="Create as private if it doesn't exist")
    args = ap.parse_args()

    missing = [p for p in ARTIFACTS if not (REPO_ROOT / p).exists()]
    if missing:
        print("error: missing local artifacts (run the pipeline first):", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        return 1

    api = HfApi()

    try:
        api.repo_info(repo_id=args.repo_id, repo_type="dataset")
        print(f"[upload] using existing dataset repo {args.repo_id}")
    except RepositoryNotFoundError:
        print(f"[upload] creating dataset repo {args.repo_id} (private={args.private})")
        create_repo(repo_id=args.repo_id, repo_type="dataset", private=args.private)

    # Stage only the needed files into a temp tree, preserving relative paths,
    # then upload_folder that. Avoids bundling the entire repo.
    with tempfile.TemporaryDirectory() as staging:
        staging_root = Path(staging)
        for rel in ARTIFACTS:
            src = REPO_ROOT / rel
            dst = staging_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.symlink_to(src.resolve())

        total_mb = sum((REPO_ROOT / p).stat().st_size for p in ARTIFACTS) / 1e6
        print(f"[upload] staging {len(ARTIFACTS)} files ({total_mb:,.0f} MB). Uploading...")

        api.upload_folder(
            folder_path=str(staging_root),
            repo_id=args.repo_id,
            repo_type="dataset",
            commit_message="upload backend artifacts",
        )

    print("[upload] done.")
    print(f"         https://huggingface.co/datasets/{args.repo_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
