"""
4_pca.py
Dimensionality reduction of review and metadata embeddings via PCA.

Reads the merged 768-dimensional embedding vectors produced by 2_embedding.py,
fits PCA, and saves the reduced-dimension vectors alongside the fitted PCA
model so downstream scripts (e.g. 5_search_test_pca.py) can project new
queries into the same low-dimensional space.

Output files (saved to data/processed/):
  - review_embeddings_pca.npy   : PCA-reduced review embeddings  (N, n_components)
  - meta_embeddings_pca.npy     : PCA-reduced metadata embeddings (M, n_components)
  - pca_model.pkl               : Fitted sklearn PCA object (for projecting queries)
"""

import os
import numpy as np
import joblib
from sklearn.decomposition import PCA

# --------------- Configuration ---------------
INPUT_DIR = "./data/processed"
OUTPUT_DIR = "./data/processed"
N_COMPONENTS = 128          # Target dimensionality (tune as needed)
CHUNK_SIZE = 100_000        # Rows read at a time when the file is memory-mapped
# ------------------------------------------------


def fit_pca(embeddings: np.ndarray, n_components: int) -> PCA:
    """Fit PCA on the embedding matrix and return the fitted model."""
    print(f"Fitting PCA (n_components={n_components}) on {embeddings.shape[0]:,} vectors ...")
    pca = PCA(n_components=n_components, random_state=42)
    pca.fit(embeddings)
    explained = pca.explained_variance_ratio_.sum() * 100
    print(f"  → Explained variance retained: {explained:.2f}%")
    return pca


def transform_chunked(pca: PCA, embeddings: np.ndarray, chunk_size: int) -> np.ndarray:
    """
    Project embeddings through PCA in chunks to limit peak RAM usage
    when the full embedding matrix is memory-mapped.
    """
    n = embeddings.shape[0]
    out = np.empty((n, pca.n_components_), dtype=np.float32)
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        out[start:end] = pca.transform(embeddings[start:end]).astype(np.float32)
        if (start // chunk_size) % 5 == 0:
            print(f"  Transformed {end:,} / {n:,} rows")
    return out


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Load embeddings (memory-mapped to keep RAM usage low) ---
    review_emb_path = os.path.join(INPUT_DIR, "review_embeddings.npy")
    meta_emb_path = os.path.join(INPUT_DIR, "meta_embeddings.npy")

    print("Loading review embeddings (mmap) ...")
    review_embeddings = np.load(review_emb_path, mmap_mode="r")
    print(f"  Review embeddings shape: {review_embeddings.shape}")

    print("Loading meta embeddings ...")
    meta_embeddings = np.load(meta_emb_path)
    print(f"  Meta embeddings shape:   {meta_embeddings.shape}")

    # --- Fit PCA on review embeddings (dominant corpus) ---
    pca = fit_pca(review_embeddings, N_COMPONENTS)

    # --- Transform review embeddings ---
    print("Projecting review embeddings ...")
    review_pca = transform_chunked(pca, review_embeddings, CHUNK_SIZE)

    # --- Transform meta embeddings ---
    print("Projecting meta embeddings ...")
    meta_pca = pca.transform(meta_embeddings).astype(np.float32)

    # --- Save outputs ---
    review_out = os.path.join(OUTPUT_DIR, "review_embeddings_pca.npy")
    meta_out = os.path.join(OUTPUT_DIR, "meta_embeddings_pca.npy")
    model_out = os.path.join(OUTPUT_DIR, "pca_model.pkl")

    np.save(review_out, review_pca)
    print(f"Saved reduced review embeddings → {review_out}  shape={review_pca.shape}")

    np.save(meta_out, meta_pca)
    print(f"Saved reduced meta embeddings   → {meta_out}  shape={meta_pca.shape}")

    joblib.dump(pca, model_out)
    print(f"Saved fitted PCA model          → {model_out}")

    print("\nDone! PCA reduction complete.")


if __name__ == "__main__":
    main()
