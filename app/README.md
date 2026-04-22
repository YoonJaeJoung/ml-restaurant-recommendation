# App — FastAPI backend + Vite/React SPA

The production UI for the Noble Jaguars restaurant recommender. Natural-language
search over 19.5k NYC restaurants and 2.1M Google reviews, with an interactive
Mapbox map, aspect-based sentiment, client-side sort, and an inline detail panel.

Top-level project context (ML pipeline, data processing, embeddings, clustering,
ABSA, ranking) lives in the root [`README.md`](../README.md). This document is
scoped to what's inside `app/`.

---

## Architecture

```
┌───────────────────┐   /api/*     ┌─────────────────────────────────┐
│  Vite dev server  │──────────── →│  FastAPI (uvicorn, port 8000)   │
│  (port 5173)      │              │                                 │
│  React SPA        │←──── JSON ───│  ┌── imports ─────────────┐     │
└───────────────────┘              │  │ src/absa.py            │     │
         │                         │  │ src/similarity.py      │     │
         │ tiles                   │  │ src/ranking.py         │     │
         ▼                         │  └────────────────────────┘     │
┌───────────────────┐              │                                 │
│   Mapbox CDN      │              │  loads on startup: model,       │
│   (Streets v12)   │              │  PCA, embeddings memmap,        │
└───────────────────┘              │  meta parquet (with aspect_*),  │
                                   │  centroids, cluster summary     │
                                   └─────────────────────────────────┘
```

The backend imports the stable library code from `src/` (`absa.py`,
`similarity.py`, `ranking.py`) directly. It does **not** shell out to the
numbered CLI scripts — those remain for offline / regression work.

---

## Backend — `app/backend/`

All modules share a single in-process singleton, `STATE` (a dataclass in
`state.py`), which is populated once at FastAPI startup via the `lifespan`
context manager in `main.py`.

| File | Responsibility |
|---|---|
| `main.py` | FastAPI app factory, lifespan loader, CORS regex for any localhost port, route registrations. |
| `state.py` | `AppState` dataclass + `load_all()` loader. Memmap's the 128-dim PCA review embeddings (~1 GB on disk, zero-copy), loads `review-NYC-restaurant-filtered.parquet` (gmap_id column for retrieval; full rows for the detail endpoint), `meta-NYC-restaurant.parquet` (asserts the 4 `aspect_*` columns exist), cluster centroids + assignments, and the cluster summary JSON. Caches `log_reviews_max` for the ranker. |
| `schemas.py` | Pydantic v2 models: `LocationFilter` (5 modes: `all` / `borough` / `radius` / `bbox` / `polygon`), `TimeFilter` (`at` + `any_time`; the field is deliberately named `at` — see note below), `ToggleSelection`, `SearchRequest`/`Response`, `RestaurantSummary` (includes `aspect_food/service/price/price_blended/wait_time` so the sidebar can sort client-side), `RestaurantDetail`, `ReviewsPage`, `BrowseResponse`. |
| `search.py` | End-to-end search orchestration. `do_search(req)` composes the query → `get_aspect_prefs` → `search_pca_within_clusters` → NYC-ZIP filter → `filter_by_location` → `is_open_at` → `rank_candidates` → `_summary_rows`. Constants `TOP_N_CLUSTERS=5`, `K_REVIEWS_PER_SEARCH=500`, `RETRIEVAL_POOL=500`. |
| `detail.py` | `get_detail(gmap_id)` → `RestaurantDetail`. Applies the same 50/50 price blend from `src.ranking`. `get_reviews(gmap_id, page, page_size)` paginates reviews, sorts photos-first then recency-desc, and renders the **English-only** text from `text_for_embedding` (stripped of `(Translated by Google)` / `(Original)` blocks by the data-processing step). |
| `browse.py` | `GET /api/browse`. Returns every restaurant that passes three gates: (1) has lat/lon, (2) has a valid NYC ZIP, (3) appears in the filtered reviews parquet (⇒ ≥15 English reviews, no Chinese-only noise). ~19.4k points; same universe the search engine ranks over. |
| `geo.py` | `filter_by_location(meta, loc)`: vectorised haversine for `radius`, bbox membership for `bbox`, Shapely `Polygon.contains` for `polygon`, `isin` for `borough`. |
| `hours.py` | `is_open_at(hours_info, visit)` → `True / False / None`. Parses the legacy Google hour strings (`Monday11AM–10PM`, handles overnight ranges). `None` means "unknown" and is kept by the search filter (err on inclusion). |
| `query_builder.py` | Pure function `build_query(toggles, free_text)` mirroring `src/10_query_construction.py`. Order: cuisine → vibe → occasion → priority, with free text prepended when supplied. |
| `requirements.txt` | FastAPI, uvicorn[standard], shapely, pydantic. Install into the **project** venv (not a separate app venv). |

### Search request lifecycle

```
POST /api/search body
  │
  ├── build_query(toggles, free_text)               → single query string
  ├── get_aspect_prefs(query)                       → weights per aspect
  │
  ├── search_pca_within_clusters(query, …)          → top 500 restaurants
  │     ├── PCA-embed the query
  │     ├── cosine vs 50 cluster centroids → pick top 5 clusters
  │     ├── cosine over 500 reviews inside those clusters
  │     └── aggregate reviews → restaurants
  │
  ├── filter: has_valid_nyc_zip(address)            → trims non-NYC leakage
  ├── filter_by_location(meta, req.location)        → borough/radius/bbox/polygon
  ├── is_open_at(row.hours, req.time.at)            → drops definitively-closed
  │
  ├── rank_candidates(candidates, meta, prefs, α, β, γ, log_reviews_max)
  │     final = α · rating/5 + β · Σ wᵢ·aspectᵢ + γ · log1p(reviews)/global_max
  │     (price aspect is blended 50/50 with the $/$$/$$$ tier here)
  │
  └── _summary_rows(ranked_df, limit=30)            → RestaurantSummary[]
        (joins aspect_* columns from meta so the client can sort on them)
```

### Note — why `TimeFilter.at` instead of `datetime`

Pydantic resolves annotations against enclosing scope. A field named `datetime`
with annotation `Optional[datetime]` makes Pydantic look up the field-name
against the already-defined field and infer `Optional[<self>]`, which accepts
only `None` — every real value 422s with `none_required`. Renaming the field to
`at` (and updating the frontend payload to match) fixed it.

### API

| Endpoint | Description |
|---|---|
| `GET /api/health` | Liveness. |
| `POST /api/search` | Request: `{query, toggles, location: {mode, …}, time: {at?, any_time}, limit=30}`. Response: ranked summaries + matched clusters + timing + `aspect_*` per result. |
| `GET /api/browse` | All NYC restaurants that qualified through the data pipeline. ~19.4k points; used by the clustered browse-all map. |
| `GET /api/restaurant/{gmap_id}` | Full detail, including blended price, `state` (Google's live open/closed status), `misc`, category, hours. |
| `GET /api/restaurant/{gmap_id}/reviews?page=&page_size=` | Paginated reviews. Returns the English `text_for_embedding` (falls back to raw `text` if missing). Photo URLs flattened. Photos-first then recency-desc. |

---

## Frontend — `app/frontend/src/`

Vite + React 19. No Redux / zustand — state lives in `App.jsx` (`searchState`
+ view state) and drills down. Views are pure render; components encapsulate
interaction.

### Top-level

| File | Role |
|---|---|
| `App.jsx` | View router (`home` / `results` / `browse` / `detail`) and **topbar** renderer (brand pill on home, ← Home button elsewhere, query-pill in the center of Results, ? on the right). Owns `searchState`, `runSearch`, `resetDefaults`. Hosts the Results filter drop-down under the topbar. |
| `main.jsx` | ReactDOM bootstrap. |
| `index.css` | Design tokens: Eater red `#E31919`, radius 6 / 8, text `#0F0F0F`, shadow scale. |
| `app.css` | All layout + component styles. Media queries at ≤820 px (bottom-sheet sidebar) and ≤420 px (brand shrink). |
| `vite.config.js` | Proxies `/api/*` → `http://127.0.0.1:8000`. |

### Views

| File | Role |
|---|---|
| `views/Home.jsx` | Landing page. Title + subtitle, collapsible filter accordion (defaults `All NYC · Today · now`), query box with the live `✨ Need inspiration?` expansion, **Browse all restaurants** (outlined) + **Search** (filled) CTA row. |
| `views/Results.jsx` | Sidebar (sticky header with meta + **Sort by…** row: Overall / Google / Food / Service / Wait / Price, re-sorts client-side) + full-bleed Mapbox map underneath + inline right-side Detail panel on desktop. No sidebar head; the toolbar moved into the app-level topbar. |
| `views/BrowseAll.jsx` | Full-screen clustered map of every qualifying restaurant (`leaflet.markercluster`). Clicking a pin opens the full-page `Detail` variant. |
| `views/Detail.jsx` | Works as both a full `page` and an inline `panel` variant. Sticky header (name, meta, Google Maps link, tab bar). Three tabs: **Score** (Overall as %, Food/Service/Price/Wait as X.X/10 with icons), **Detail** (Status, Description, Category, weekday×hours table, MISC — null → `-`), **Reviews** (paginated, 8/page, photos-first). |

### Components

| File | Role |
|---|---|
| `components/MapView.jsx` | `react-leaflet` + Mapbox raster tiles + `leaflet-draw` (polygon **and** rectangle) + `leaflet.markercluster`. Teardrop result pins (top-5 numbered). Custom `drawTrigger` to drive draw tools from our own buttons instead of the stock leaflet-draw toolbar (which is CSS-hidden). `MapRefExposer` exposes the map imperatively for `zoomIn/zoomOut/getBounds`. |
| `components/MapInline.jsx` | 320-px map embedded inside the filter body. Two modes: `nearby` (pin + radius + `Current Location` button — the *only* code path that triggers geolocation) or `area` (overlay buttons: `Use current viewport` / `Draw Polygon` / `Draw Rectangle` → collapse to `Clear Selection` once a shape exists). Custom horizontal +/- zoom widget above the hint box. |
| `components/LocationControls.jsx` | 3-tab segmented control (flex:1 each): Select Borough / Search nearby / Select area from map. |
| `components/BoroughSelector.jsx` | Multi-select chips + All NYC toggle. Selecting a borough deselects All NYC, clicking All NYC clears boroughs. No disabled state. |
| `components/DayTimePicker.jsx` | `DAY` row: Today / Tomorrow / Select day (reveals a Mon–Sun row) / Any time. `TIME` row: Breakfast (9AM) / Lunch (12PM) / Dinner (6PM) / Custom (reveals a `<input type="time">` styled like a weekday chip). |
| `components/FilterPanel.jsx` | Shared wrapper around `DayTimePicker` + `LocationControls`. Used by both the Home filter accordion and the Results topbar drop-down. |
| `components/InspireBuilder.jsx` | 4-question chip grid (cuisine / vibe / occasion / priority). Live-updates the query field via `buildQueryFromToggles` as chips toggle. Cancel restores the prior query; Search commits + triggers search. |
| `components/ResultCard.jsx` | Hoverable, selectable ranked row. `selected` state uses a full 2-px accent outline (not a left stripe). |
| `components/Icons.jsx` | Zero-dependency inline SVG icon components (Lucide-port). Exports `IconStar` / `Utensils` / `Service` (smile face) / `Clock` / `Dollar` / `Target` / `ArrowLeft` / `Github` / `Plus` / `Minus` / `Locate` / `Polygon` / `Rectangle` / `Viewport` / `Close` / `Search` / `Chevron*`. |
| `components/HelpModal.jsx` | Full pipeline math: embeddings → PCA → clustering → ABSA → ranking. |
| `components/AboutModal.jsx` | Team + project blurb + outlined GitHub button. Opens on clicking the Noble Jaguars pill on Home. |
| `components/Spinner.jsx` | Full-overlay spinner for Results-page loading; `SpinnerInline` for CTA buttons. |

### Hooks / lib / api

| File | Role |
|---|---|
| `hooks/useGeolocation.js` | `useGeolocation(enabled)` — gated by the `enabled` flag. Times Square fallback if the permission is denied or times out. No longer called on page mount or tab switch — only from the `Current Location` button in `MapInline`. |
| `lib/queryBuilder.js` | `buildQueryFromToggles(t)` — client-side mirror of `src/10_query_construction.py` / `backend/query_builder.py`. Drives the live auto-fill in `InspireBuilder`. |
| `api/client.js` | Tiny `fetch` wrapper. `api.search / detail / reviews / browse / health`. Formats Pydantic 422 arrays into human-readable `field: msg; …` strings (not `[object Object]`). |

### Design system

- **Accent**: high-contrast Eater red `#E31919` (lift `#BD0F0F`, bg `rgba(227,25,25,0.08/0.16)`).
- **Text**: `#0F0F0F` body; `#2a2826` muted-strong.
- **Radius**: `--radius: 6px` (buttons, inputs, cards) and `--radius-lg: 8px` (panels, modals, sidebar, detail panel). Pills/chips are fully rounded (`999px`). **No intermediate radii.**
- **Shadows**: `--shadow-sm / md / lg` tokens (`0 1px 2px` / `0 4px 10px` / `0 8px 24px` rgba black).
- **Type**: Inter + JetBrains Mono; mono labels use 10–11 px with 1.6–2.2 px letter-spacing, all-caps.
- **Map pins**: red teardrops for ranked results (top-5 numbered), small red teardrops for the browse clusters.

### Responsive behaviour

- **≥821 px** — floating 380-px rounded-rectangle sidebar on the left, 480-px detail panel on the right, full-bleed map behind.
- **≤820 px** — sidebar becomes a draggable bottom sheet; detail takes over the full screen; filter body compresses; map panels slide from the bottom.

---

## Environment

Create `app/frontend/.env.local` (gitignored via the `*.local` pattern in
`app/frontend/.gitignore`) with:

```
VITE_MAPBOX_TOKEN=pk.eyJ1...your_token_here
```

The token is read at build time by `MapView.jsx`. If absent, the app falls
back to Carto Voyager OSM tiles so it still works without a token.

## Run

Both ends run against the **project venv** for Python and the **frontend
`node_modules`** for React.

**Terminal A — backend** (run from repo root, venv active):

```bash
source .venv/bin/activate
uv pip install fastapi 'uvicorn[standard]' shapely pydantic   # one-time
uvicorn app.backend.main:app --host 127.0.0.1 --port 8000
```

Wait for `[state] ready — N meta rows, M reviews, log_reviews_max=…` in the
log. First boot takes ~60 s to load the model + memmap the 128-dim
embeddings.

**Terminal B — frontend**:

```bash
cd app/frontend
npm install        # one-time
npm run dev
```

Visit **http://localhost:5173**. Vite proxies `/api/*` to the backend, so no
CORS config is needed for local dev.

## Stopping

```bash
lsof -ti tcp:8000 tcp:5173 | xargs kill
```

## Prerequisites

Artifacts produced by the offline pipeline must exist:

- `data/processed/review-NYC-restaurant-filtered.parquet`
- `data/processed/meta-NYC-restaurant.parquet` (with `aspect_*` columns — run `python src/8_ranking.py` to populate)
- `results/pca/review_embeddings_pca.npy`, `results/pca/pca_model.pkl`
- `results/clustering/cluster_centroids.npy`, `results/clustering/restaurant_clusters.csv`, `results/clustering/evaluation/cluster_summary.json`

See the top-level [`README.md`](../README.md) for the end-to-end pipeline that
produces these.

## Smoke test

```bash
curl -s http://127.0.0.1:8000/api/health
curl -s -X POST http://127.0.0.1:8000/api/search -H 'Content-Type: application/json' \
  -d '{"query":"ramen","location":{"mode":"all"},"time":{"any_time":true},"limit":3}' \
  | python -c "import sys,json; r=json.load(sys.stdin)['results'][0]; print({k:r[k] for k in ['name','final_score','aspect_food','aspect_service','aspect_price_blended','aspect_wait_time']})"
```

Expected: the first result is a ramen place and all five aspect fields are
floats in `[0, 1]`.
