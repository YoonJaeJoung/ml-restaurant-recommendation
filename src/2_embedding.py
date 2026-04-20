"""
embedding.py
Sentence embedding generation for reviews and queries using nomic-ai/nomic-embed-text-v1.5.

Reads the filtered review parquet produced by 1_data_processing.py, which already
has the 30-500 review count rule applied and a `text_for_embedding` column that
contains the English portion of Google-translated reviews (or the original text
when the review was already in English).
"""

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import os

def load_and_embed_data(meta_path, review_path, output_dir):
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

    print(f"Data shape - Meta: {len(meta_df)}, Reviews: {len(review_df)}")

    # Reviews are already filtered by 1_data_processing.py. Align meta rows to
    # the surviving gmap_ids so meta_embeddings.npy matches the filtered set.
    valid_gmap_ids = set(review_df["gmap_id"].unique())
    meta_df = meta_df[meta_df["gmap_id"].isin(valid_gmap_ids)].reset_index(drop=True)
    print(f"Meta after aligning to filtered reviews: {len(meta_df)}")

    # Guard: the filtered parquet must carry text_for_embedding (English-only text).
    if "text_for_embedding" not in review_df.columns:
        raise KeyError(
            "review parquet is missing 'text_for_embedding' column. "
            "Run src/1_data_processing.py first to regenerate the filtered parquet."
        )

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

    # Prepare review text — uses the English-only column populated in step 2
    print("Preparing review corpus (column: text_for_embedding)...")
    review_df['text_to_embed'] = "search_document: " + review_df['text_for_embedding'].fillna("")
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
    REVIEW_PATH = "./data/processed/review-NYC-restaurant-filtered.parquet"
    OUTPUT_DIR = "./data/processed/"

    load_and_embed_data(META_PATH, REVIEW_PATH, OUTPUT_DIR)
