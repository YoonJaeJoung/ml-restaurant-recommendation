"""
embedding.py
Sentence embedding generation for reviews and queries using nomic-ai/nomic-embed-text-v1.5.
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import os

def load_and_embed_data(meta_path, review_path, output_dir, min_reviews=30, max_reviews=500):
    print("Loading model...")
    # Enable MPS (Apple Silicon GPU acceleration) for faster processing
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Load the embedding model
    model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True, device=device)
    
    # [Explanation on sequence truncation length]
    # 1 token is roughly 0.75 words.
    # Truncating to 256 tokens can fit a ~200-word short review.
    # Truncating to 512 tokens can fit a ~400-word long review.
    # For typical restaurant reviews, setting this to 256 or 512 is completely sufficient.
    # Here we cap it at 256 to ensure semantic meaning is captured while maximizing speed.
    model.max_seq_length = 256 
    
    print("Loading data...")
    meta_df = pd.read_parquet(meta_path)
    review_df = pd.read_parquet(review_path)
    
    print(f"Original data shape - Meta: {len(meta_df)}, Reviews: {len(review_df)}")

    # ========= Filtering: Remove restaurants with too few reviews =========
    if min_reviews is not None:
        print(f"Filtering: keeping only restaurants with > {min_reviews} reviews...")
        
        # 1. Count how many reviews each restaurant (gmap_id) has
        review_counts = review_df.groupby('gmap_id').size()
        
        # 2. Find eligible restaurants with > min_reviews counts
        valid_gmap_ids = review_counts[review_counts > min_reviews].index
        
        # 3. Filter the datasets to keep only these restaurants
        review_df = review_df[review_df['gmap_id'].isin(valid_gmap_ids)]
        meta_df = meta_df[meta_df['gmap_id'].isin(valid_gmap_ids)]
        
        print(f"Filtered data shape - Meta: {len(meta_df)}, Reviews: {len(review_df)}")
        
    # ========= Downsampling: Keep at most max_reviews per restaurant =========
    if max_reviews is not None:
        print(f"Downsampling: keeping maximum {max_reviews} reviews per restaurant...")
        # Group by gmap_id and keep only the top max_reviews rows per group
        review_df = review_df.groupby('gmap_id').head(max_reviews).reset_index(drop=True)
        print(f"Data shape after max limit - Reviews: {len(review_df)}")
    # ===============================================

    # Prepare metadata text
    # Combine name, category, and description as the metadata corpus
    print("Preparing metadata corpus...")
    # Combine relevant columns for metadata text embedding
    meta_df['text_to_embed'] = "search_document: " + meta_df['name'].fillna("") + " " + \
                               meta_df['category'].fillna("").astype(str) + " " + \
                               meta_df['description'].fillna("")
    
    meta_corpus = meta_df['text_to_embed'].tolist()
    
    print("Encoding metadata...")
    # Lab 3 Step 2: Text vectorization and normalization
    # Increased batch size (e.g. 32 to 64) is feasible when using sequence truncation and MPS acceleration
    meta_embeddings = model.encode(meta_corpus, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
    
    # Prepare review text
    print("Preparing review corpus...")
    review_df['text_to_embed'] = "search_document: " + review_df['text'].fillna("")
    review_corpus = review_df['text_to_embed'].tolist()
    
    print("Encoding reviews...")
    # Review dataset is large; use batch size 32 or 64 to speed up calculation on GPU/CPU
    review_embeddings = model.encode(review_corpus, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
    
    print("Saving embeddings...")
    os.makedirs(output_dir, exist_ok=True)
    
    np.save(os.path.join(output_dir, 'meta_embeddings.npy'), meta_embeddings)
    np.save(os.path.join(output_dir, 'review_embeddings.npy'), review_embeddings)
    
    print("Embeddings generated and saved successfully!")

if __name__ == "__main__":
    META_PATH = "./data/processed/meta-NYC-restaurant.parquet"
    REVIEW_PATH = "./data/processed/review-NYC-restaurant.parquet"
    OUTPUT_DIR = "./data/processed/"
    
    # Filter out restaurants with < 30 reviews, and keep at most 500 reviews per restaurant
    load_and_embed_data(META_PATH, REVIEW_PATH, OUTPUT_DIR, min_reviews=30, max_reviews=500)

