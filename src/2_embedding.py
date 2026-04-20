"""
embedding.py
Sentence embedding generation for reviews and queries using nomic-ai/nomic-embed-text-v1.5.

Reads the filtered review parquet produced by 1_data_processing.py.
Implements robust chunk-based memmap fault-tolerance allowing pausing and resuming.
"""

import pandas as pd
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import os

def load_and_embed_data(meta_path, review_path, output_dir):
    print("Loading model...")
    # Prioritize CUDA on Lightning AI, then MPS on Mac, then CPU
    import torch
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Using device: {device}")

    # Load the embedding model
    model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True, device=device)
    model.max_seq_length = 256

    print("Loading data...")
    meta_df = pd.read_parquet(meta_path)
    review_df = pd.read_parquet(review_path)

    print(f"Data shape - Meta: {len(meta_df)}, Reviews: {len(review_df)}")

    valid_gmap_ids = set(review_df["gmap_id"].unique())
    meta_df = meta_df[meta_df["gmap_id"].isin(valid_gmap_ids)].reset_index(drop=True)
    print(f"Meta after aligning to filtered reviews: {len(meta_df)}")

    if "text_for_embedding" not in review_df.columns:
        raise KeyError("review parquet is missing 'text_for_embedding' column.")

    print("Preparing metadata corpus...")
    meta_df['text_to_embed'] = "search_document: " + meta_df['name'].fillna("") + " " + \
                               meta_df['category'].fillna("").astype(str) + " " + \
                               meta_df['description'].fillna("")

    meta_corpus = meta_df['text_to_embed'].tolist()

    os.makedirs(output_dir, exist_ok=True)
    meta_out = os.path.join(output_dir, 'meta_embeddings.npy')
    
    if not os.path.exists(meta_out):
        print("Encoding metadata...")
        meta_embeddings = model.encode(meta_corpus, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
        np.save(meta_out, meta_embeddings)
        print(f"Saved {meta_out}")
    else:
        print(f"Metadata embeddings already exist at {meta_out}. Skipping.")

    print("Preparing review corpus (column: text_for_embedding)...")
    review_df['text_to_embed'] = "search_document: " + review_df['text_for_embedding'].fillna("")
    review_corpus = review_df['text_to_embed'].tolist()

    # --- CHUNKED RESUMABLE ENCODING ---
    n_reviews = len(review_corpus)
    dim = 768
    chunk_size = 50000 
    
    checkpoint_file = os.path.join(output_dir, "embedding_checkpoint.json")
    review_out_file = os.path.join(output_dir, "review_embeddings.npy")
    
    start_idx = 0
    if os.path.exists(checkpoint_file) and os.path.exists(review_out_file):
        try:
            with open(checkpoint_file, "r") as f:
                chk = json.load(f)
                start_idx = chk.get("last_processed_idx", 0)
        except Exception:
            start_idx = 0
            
    if start_idx < n_reviews:
        if start_idx == 0:
            print(f"Starting fresh review embedding run for {n_reviews} reviews...")
            memmap_arr = np.memmap(review_out_file, dtype='float32', mode='w+', shape=(n_reviews, dim))
        else:
            print(f"Resuming review embedding from index {start_idx} / {n_reviews}...")
            memmap_arr = np.memmap(review_out_file, dtype='float32', mode='r+', shape=(n_reviews, dim))
            
        print("Encoding reviews in chunks of 50,000...")
        for i in range(start_idx, n_reviews, chunk_size):
            end_idx = min(i + chunk_size, n_reviews)
            chunk_text = review_corpus[i:end_idx]
            
            print(f"Processing chunk {i:,} to {end_idx:,}...")
            chunk_emb = model.encode(chunk_text, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
            memmap_arr[i:end_idx] = chunk_emb
            memmap_arr.flush()
            
            with open(checkpoint_file, "w") as f:
                json.dump({"last_processed_idx": end_idx}, f)
        
        print("Embeddings generated and saved successfully!")
    else:
        print("Review embeddings are already fully encoded based on checkpoint!")

if __name__ == "__main__":
    META_PATH = "./data/processed/meta-NYC-restaurant.parquet"
    REVIEW_PATH = "./data/processed/review-NYC-restaurant-filtered.parquet"
    OUTPUT_DIR = "./data/processed/"

    load_and_embed_data(META_PATH, REVIEW_PATH, OUTPUT_DIR)
