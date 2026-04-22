"""
main.py — FastAPI entrypoint.

Run from the repo root (with .venv active) as:
    uvicorn app.backend.main:app --reload --port 8000

Or directly:
    python -m app.backend.main
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .browse  import get_all_points
from .detail  import get_detail, get_reviews
from .schemas import (
    BrowseResponse,
    RestaurantDetail,
    ReviewsPage,
    SearchRequest,
    SearchResponse,
)
from .search import do_search
from .state  import load_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all()
    yield


app = FastAPI(
    title="NYC Restaurant Recommendation API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # Vite dev server, same origin, CRA-ish — allow any localhost port during dev.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest):
    try:
        return do_search(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/restaurant/{gmap_id}", response_model=RestaurantDetail)
def restaurant_detail(gmap_id: str):
    d = get_detail(gmap_id)
    if d is None:
        raise HTTPException(status_code=404, detail="restaurant not found")
    return d


@app.get("/api/browse", response_model=BrowseResponse)
def browse_all():
    return get_all_points()


@app.get("/api/restaurant/{gmap_id}/reviews", response_model=ReviewsPage)
def restaurant_reviews(
    gmap_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    return get_reviews(gmap_id, page=page, page_size=page_size)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
