"""
similarity.py — importable wrapper around src/7_similarity.py.

7_similarity.py's filename starts with a digit, so Python's `from src.7_similarity
import X` syntax is a SyntaxError. This module uses importlib to load the real
implementation at runtime and re-exports its public API so the backend and
other callers can simply `from src.similarity import ...`.
"""
import importlib

_mod = importlib.import_module("src.7_similarity")

# Public API re-exports
MODEL_NAME                   = _mod.MODEL_NAME
VALID_ZIP_PREFIX             = _mod.VALID_ZIP_PREFIX
load_model                   = _mod.load_model
load_pca_model               = _mod.load_pca_model
load_embeddings_raw          = _mod.load_embeddings_raw
embed_query                  = _mod.embed_query
embed_query_pca              = _mod.embed_query_pca
find_best_cluster            = _mod.find_best_cluster
get_top_k_reviews            = _mod.get_top_k_reviews
aggregate_to_restaurants     = _mod.aggregate_to_restaurants
search                       = _mod.search
search_pca                   = _mod.search_pca
search_pca_within_clusters   = _mod.search_pca_within_clusters
has_valid_nyc_zip            = _mod.has_valid_nyc_zip
valid_nyc_gmap_ids           = _mod.valid_nyc_gmap_ids
