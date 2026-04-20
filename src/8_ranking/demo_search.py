"""
demo_search.py
Standalone search + ranking demo.
Run: streamlit run src/8_ranking/demo_search.py
search --> visualize 4 aspects's weights and can manually adjust
--> recompute and show the ranks
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

from src.7_similarity import load_model, load_pca_model, search_pca_within_clusters
from src.absa import get_aspect_prefs
from src.8_ranking import rank_candidates, add_price_tier_score

# ── Paths ─────────────────────────────────────────────────────────────────────
REVIEWS_PATH   = "data/processed/review-NYC-restaurant-filtered.parquet"
META_PATH      = "data/processed/meta-NYC-restaurant.parquet"
EMB_PCA_PATH   = "data/processed/review_embeddings_pca.npy"
PCA_MODEL_PATH = "data/processed/pca_model.pkl"
CENTROIDS_PATH = "results/clustering/cluster_centroids.npy"
CLUSTERS_PATH  = "results/clustering/restaurant_clusters.csv"
SCORES_PATH    = "data/processed/aspect_scores.parquet"

st.set_page_config(page_title="NYC Restaurant Search Demo", layout="wide")

# ── Load heavy resources once ─────────────────────────────────────────────────
@st.cache_resource
def load_resources():
    model          = load_model()
    pca            = load_pca_model(PCA_MODEL_PATH)
    embeddings_pca = np.load(EMB_PCA_PATH, mmap_mode='r')
    centroids      = np.load(CENTROIDS_PATH)
    return model, pca, embeddings_pca, centroids

@st.cache_data
def load_data():
    reviews_df    = pd.read_parquet(REVIEWS_PATH)
    meta_df       = pd.read_parquet(META_PATH)
    clusters_df   = pd.read_csv(CLUSTERS_PATH)
    aspect_scores = pd.read_parquet(SCORES_PATH)
    num_reviews   = reviews_df.groupby("gmap_id").size().rename("num_reviews").reset_index()
    return reviews_df, meta_df, clusters_df, aspect_scores, num_reviews

# ── Page ──────────────────────────────────────────────────────────────────────
st.title("🍕 NYC Restaurant Search Demo")
st.caption("Enter a query → review detected aspect preferences → adjust if needed → see ranked results.")

with st.spinner("Loading model and data (first run only)…"):
    model, pca, embeddings_pca, centroids = load_resources()
    reviews_df, meta_df, clusters_df, aspect_scores, num_reviews = load_data()

# ── Search bar ────────────────────────────────────────────────────────────────
col_input, col_btn, col_n = st.columns([5, 1, 1])
with col_input:
    query = st.text_input("Search query", placeholder="e.g. cheap ramen no long wait")
with col_btn:
    st.write("")
    search_clicked = st.button("Search", type="primary", use_container_width=True)
with col_n:
    top_n = st.number_input("Top N", min_value=5, max_value=50, value=10, step=5)

# ── On search: run semantic search and reset slider values to detected prefs ──
# Fix 1: write slider keys into session_state BEFORE sliders are rendered,
# so each new search resets them to auto-detected values even if user had
# manually adjusted them before.
if search_clicked and query.strip():
    with st.spinner(f'Searching for "{query}"…'):
        candidates = search_pca_within_clusters(
            query, model, pca, embeddings_pca,
            reviews_df, meta_df, centroids, clusters_df,
            top_n=100, top_n_clusters=5, k=500
        )
        candidates = candidates.merge(num_reviews, on="gmap_id", how="left").fillna({"num_reviews": 0})
        candidates = add_price_tier_score(candidates, meta_df)
        st.session_state["candidates"]   = candidates
        st.session_state["query"]        = query
        detected = get_aspect_prefs(query)
        st.session_state["prefs"]        = detected
        # Reset all sliders to detected values on every new search
        st.session_state["sl_food"]      = float(round(detected["food"],      2))
        st.session_state["sl_service"]   = float(round(detected["service"],   2))
        st.session_state["sl_price"]     = float(round(detected["price"],     2))
        st.session_state["sl_wait"]      = float(round(detected["wait_time"], 2))
        st.session_state["sl_alpha"]     = 0.4
        st.session_state["sl_beta"]      = 0.5
        st.session_state["sl_gamma"]     = 0.1

if "candidates" not in st.session_state:
    st.info("Enter a query above and click Search to get started.")
    st.stop()

candidates   = st.session_state["candidates"]
stored_query = st.session_state["query"]
init         = st.session_state["prefs"]

# ── Aspect preference sliders ─────────────────────────────────────────────────
st.divider()
st.subheader("🎛️ Aspect Preferences")
st.caption(
    f"Auto-detected from **\"{stored_query}\"**. "
    "Drag sliders to override — results update instantly without re-searching."
)

# Initialize keys on very first load (before any search)
for key, asp in [("sl_food","food"),("sl_service","service"),
                 ("sl_price","price"),("sl_wait","wait_time")]:
    if key not in st.session_state:
        st.session_state[key] = float(round(init[asp], 2))

c1, c2, c3, c4 = st.columns(4)
with c1:
    w_food    = st.slider("🍜 Food",      0.0, 1.0, step=0.05, key="sl_food")
with c2:
    w_service = st.slider("🤝 Service",   0.0, 1.0, step=0.05, key="sl_service")
with c3:
    w_price   = st.slider("💰 Price",     0.0, 1.0, step=0.05, key="sl_price")
with c4:
    w_wait    = st.slider("⏱️ Wait time", 0.0, 1.0, step=0.05, key="sl_wait")

total_w = w_food + w_service + w_price + w_wait
if total_w == 0:
    st.warning("All weights are 0 — set at least one above 0.")
    st.stop()

# Fix 2: auto-normalize, no manual warning needed
user_pref = {
    "food":      w_food     / total_w,
    "service":   w_service  / total_w,
    "price":     w_price    / total_w,
    "wait_time": w_wait     / total_w,
}

st.caption(
    f"Normalized → "
    f"food **{user_pref['food']:.2f}** · "
    f"service **{user_pref['service']:.2f}** · "
    f"price **{user_pref['price']:.2f}** · "
    f"wait **{user_pref['wait_time']:.2f}**"
)

# ── Ranking formula hyper-parameters (α / β / γ, auto-normalized) ─────────────
with st.expander("⚙️ Ranking weights (α / β / γ)", expanded=False):
    st.caption("final_score = α·avg_rating + β·aspect_weighted + γ·log(1+num_reviews) — auto-normalized")
    ca, cb, cg = st.columns(3)
    with ca: alpha_raw = st.slider("α  avg_rating",   0.0, 1.0, 0.4, 0.1, key="sl_alpha")
    with cb: beta_raw  = st.slider("β  aspect score", 0.0, 1.0, 0.5, 0.1, key="sl_beta")
    with cg: gamma_raw = st.slider("γ  review count", 0.0, 1.0, 0.1, 0.1, key="sl_gamma")
    abg_total = alpha_raw + beta_raw + gamma_raw
    # Fix 2: auto-normalize α/β/γ, show result instead of warning
    if abg_total == 0:
        alpha, beta, gamma = 0.4, 0.5, 0.1
    else:
        alpha = alpha_raw / abg_total
        beta  = beta_raw  / abg_total
        gamma = gamma_raw / abg_total
    st.caption(f"Normalized → α **{alpha:.2f}** · β **{beta:.2f}** · γ **{gamma:.2f}**")

# ── Re-rank ───────────────────────────────────────────────────────────────────
ranked = rank_candidates(candidates, aspect_scores, user_pref, alpha, beta, gamma)
# Fix 3: rank starts from 1
top = ranked.head(top_n).reset_index(drop=True)
top.index = top.index + 1

# ── Results ───────────────────────────────────────────────────────────────────
st.divider()
st.subheader(f"📍 Top {top_n} Results for \"{stored_query}\"")

map_col, list_col = st.columns([2, 1])

with map_col:
    fig = px.scatter_map(
        top,
        lat="latitude", lon="longitude",
        hover_name="name",
        hover_data={"avg_rating": True, "borough": True,
                    "latitude": False, "longitude": False},
        color_discrete_sequence=["#e63946"],
        zoom=11, height=520,
    )
    fig.update_layout(map_style="carto-positron",
                      margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, width='stretch', config={"scrollZoom": True})

with list_col:
    # Fix 4: rename avg_rating to "Rating(1-5)" to make meaning clear
    # Attach the raw price tier symbol for display ($ / $$ / etc.)
    price_tier_display = meta_df[["gmap_id", "price"]].rename(columns={"price": "tier"})
    top_display = top.merge(price_tier_display, on="gmap_id", how="left")
    top_display["tier"] = top_display["tier"].fillna("?")

    display_cols = ["name", "borough", "avg_rating", "tier",
                    "food", "service", "price", "wait_time", "final_score"]
    available = [c for c in display_cols if c in top_display.columns]
    st.dataframe(
        top_display[available].rename(columns={
            "avg_rating":  "Rating(1-5)",
            "final_score": "score",
            "wait_time":   "wait",
            "tier":        "$$",
        }).style.format({
            "Rating(1-5)": "{:.1f}", "score": "{:.3f}",
            "food": "{:.2f}", "service": "{:.2f}",
            "price": "{:.2f}", "wait": "{:.2f}",
        }),
        height=520, width='stretch'
    )
