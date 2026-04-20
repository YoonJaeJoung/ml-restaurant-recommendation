"""
6c_clustering_evaluation.py
Consolidated evaluation pipeline for NYC Restaurant Clustering.
- Runs grid search for K and Feature Scheme (Silhouette scores)
- Generates human-readable cluster summaries (TF-IDF keywords)
- Produces automated visualizations (Plots, WordClouds, Maps)
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score
from wordcloud import WordCloud
import plotly.express as px

# Configuration
DATA_DIR = "data/processed"
RESULTS_DIR = "results/clustering"
EVAL_DIR = "results/clustering/evaluation"

def restore_filtered_meta():
    meta_df = pd.read_parquet(f"{DATA_DIR}/meta-NYC-restaurant.parquet")
    review_filtered_path = f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet"
    review_df = pd.read_parquet(review_filtered_path, columns=["gmap_id"])
    valid_gmap_ids = review_df["gmap_id"].unique()
    return meta_df[meta_df["gmap_id"].isin(valid_gmap_ids)].reset_index(drop=True)

def build_features_combined(meta_normed, restaurant_ids):
    review_df = pd.read_parquet(
        f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet",
        columns=["gmap_id", "text_for_embedding"],
    )
    review_df["text_for_embedding"] = review_df["text_for_embedding"].fillna("")
    agg = review_df.groupby("gmap_id")["text_for_embedding"].apply(" ".join).reset_index()
    agg.columns = ["gmap_id", "all_text"]

    id_order = pd.DataFrame({"gmap_id": restaurant_ids, "_order": range(len(restaurant_ids))})
    agg = id_order.merge(agg, on="gmap_id", how="left").sort_values("_order")
    agg["all_text"] = agg["all_text"].fillna("")

    custom_stop_words = [
        "good", "great", "nice", "delicious", "amazing", "excellent", "best",
        "bad", "food", "place", "restaurant", "came", "got", "went",
        "time", "really", "just", "ordered", "staff", "service", "definitely",
        "like", "get", "love", "highly", "recommend"
    ]
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    stop_words = list(ENGLISH_STOP_WORDS | set(custom_stop_words))

    vectorizer = TfidfVectorizer(
        max_features=500, min_df=5, max_df=0.3,
        ngram_range=(1, 2), stop_words=stop_words,
    )
    tfidf_matrix = vectorizer.fit_transform(agg["all_text"]).toarray().astype(np.float32)
    tfidf_normed = normalize(tfidf_matrix, norm="l2")
    return np.hstack([meta_normed, tfidf_normed])

def run_grid_search(meta_normed, combined):
    print("🧹 Running Silhouette Grid Search...")
    pca_meta = PCA(n_components=100, random_state=42).fit_transform(meta_normed)
    pca_combined = PCA(n_components=100, random_state=42).fit_transform(combined)

    k_values = [5, 8, 10, 15, 20, 25, 30, 40, 50]
    feature_map = {"meta": pca_meta, "combined": pca_combined}
    results = []

    for feat_name, X in feature_map.items():
        for algo in ["kmeans", "gmm"]:
            scheme = f"{feat_name}+{algo}"
            print(f"  Evaluating scheme: {scheme}")
            for k in k_values:
                if algo == "kmeans":
                    model = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = model.fit_predict(X)
                else:
                    model = GaussianMixture(n_components=k, covariance_type="diag", random_state=42)
                    labels = model.fit(X).predict(X)

                score = silhouette_score(X, labels, sample_size=3000, random_state=42)
                results.append({"scheme": scheme, "k": k, "silhouette": round(float(score), 4)})
    
    scores_df = pd.DataFrame(results)
    scores_df.to_csv(f"{EVAL_DIR}/clustering_scores.csv", index=False)
    return scores_df

def generate_summaries(clusters_df):
    print("📝 Generating Cluster Keyword Summaries...")
    review_parquet = f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet"
    reviews_df = pd.read_parquet(review_parquet, columns=["gmap_id", "text_for_embedding"])
    
    merged = reviews_df.merge(clusters_df[["gmap_id", "cluster"]], on="gmap_id")
    cluster_texts = merged.groupby("cluster")["text_for_embedding"].apply(lambda x: " ".join(x.fillna(""))).reset_index()
    
    custom_stop_words = ["good", "great", "nice", "delicious", "amazing", "food", "place", "ordered", "time", "just", "really"]
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    stop_words = list(ENGLISH_STOP_WORDS | set(custom_stop_words))
    
    vectorizer = TfidfVectorizer(max_features=2000, stop_words=stop_words, ngram_range=(1,2))
    tfidf_matrix = vectorizer.fit_transform(cluster_texts["text_for_embedding"])
    feature_names = vectorizer.get_feature_names_out()
    
    summaries = []
    for i, row in cluster_texts.iterrows():
        cluster_id = int(row["cluster"])
        scores = tfidf_matrix[i].toarray().flatten()
        top_keywords = [feature_names[idx] for idx in scores.argsort()[-10:][::-1]]
        
        subset = clusters_df[clusters_df["cluster"] == cluster_id]
        summaries.append({
            "cluster_id": cluster_id,
            "size": len(subset),
            "avg_rating": round(float(subset["avg_rating"].mean()), 2),
            "top_borough": subset["borough"].value_counts().index[0] if not subset.empty else "N/A",
            "top_keywords": top_keywords
        })
    
    with open(f"{EVAL_DIR}/cluster_summary.json", "w") as f:
        json.dump(summaries, f, indent=2)
    return summaries

def save_visualizations(scores_df, clusters_df, summaries):
    print("🎨 Saving Visualizations to results/clustering/evaluation/ ...")
    
    # 1. Silhouette vs K
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=scores_df, x='k', y='silhouette', hue='scheme', marker='o')
    plt.title("Clustering Performance: Silhouette Score vs K")
    plt.grid(True, alpha=0.3)
    plt.savefig(f"{EVAL_DIR}/silhouette_vs_k.png")
    plt.close()

    # 2. Cluster Size Distribution
    plt.figure(figsize=(12, 6))
    sizes = sorted([s['size'] for s in summaries], reverse=True)
    plt.bar(range(len(sizes)), sizes, color='skyblue')
    plt.title("Cluster Size Distribution (K=50)")
    plt.xlabel("Cluster Rank (by size)")
    plt.ylabel("Number of Restaurants")
    plt.savefig(f"{EVAL_DIR}/cluster_size_dist.png")
    plt.close()

    # 3. WordClouds (Top 5 clusters by size as preview, but logic for all)
    wc_dir = f"{EVAL_DIR}/wordclouds"
    os.makedirs(wc_dir, exist_ok=True)
    print(f"  Generating {len(summaries)} WordClouds...")
    for s in summaries:
        text = " ".join(s['top_keywords']) # Simple repetition or weights would be better but keywords are pre-filtered
        wc = WordCloud(width=800, height=400, background_color='white').generate(text)
        wc.to_file(f"{wc_dir}/cluster_{s['cluster_id']}.png")

    # 4. Interactive Geographic Map
    fig = px.scatter_mapbox(
        clusters_df, lat="latitude", lon="longitude", color="cluster",
        hover_name="name", zoom=10, height=800,
        title="NYC Restaurant Clusters Map",
        color_continuous_scale=px.colors.cyclical.IceFire
    )
    fig.update_layout(mapbox_style="carto-positron")
    fig.write_html(f"{EVAL_DIR}/cluster_map.html")

def main():
    os.makedirs(EVAL_DIR, exist_ok=True)
    
    # 1. Prepare Data
    print("🚀 Starting Consolidated Clustering Evaluation")
    meta_df = restore_filtered_meta()
    raw_meta_emb = np.load(f"{DATA_DIR}/meta_embeddings.npy").astype(np.float32)
    meta_normed = normalize(raw_meta_emb, norm="l2")
    combined = build_features_combined(meta_normed, meta_df["gmap_id"].tolist())

    # 2. Run Grid Search (Skip if exists)
    scores_path = f"{EVAL_DIR}/clustering_scores.csv"
    if os.path.exists(scores_path):
        print(f"⏩ Found existing scores at {scores_path}. Skipping Grid Search.")
        scores_df = pd.read_csv(scores_path)
    else:
        scores_df = run_grid_search(meta_normed, combined)

    # 3. Process Current Production Result (Skip summary if exists)
    clusters_df = pd.read_csv(f"{RESULTS_DIR}/restaurant_clusters.csv")
    summary_path = f"{EVAL_DIR}/cluster_summary.json"
    if os.path.exists(summary_path):
        print(f"⏩ Found existing summary at {summary_path}. Skipping Summary Generation.")
        with open(summary_path, "r") as f:
            summaries = json.load(f)
    else:
        summaries = generate_summaries(clusters_df)

    # 4. Save Visualizations
    save_visualizations(scores_df, clusters_df, summaries)
    
    print(f"\n✅ All evaluation artifacts saved to {EVAL_DIR}")

if __name__ == "__main__":
    main()
