#!/usr/bin/env bash
set -euo pipefail

# Required: HF Dataset repo_id holding the ~1.45 GB of model artifacts.
# Set this in the Space's Settings → Variables and secrets.
: "${HF_DATASET_REPO:?Set HF_DATASET_REPO to e.g. <user>/nyc-restaurant-artifacts}"

# Optional overrides (defaults come from the Dockerfile's ENV):
#   ARTIFACTS_DIR         — where to materialize the dataset (default /home/user/data)
#   ALLOWED_ORIGIN_REGEX  — CORS regex for the Vercel frontend origin
: "${ARTIFACTS_DIR:=/home/user/data}"

echo "[entrypoint] pulling artifacts from $HF_DATASET_REPO → $ARTIFACTS_DIR"
python - <<'PY'
import os
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id=os.environ["HF_DATASET_REPO"],
    repo_type="dataset",
    local_dir=os.environ["ARTIFACTS_DIR"],
)
PY

echo "[entrypoint] starting uvicorn on :7860"
exec uvicorn app.backend.main:app --host 0.0.0.0 --port 7860
