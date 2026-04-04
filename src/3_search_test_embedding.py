import os
import tempfile
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Load the embedding model (same one Yiduo used)
MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"

def load_model():
  """Load the sentence embedding model."""
  model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
  return model

def embed_query(query: str, model: SentenceTransformer) -> np.ndarray:
  """
  Embed a user's search query into a vector.
  Note: queries use 'search_query' prefix (asymmetric search).
  """
  prefixed = f"search_query: {query}"
  embedding = model.encode([prefixed], convert_to_numpy=True)
  return embedding  # shape: (1, 768)

def load_embeddings(embeddings_path: str) -> np.ndarray:
  """Load precomputed review embeddings from a .npy file using memory mapping."""
  return np.load(embeddings_path, mmap_mode='r')

def get_top_k_reviews(
  query_embedding: np.ndarray,
  review_embeddings: np.ndarray,
  reviews_df: pd.DataFrame,
  k: int = 50,
  chunk_size: int = 50000
) -> pd.DataFrame:
  """
  Find the top-k most similar reviews to a query embedding.
  Stores intermediate similarity scores on disk to save RAM.
  Returns a dataframe of the top reviews with their similarity scores.
  """
  n_reviews = review_embeddings.shape[0]
  
  # Create a temporary file to store the scores
  fd, temp_path = tempfile.mkstemp(suffix='.dat')
  os.close(fd)
  
  try:
    scores_memmap = np.memmap(temp_path, dtype='float32', mode='w+', shape=(n_reviews,))
    
    # Process in chunks
    for i in range(0, n_reviews, chunk_size):
      end_idx = min(i + chunk_size, n_reviews)
      chunk = review_embeddings[i:end_idx]
      scores_memmap[i:end_idx] = cosine_similarity(query_embedding, chunk)[0]
      
    scores_memmap.flush()
    
    k_actual = min(k, n_reviews)
    if k_actual < n_reviews:
      top_indices = np.argpartition(scores_memmap, -k_actual)[-k_actual:]
      top_indices = top_indices[np.argsort(scores_memmap[top_indices])[::-1]]
    else:
      top_indices = np.argsort(scores_memmap)[::-1]
      
    top_reviews = reviews_df.iloc[top_indices].copy()
    top_reviews["similarity_score"] = scores_memmap[top_indices]
    
  finally:
    # Explicitly clear reference before removing file
    del scores_memmap
    if os.path.exists(temp_path):
      os.remove(temp_path)
      
  return top_reviews

def aggregate_to_restaurants(
  top_reviews: pd.DataFrame,
  meta_df: pd.DataFrame,
  top_n: int = 10
) -> pd.DataFrame:
  """
  Aggregate review-level scores up to restaurant level.
  Returns top_n restaurants ranked by average similarity score.
  """
  restaurant_scores = (
    top_reviews.groupby("gmap_id")["similarity_score"]
    .mean()
    .reset_index()
    .rename(columns={"similarity_score": "avg_similarity"})
  )
  results = restaurant_scores.merge(meta_df, on="gmap_id", how="left")
  results = results.sort_values("avg_similarity", ascending=False).head(top_n)
  return results[["name", "avg_similarity", "avg_rating", "borough", "latitude", "longitude", "gmap_id"]]

def search(
  query: str,
  model: SentenceTransformer,
  review_embeddings: np.ndarray,
  reviews_df: pd.DataFrame,
  meta_df: pd.DataFrame,
  k: int = 50,
  top_n: int = 10
) -> pd.DataFrame:
  """
  Main search function. Takes a natural language query and returns
  top_n recommended restaurants.
  """
  query_embedding = embed_query(query, model)
  top_reviews = get_top_k_reviews(query_embedding, review_embeddings, reviews_df, k=k)
  results = aggregate_to_restaurants(top_reviews, meta_df, top_n=top_n)
  return results


print('loading data...')
reviews = pd.read_parquet('data/processed/review-NYC-restaurant-filtered.parquet')
meta = pd.read_parquet('data/processed/meta-NYC-restaurant.parquet')
embeddings = np.load('data/processed/review_embeddings.npy', mmap_mode='r')

print('loading model...')
model = load_model()

print('searching...')
results = search('cozy italian restaurant for a date night', model, embeddings, reviews, meta)
print(results)