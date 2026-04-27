#!/usr/bin/env bash
# Sync the minimal backend into a local clone of the HF Space git repo.
#
# Usage:
#   deploy/hf-space/sync.sh <path-to-local-hf-space-clone>
#
# First time (one-time):
#   git clone https://huggingface.co/spaces/<user>/nyc-restaurant-api ~/hf-space-api
#   deploy/hf-space/sync.sh ~/hf-space-api
#   cd ~/hf-space-api && git add -A && git commit -m "initial deploy" && git push
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: $0 <path-to-local-hf-space-clone>" >&2
    exit 2
fi

SPACE_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ ! -d "$SPACE_DIR/.git" ]]; then
    echo "error: '$SPACE_DIR' is not a git repo." >&2
    echo "       Clone the Space first, e.g.:" >&2
    echo "         git clone https://huggingface.co/spaces/<user>/nyc-restaurant-api \"$SPACE_DIR\"" >&2
    exit 1
fi

echo "[sync] $REPO_ROOT  →  $SPACE_DIR"

# Space-root scaffold
cp "$SCRIPT_DIR/Dockerfile"    "$SPACE_DIR/Dockerfile"
cp "$SCRIPT_DIR/entrypoint.sh" "$SPACE_DIR/entrypoint.sh"
cp "$SCRIPT_DIR/README.md"     "$SPACE_DIR/README.md"
cp "$REPO_ROOT/app/backend/requirements.txt" "$SPACE_DIR/requirements.txt"

# Backend code (drop caches)
mkdir -p "$SPACE_DIR/app"
rsync -a --delete \
    --exclude='__pycache__' \
    --exclude='.DS_Store' \
    --exclude='*.pyc' \
    "$REPO_ROOT/app/backend/" "$SPACE_DIR/app/backend/"

# Minimal src/: only the four modules imported at runtime.
mkdir -p "$SPACE_DIR/src"
for f in absa.py ranking.py similarity.py 7_similarity.py; do
    cp "$REPO_ROOT/src/$f" "$SPACE_DIR/src/$f"
done
# Remove anything else that might have lingered from a previous sync.
find "$SPACE_DIR/src" -mindepth 1 -maxdepth 1 \
    ! -name 'absa.py' ! -name 'ranking.py' \
    ! -name 'similarity.py' ! -name '7_similarity.py' \
    -exec rm -rf {} +

echo "[sync] done. Review and push:"
echo "    cd \"$SPACE_DIR\" && git status"
echo "    git add -A && git commit -m 'sync from main repo' && git push"
