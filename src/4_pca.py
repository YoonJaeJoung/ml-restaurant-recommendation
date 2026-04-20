"""
4_pca.py
Dimensionality reduction of review and metadata embeddings via Incremental PCA.

Reads the merged 768-dimensional embedding vectors produced by 2_embedding.py,
fits IncrementalPCA in chunks to limit RAM usage, and saves the reduced-dimension
vectors robustly using memmap and JSON checkpoints to allow safe pause/resume.

Output files (saved to data/processed/):
  - review_embeddings_pca.npy   : PCA-reduced review embeddings  (N, n_components)
  - meta_embeddings_pca.npy     : PCA-reduced metadata embeddings (M, n_components)
  - pca_model.pkl               : Fitted sklearn PCA object (for projecting queries)
"""

import os
import json
import numpy as np
import joblib
from sklearn.decomposition import IncrementalPCA

# --------------- Configuration ---------------
INPUT_DIR = "./data/processed"
OUTPUT_DIR = "./data/processed"
N_COMPONENTS = 128          
CHUNK_SIZE = 100_000        
# ------------------------------------------------

def fit_pca_incremental(embeddings: np.ndarray, n_components: int, chunk_size: int, model_out: str, checkpoint_out: str) -> IncrementalPCA:
    n = embeddings.shape[0]
    
    start_idx = 0
    if os.path.exists(checkpoint_out) and os.path.exists(model_out):
        try:
            with open(checkpoint_out, "r") as f:
                chk = json.load(f)
                start_idx = chk.get("last_fit_idx", 0)
            pca = joblib.load(model_out)
        except Exception:
            start_idx = 0
            pca = IncrementalPCA(n_components=n_components)
    else:
        pca = IncrementalPCA(n_components=n_components)
        
    if start_idx < n:
        print(f"Fitting IncrementalPCA (n_components={n_components}) from index {start_idx:,} ...")
        for i in range(start_idx, n, chunk_size):
            end_idx = min(i + chunk_size, n)
            chunk = embeddings[i:end_idx]
            pca.partial_fit(chunk)
            print(f"  Fitted {end_idx:,} / {n:,} rows")
            
            joblib.dump(pca, model_out)
            with open(checkpoint_out, "w") as f:
                json.dump({"last_fit_idx": end_idx}, f)
    else:
        print("IncrementalPCA is already fully fitted based on checkpoint.")
        
    explained = pca.explained_variance_ratio_.sum() * 100
    print(f"  → Explained variance retained: {explained:.2f}%")
    return pca

def transform_chunked_resume(pca: IncrementalPCA, embeddings: np.ndarray, chunk_size: int, output_path: str, checkpoint_out: str):
    n = embeddings.shape[0]
    
    start_idx = 0
    if os.path.exists(checkpoint_out) and os.path.exists(output_path):
        try:
            with open(checkpoint_out, "r") as f:
                chk = json.load(f)
                start_idx = chk.get("last_transform_idx", 0)
        except Exception:
            start_idx = 0
            
    if start_idx == 0:
        print(f"Starting fresh projection to {output_path}...")
        out = np.memmap(output_path, dtype='float32', mode='w+', shape=(n, pca.n_components))
    else:
        print(f"Resuming projection from index {start_idx:,} ...")
        out = np.memmap(output_path, dtype='float32', mode='r+', shape=(n, pca.n_components))
        
    if start_idx < n:
        for i in range(start_idx, n, chunk_size):
            end_idx = min(i + chunk_size, n)
            chunk = embeddings[i:end_idx]
            out[i:end_idx] = pca.transform(chunk).astype(np.float32)
            out.flush()
            print(f"  Transformed {end_idx:,} / {n:,} rows")
            
            with open(checkpoint_out, "w") as f:
                json.dump({"last_transform_idx": end_idx}, f)
    else:
        print("Transformation already complete based on checkpoint.")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    review_emb_path = os.path.join(INPUT_DIR, "review_embeddings.npy")
    meta_emb_path = os.path.join(INPUT_DIR, "meta_embeddings.npy")

    print("Loading review embeddings (mmap) ...")
    review_embeddings = np.load(review_emb_path, mmap_mode="r")
    print(f"  Review embeddings shape: {review_embeddings.shape}")

    print("Loading meta embeddings ...")
    meta_embeddings = np.load(meta_emb_path)
    print(f"  Meta embeddings shape:   {meta_embeddings.shape}")

    model_out = os.path.join(OUTPUT_DIR, "pca_model.pkl")
    fit_checkpoint = os.path.join(OUTPUT_DIR, "pca_fit_checkpoint.json")
    
    # --- Fit PCA incrementally ---
    pca = fit_pca_incremental(review_embeddings, N_COMPONENTS, CHUNK_SIZE, model_out, fit_checkpoint)

    # --- Transform review embeddings ---
    print("\nProjecting review embeddings in chunks...")
    review_out = os.path.join(OUTPUT_DIR, "review_embeddings_pca.npy")
    transform_checkpoint = os.path.join(OUTPUT_DIR, "pca_transform_checkpoint.json")
    transform_chunked_resume(pca, review_embeddings, CHUNK_SIZE, review_out, transform_checkpoint)

    # --- Transform meta embeddings ---
    print("\nProjecting meta embeddings (fast in-memory)...")
    meta_out = os.path.join(OUTPUT_DIR, "meta_embeddings_pca.npy")
    if not os.path.exists(meta_out):
        meta_pca = pca.transform(meta_embeddings).astype(np.float32)
        np.save(meta_out, meta_pca)
        print(f"Saved reduced meta embeddings   → {meta_out}  shape={meta_pca.shape}")
    else:
        print(f"Metadata PCA embeddings already exist at {meta_out}. Skipping.")

    print("\nDone! Incremental PCA reduction complete.")

if __name__ == "__main__":
    main()
