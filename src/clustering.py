"""
clustering.py
K-Means and GMM clustering for restaurant grouping.
"""

import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


DATA_DIR = "data/processed"


def restore_filtered_meta():
    """Restore the filtered meta_df aligned with meta_embeddings.npy.

    Reproduces the exact filtering from 1_embedding.py:
      - read full meta parquet
      - read review parquet, count reviews per gmap_id
      - keep restaurants with > 30 reviews
      - filter meta_df to those gmap_ids (preserving original row order)
    """
    meta_df = pd.read_parquet(f"{DATA_DIR}/meta-NYC-restaurant.parquet")
    review_df = pd.read_parquet(f"{DATA_DIR}/review-NYC-restaurant.parquet")

    review_counts = review_df.groupby("gmap_id").size()
    valid_gmap_ids = review_counts[review_counts > 30].index

    meta_df = meta_df[meta_df["gmap_id"].isin(valid_gmap_ids)].reset_index(drop=True)
    return meta_df


def build_restaurant_ids(meta_df):
    """Extract and save restaurant_ids list aligned with embeddings."""
    restaurant_ids = meta_df["gmap_id"].tolist()
    with open(f"{DATA_DIR}/restaurant_ids.json", "w") as f:
        json.dump(restaurant_ids, f)
    print(f"Saved restaurant_ids.json  len={len(restaurant_ids)}  first 3: {restaurant_ids[:3]}")
    return restaurant_ids


def build_features_meta():
    """Load meta_embeddings, cast to float32, L2-normalize, and save."""
    meta_emb = np.load(f"{DATA_DIR}/meta_embeddings.npy").astype(np.float32)
    meta_normed = normalize(meta_emb, norm="l2")
    np.save(f"{DATA_DIR}/features_meta.npy", meta_normed)
    print(f"Saved features_meta.npy  shape={meta_normed.shape}  NaN count={np.isnan(meta_normed).sum()}")
    return meta_normed


def build_features_combined(meta_normed, restaurant_ids):
    """Build meta + TF-IDF combined feature matrix.

    - Reads filtered reviews, concatenates all review texts per restaurant
    - Orders rows to match restaurant_ids (same order as meta_embeddings)
    - Extracts TF-IDF features, L2-normalizes, hstacks with meta features
    """
    review_df = pd.read_parquet(
        f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet",
        columns=["gmap_id", "text_for_embedding"],
    )

    # Concatenate all review texts per restaurant (English-only text)
    review_df["text_for_embedding"] = review_df["text_for_embedding"].fillna("")
    agg = review_df.groupby("gmap_id")["text_for_embedding"].apply(" ".join).reset_index()
    agg.columns = ["gmap_id", "all_text"]

    # Align to restaurant_ids order
    id_order = pd.DataFrame({"gmap_id": restaurant_ids, "_order": range(len(restaurant_ids))})
    agg = id_order.merge(agg, on="gmap_id", how="left")
    agg = agg.sort_values("_order")
    agg["all_text"] = agg["all_text"].fillna("")

    # TF-IDF
    custom_stop_words = [
        "good", "great", "nice", "delicious", "amazing", "excellent",
        "bad", "food", "place", "restaurant", "came", "got", "went",
        "time", "really", "just", "ordered", "staff", "service", "definitely",
    ]
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    stop_words = list(ENGLISH_STOP_WORDS | set(custom_stop_words))

    vectorizer = TfidfVectorizer(
        max_features=500,
        min_df=5,
        max_df=0.3,
        ngram_range=(1, 2),
        stop_words=stop_words,
    )
    tfidf_matrix = vectorizer.fit_transform(agg["all_text"]).toarray().astype(np.float32)
    tfidf_normed = normalize(tfidf_matrix, norm="l2")

    # Combine
    combined = np.hstack([meta_normed, tfidf_normed])
    np.save(f"{DATA_DIR}/features_combined.npy", combined)
    print(f"Saved features_combined.npy  shape={combined.shape}  NaN count={np.isnan(combined).sum()}")
    return combined


def build_category_onehot(restaurant_ids, min_count=50):
    """Build category one-hot matrix aligned with restaurant_ids.

    Each restaurant may have multiple categories (multi-label).
    Only categories appearing in >= min_count restaurants are kept.
    """
    from sklearn.preprocessing import MultiLabelBinarizer

    meta_df = pd.read_parquet(f"{DATA_DIR}/meta-NYC-restaurant.parquet",
                              columns=["gmap_id", "category"])
    meta_df = meta_df.drop_duplicates("gmap_id", keep="first")

    # Align to restaurant_ids order
    id_order = pd.DataFrame({"gmap_id": restaurant_ids, "_order": range(len(restaurant_ids))})
    merged = id_order.merge(meta_df, on="gmap_id", how="left").sort_values("_order")
    merged["category"] = merged["category"].apply(
        lambda x: list(x) if x is not None and hasattr(x, '__iter__') else []
    )

    # Filter low-frequency categories
    from collections import Counter
    counter = Counter()
    for cats in merged["category"]:
        for c in cats:
            counter[c] += 1
    valid_cats = {c for c, cnt in counter.items() if cnt >= min_count}
    merged["category"] = merged["category"].apply(
        lambda cats: [c for c in cats if c in valid_cats]
    )

    mlb = MultiLabelBinarizer()
    onehot = mlb.fit_transform(merged["category"]).astype(np.float32)
    print(f"Category one-hot: {onehot.shape[1]} categories (min_count={min_count})")
    return onehot


def run_experiments(meta_normed, combined):
    """Run PCA, UMAP, and clustering experiments (KMeans + GMM) across feature sets."""
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.mixture import GaussianMixture
    from sklearn.metrics import silhouette_score
    import os

    os.makedirs("results/clustering", exist_ok=True)

    # Step 1: PCA to 100 dimensions
    print("Running PCA...")
    pca_meta = PCA(n_components=100, random_state=42).fit_transform(meta_normed)
    pca_combined = PCA(n_components=100, random_state=42).fit_transform(combined)
    print(f"PCA done: meta={pca_meta.shape}, combined={pca_combined.shape}")

    # Step 2: UMAP to 2D (meta only, for visualization)
    print("Running UMAP (this may take a few minutes)...")
    import umap
    reducer = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=42)
    meta_2d = reducer.fit_transform(pca_meta)
    np.save(f"{DATA_DIR}/umap_2d.npy", meta_2d)
    print(f"UMAP done: shape={meta_2d.shape}")

    # Step 3: 4 schemes × extended K search
    k_values = [5, 8, 10, 15, 20, 25, 30, 40, 50]
    feature_map = {"meta": pca_meta, "combined": pca_combined}
    results = []
    best_labels = {}

    for feat_name, X in feature_map.items():
        for algo in ["kmeans", "gmm"]:
            scheme = f"{feat_name}+{algo}"
            print(f"\n--- {scheme} ---")
            best_score = -1
            for k in k_values:
                if algo == "kmeans":
                    model = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = model.fit_predict(X)
                else:
                    model = GaussianMixture(
                        n_components=k, covariance_type="diag", random_state=42
                    )
                    model.fit(X)
                    labels = model.predict(X)

                score = silhouette_score(
                    X, labels, sample_size=3000, random_state=42
                )
                results.append({"scheme": scheme, "k": k, "silhouette": round(score, 4)})
                print(f"  k={k}: silhouette={score:.4f}")

                if score > best_score:
                    best_score = score
                    best_labels[scheme] = labels.copy()

    # Step 4: Save results
    df = pd.DataFrame(results)
    df.to_csv("results/clustering/clustering_scores.csv", index=False)

    print("\n=== Best result per scheme ===")
    summary = df.loc[df.groupby("scheme")["silhouette"].idxmax()]
    print(summary.to_string(index=False))

    for scheme, labels in best_labels.items():
        np.save(f"{DATA_DIR}/labels_{scheme}.npy", labels)
        print(f"Saved labels_{scheme}.npy")

    return df, best_labels


def visualize_results(df_scores, best_labels):
    """Generate three visualization plots from clustering results."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import os

    os.makedirs("results/clustering", exist_ok=True)

    umap_2d = np.load(f"{DATA_DIR}/umap_2d.npy")

    # === Plot 1: 2x2 UMAP scatter for all 4 schemes ===
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    schemes = ["meta+kmeans", "meta+gmm", "combined+kmeans", "combined+gmm"]
    titles = ["Pure Meta + KMeans", "Pure Meta + GMM",
              "Meta+TF-IDF + KMeans", "Meta+TF-IDF + GMM"]

    for ax, scheme, title in zip(axes.flat, schemes, titles):
        labels = best_labels[scheme]
        best_row = df_scores[df_scores["scheme"] == scheme].sort_values("silhouette").iloc[-1]
        ax.scatter(umap_2d[:, 0], umap_2d[:, 1],
                   c=labels, cmap="tab20", s=1, alpha=0.4)
        ax.set_title(f"{title}\nk={int(best_row['k'])}, "
                     f"silhouette={best_row['silhouette']:.4f}", fontsize=12)
        ax.axis("off")

    plt.suptitle("NYC Restaurant Clustering - UMAP Visualization", fontsize=15, y=1.01)
    plt.tight_layout()
    plt.savefig("results/clustering/cluster_comparison_umap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: results/clustering/cluster_comparison_umap.png")

    # === Plot 2: Silhouette vs K line chart ===
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    colors = {"meta+kmeans": "#2196F3", "meta+gmm": "#FF9800",
              "combined+kmeans": "#4CAF50", "combined+gmm": "#E91E63"}

    for scheme, color in colors.items():
        subset = df_scores[df_scores["scheme"] == scheme].sort_values("k")
        ax2.plot(subset["k"], subset["silhouette"],
                 marker="o", label=scheme, color=color, linewidth=2)
        best = subset.loc[subset["silhouette"].idxmax()]
        ax2.annotate(f"k={int(best['k'])}\n{best['silhouette']:.4f}",
                     xy=(best["k"], best["silhouette"]),
                     xytext=(8, 4), textcoords="offset points", fontsize=9)

    ax2.set_xlabel("K (number of clusters)", fontsize=12)
    ax2.set_ylabel("Silhouette Score", fontsize=12)
    ax2.set_title("Silhouette Score vs K - All Schemes", fontsize=14)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("results/clustering/silhouette_vs_k.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: results/clustering/silhouette_vs_k.png")

    # === Plot 3: Cluster size distribution for best scheme ===
    best_scheme = "combined+kmeans"
    labels = best_labels[best_scheme]
    cluster_sizes = pd.Series(labels).value_counts().sort_index()

    fig3, ax3 = plt.subplots(figsize=(14, 5))
    bars = ax3.bar(cluster_sizes.index, cluster_sizes.values, color="#4CAF50", alpha=0.8)
    ax3.axhline(cluster_sizes.mean(), color="red", linestyle="--",
                label=f"Mean: {cluster_sizes.mean():.0f} restaurants")
    ax3.set_xlabel("Cluster ID", fontsize=12)
    ax3.set_ylabel("Number of Restaurants", fontsize=12)
    best_k = int(df_scores[df_scores["scheme"] == best_scheme].sort_values("silhouette").iloc[-1]["k"])
    ax3.set_title(f"Cluster Size Distribution ({best_scheme}, k={best_k})", fontsize=14)
    ax3.legend()
    for bar, val in zip(bars, cluster_sizes.values):
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                 str(val), ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    plt.savefig("results/clustering/best_cluster_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Saved: results/clustering/best_cluster_distribution.png")


if __name__ == "__main__":
    import os

    # If feature files already exist, load them directly; otherwise build from scratch
    meta_path = f"{DATA_DIR}/features_meta.npy"
    combined_path = f"{DATA_DIR}/features_combined.npy"
    ids_path = f"{DATA_DIR}/restaurant_ids.json"

    if os.path.exists(meta_path) and os.path.exists(ids_path):
        print("=== Loading pre-built meta features ===")
        meta_normed = np.load(meta_path)
        with open(ids_path) as f:
            restaurant_ids = json.load(f)
        print(f"features_meta: {meta_normed.shape}, ids: {len(restaurant_ids)}")
    else:
        print("=== Step 1: Restore filtered meta_df ===")
        meta_df = restore_filtered_meta()
        assert len(meta_df) == 21311, f"Expected 21311 rows, got {len(meta_df)}"
        restaurant_ids = build_restaurant_ids(meta_df)

        print("\n=== Step 2: Build features_meta (pure meta embedding) ===")
        meta_normed = build_features_meta()

    print("\n=== Step 3: Rebuild features_combined (meta + TF-IDF) ===")
    combined = build_features_combined(meta_normed, restaurant_ids)

    print("\n=== Step 4: Build category one-hot and combined_cat features ===")
    cat_onehot = build_category_onehot(restaurant_ids, min_count=50)
    combined_cat = np.hstack([combined, cat_onehot])
    np.save(f"{DATA_DIR}/features_combined_cat.npy", combined_cat)
    print(f"features_combined_cat shape: {combined_cat.shape}")

    print("\n=== Step 5: Run clustering experiments (all schemes) ===")
    scores_path = "results/clustering/clustering_scores.csv"
    schemes = ["meta+kmeans", "meta+gmm", "combined+kmeans", "combined+gmm"]
    df_scores, best_labels = run_experiments(meta_normed, combined)

    print("\n=== Step 6: Run combined_cat+kmeans extended k search ===")
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    pca_combined_cat = PCA(n_components=100, random_state=42).fit_transform(combined_cat)
    print(f"PCA done: combined_cat -> {pca_combined_cat.shape}")

    k_values_ext = [25, 30, 40, 50, 60, 75, 100, 125, 150]
    cat_results = []
    best_score_cat = -1
    best_labels_cat = None

    for k in k_values_ext:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(pca_combined_cat)
        score = silhouette_score(pca_combined_cat, labels, sample_size=3000, random_state=42)
        cat_results.append({"scheme": "combined_cat+kmeans", "k": k, "silhouette": round(score, 4)})
        print(f"  k={k}: silhouette={score:.4f}")
        if score > best_score_cat:
            best_score_cat = score
            best_labels_cat = labels.copy()

    # Also run combined+kmeans on same k range for direct comparison
    pca_combined = PCA(n_components=100, random_state=42).fit_transform(combined)
    nocategory_results = []
    for k in k_values_ext:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(pca_combined)
        score = silhouette_score(pca_combined, labels, sample_size=3000, random_state=42)
        nocategory_results.append({"scheme": "combined+kmeans", "k": k, "silhouette": round(score, 4)})

    print("\n=== Comparison: combined+kmeans vs combined_cat+kmeans ===")
    print(f"{'k':>5}  {'combined+kmeans':>16}  {'combined_cat+kmeans':>20}  {'diff':>8}")
    for nc, wc in zip(nocategory_results, cat_results):
        diff = wc["silhouette"] - nc["silhouette"]
        print(f"{nc['k']:>5}  {nc['silhouette']:>16.4f}  {wc['silhouette']:>20.4f}  {diff:>+8.4f}")

    # Save extended results
    all_cat_results = pd.DataFrame(cat_results + nocategory_results)
    all_cat_results.to_csv("results/clustering/clustering_scores_extended.csv", index=False)

    np.save(f"{DATA_DIR}/labels_combined_cat+kmeans.npy", best_labels_cat)
    print(f"\nBest combined_cat+kmeans: k={cat_results[cat_results.index(max(cat_results, key=lambda x: x['silhouette']))]}")

    print("\n=== Step 7: Visualize results ===")
    visualize_results(df_scores, best_labels)
