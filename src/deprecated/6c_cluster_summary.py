"""
6c_cluster_summary.py
Generates human-readable summaries for production restaurant clusters.
- keywords (TF-IDF)
- borough distribution
- representative venues
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_DIR = "data/processed"
RESULTS_DIR = "results/clustering"

def main():
    print("🚀 Starting Cluster Summary Generation")
    
    # 1. Load Cluster Assignments
    cluster_csv = f"{RESULTS_DIR}/restaurant_clusters.csv"
    if not os.path.exists(cluster_csv):
        raise FileNotFoundError(f"Missing {cluster_csv}. Please run clustering first.")
    
    print(f"Loading cluster mapping from {cluster_csv}...")
    clusters_df = pd.read_csv(cluster_csv)
    
    # 2. Load Filtered Reviews (Text Data)
    review_parquet = f"{DATA_DIR}/review-NYC-restaurant-filtered.parquet"
    print(f"Loading 2.1M reviews from {review_parquet} (this may take time)...")
    reviews_df = pd.read_parquet(
        review_parquet,
        columns=["gmap_id", "text_for_embedding"]
    )
    
    # 3. Associate Reviews with Clusters
    print("Joining reviews with cluster IDs...")
    # Explicitly filter clusters_df to what we need
    cluster_lookup = clusters_df[["gmap_id", "cluster"]]
    merged = reviews_df.merge(cluster_lookup, on="gmap_id", how="inner")
    
    # Cleanup to save RAM
    del reviews_df
    
    # 4. Aggregate Text per Cluster
    print("Aggregating text by cluster (50 documents)...")
    # Using a dictionary join for better memory efficiency than lambda join
    cluster_texts = merged.groupby("cluster")["text_for_embedding"].apply(lambda x: " ".join(x.fillna(""))).reset_index()
    
    print("Computing TF-IDF to find distinctive keywords...")
    # Standard restaurant stop words
    custom_stop_words = [
        "good", "great", "nice", "delicious", "amazing", "excellent", "best",
        "bad", "food", "place", "restaurant", "came", "got", "went",
        "time", "really", "just", "ordered", "staff", "service", "definitely",
        "like", "get", "love", "definitely", "highly", "recommend"
    ]
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    stop_words = list(ENGLISH_STOP_WORDS | set(custom_stop_words))
    
    vectorizer = TfidfVectorizer(
        max_features=2000, 
        stop_words=stop_words, 
        ngram_range=(1,2),
        min_df=1 # Each word must appear in at least one cluster
    )
    
    tfidf_matrix = vectorizer.fit_transform(cluster_texts["text_for_embedding"])
    feature_names = vectorizer.get_feature_names_out()
    
    # 5. Build JSON Results
    print("Compiling cluster statistics and examples...")
    summaries = []
    
    for i, row in cluster_texts.iterrows():
        cluster_id = int(row["cluster"])
        
        # Get top 10 keywords by TF-IDF score for THIS cluster
        scores = tfidf_matrix[i].toarray().flatten()
        top_indices = scores.argsort()[-15:][::-1] # Get top 15 to filter out garbage if needed
        top_keywords = [feature_names[idx] for idx in top_indices][:10]
        
        # Cluster-specific stats
        subset = clusters_df[clusters_df["cluster"] == cluster_id]
        size = len(subset)
        avg_rating = round(float(subset["avg_rating"].mean()), 2)
        
        # Geographic profile
        borough_counts = subset["borough"].value_counts()
        top_borough = borough_counts.index[0] if not borough_counts.empty else "Unknown"
        top_borough_pct = round((borough_counts.iloc[0] / size) * 100, 1) if not borough_counts.empty else 0
        
        # Representive venues (Top 3 by rating)
        examples = subset.sort_values("avg_rating", ascending=False).head(3)
        example_list = examples[["name", "borough"]].to_dict(orient="records")
        
        summaries.append({
            "cluster_id": cluster_id,
            "size": size,
            "avg_rating": avg_rating,
            "top_borough": top_borough,
            "top_borough_pct": top_borough_pct,
            "top_keywords": top_keywords,
            "example_restaurants": example_list
        })
    
    # Sort by cluster ID for consistency
    summaries.sort(key=lambda x: x["cluster_id"])
    
    out_path = f"{RESULTS_DIR}/cluster_summary.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summaries, f, indent=2)
    
    print(f"✅ Success! Cluster summary saved to {out_path}")

if __name__ == "__main__":
    main()
