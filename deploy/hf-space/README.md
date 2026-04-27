---
title: NYC Restaurant Recommendation API
emoji: 🍜
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# NYC Restaurant Recommendation — Backend API

FastAPI backend for the ML-based NYC restaurant recommender. The frontend
(Vite + React) is hosted separately on Vercel and calls this Space over HTTPS.

## Runtime configuration

Set these under **Settings → Variables and secrets** in the Space UI.

| Variable | Required | Example | Purpose |
|---|---|---|---|
| `HF_DATASET_REPO` | yes | `andrew-joung/nyc-restaurant-artifacts` | HF Dataset repo holding the ~1.45 GB of PCA embeddings + parquets. Pulled at container start. |
| `ALLOWED_ORIGIN_REGEX` | yes (for prod) | `https://.*\.vercel\.app` | CORS regex matched against the browser `Origin` header. Without it, only localhost works. |
| `ARTIFACTS_DIR` | no | `/home/user/data` | Where the dataset is materialized. Default is fine. |

## Endpoints

- `GET  /api/health`
- `POST /api/search`
- `GET  /api/restaurant/{gmap_id}`
- `GET  /api/restaurant/{gmap_id}/reviews?page=&page_size=`
- `GET  /api/browse`

## Build / deploy

Code is synced from the main GitHub project via `deploy/hf-space/sync.sh` in
that repo. Do not edit files here directly — changes will be overwritten on
the next sync.
