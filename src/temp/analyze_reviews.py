"""
分析餐厅评论数据，评估embedding和rating分析的可行性
"""

import pandas as pd
import numpy as np
from collections import Counter
import re


def analyze_review_data():
    """
    加载parquet文件，分析评论数量和字数分布
    """
    
    print("=" * 80)
    print("📊 Restaurant Review Data Analysis for Embedding & Rating")
    print("=" * 80)
    
    # 加载数据
    print("\n✅ Loading metadata...")
    df_meta = pd.read_parquet("data/processed/meta-NYC-restaurant.parquet")
    print(f"   Total restaurants: {len(df_meta):,}")
    
    print("✅ Loading reviews...")
    df_reviews = pd.read_parquet("data/processed/review-NYC-restaurant.parquet")
    print(f"   Total reviews: {len(df_reviews):,}")
    
    # 统计每个餐厅的评论数量
    print("\n" + "=" * 80)
    print("📈 Review Count per Restaurant")
    print("=" * 80)
    
    reviews_per_restaurant = df_reviews.groupby('gmap_id').size().reset_index(name='review_count')
    print(f"\nTotal restaurants with reviews: {len(reviews_per_restaurant):,}")
    print(f"Average reviews per restaurant: {reviews_per_restaurant['review_count'].mean():.2f}")
    print(f"Median reviews per restaurant: {reviews_per_restaurant['review_count'].median():.2f}")
    print(f"Max reviews in one restaurant: {reviews_per_restaurant['review_count'].max():,}")
    print(f"Min reviews in one restaurant: {reviews_per_restaurant['review_count'].min()}")
    
    # 显示分布
    print(f"\nReview count distribution:")
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    for p in percentiles:
        val = reviews_per_restaurant['review_count'].quantile(p/100)
        print(f"   {p}th percentile: {val:.0f} reviews")
    
    # 统计评论字数
    print("\n" + "=" * 80)
    print("📝 Review Text Length Analysis")
    print("=" * 80)
    
    # 计算评论字数（处理null值）
    df_reviews['text_length'] = df_reviews['text'].fillna('').apply(lambda x: len(str(x)) if pd.notna(x) else 0)
    df_reviews['word_count'] = df_reviews['text'].fillna('').apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)
    
    print(f"\nTotal characters across all reviews: {df_reviews['text_length'].sum():,}")
    print(f"Total words across all reviews: {df_reviews['word_count'].sum():,}")
    print(f"Average characters per review: {df_reviews['text_length'].mean():.2f}")
    print(f"Average words per review: {df_reviews['word_count'].mean():.2f}")
    print(f"Median characters per review: {df_reviews['text_length'].median():.2f}")
    
    # 显示文本长度分布
    print(f"\nText length distribution:")
    percentiles = [10, 25, 50, 75, 90, 95]
    for p in percentiles:
        val = df_reviews['text_length'].quantile(p/100)
        print(f"   {p}th percentile: {val:.0f} characters")
    
    # 统计每个餐厅的总字数
    print("\n" + "=" * 80)
    print("📚 Total Review Content per Restaurant")
    print("=" * 80)
    
    review_stats = df_reviews.groupby('gmap_id').agg({
        'text_length': 'sum',
        'word_count': 'sum',
        'rating': ['count', 'mean', 'std']
    }).reset_index()
    
    review_stats.columns = ['gmap_id', 'total_chars', 'total_words', 'review_count', 'avg_rating', 'rating_std']
    
    print(f"\nTotal characters available for embedding:")
    print(f"   Sum: {review_stats['total_chars'].sum():,} characters")
    print(f"   Average per restaurant: {review_stats['total_chars'].mean():.0f} characters")
    print(f"   Median per restaurant: {review_stats['total_chars'].median():.0f} characters")
    
    print(f"\nTotal words available for embedding:")
    print(f"   Sum: {review_stats['total_words'].sum():,} words")
    print(f"   Average per restaurant: {review_stats['total_words'].mean():.0f} words")
    print(f"   Median per restaurant: {review_stats['total_words'].median():.0f} words")
    
    # 评分分析
    print("\n" + "=" * 80)
    print("⭐ Rating Analysis")
    print("=" * 80)
    
    print(f"\nRatings in reviews:")
    print(f"   Total reviews with ratings: {df_reviews['rating'].notna().sum():,}")
    print(f"   Average rating: {df_reviews['rating'].mean():.2f}★")
    print(f"   Median rating: {df_reviews['rating'].median():.1f}★")
    print(f"   Rating std dev: {df_reviews['rating'].std():.2f}")
    
    rating_dist = df_reviews['rating'].value_counts().sort_index()
    print(f"\nRating distribution:")
    for rating, count in rating_dist.items():
        pct = count / len(df_reviews) * 100
        bar = "█" * int(pct / 2)
        print(f"   {rating}★: {count:>10,} ({pct:>5.1f}%) {bar}")
    
    # 评估embedding可行性
    print("\n" + "=" * 80)
    print("🤖 Embedding & Rating Analysis Feasibility")
    print("=" * 80)
    
    print(f"\n✅ Data Availability:")
    print(f"   Reviews available for embedding: {len(df_reviews):,}")
    print(f"   Restaurants with reviews: {len(review_stats):,}")
    print(f"   Total text to process: {review_stats['total_words'].sum():,} words")
    
    # 计算有足够内容的餐厅
    min_words_threshold = 50  # 最少50个词的评论
    restaurants_with_content = review_stats[review_stats['total_words'] >= min_words_threshold]
    print(f"\n   Restaurants with ≥{min_words_threshold} words: {len(restaurants_with_content):,}")
    print(f"   Reviews to process: {restaurants_with_content['review_count'].sum():,}")
    
    # 计算有足够评分的餐厅
    min_reviews_threshold = 5  # 最少5条评论
    restaurants_with_reviews = review_stats[review_stats['review_count'] >= min_reviews_threshold]
    print(f"\n   Restaurants with ≥{min_reviews_threshold} reviews: {len(restaurants_with_reviews):,}")
    print(f"   Reviews to process: {restaurants_with_reviews['review_count'].sum():,}")
    print(f"   Avg rating variance: {restaurants_with_reviews['rating_std'].mean():.2f}")
    
    print(f"\n✅ Feasibility Assessment:")
    
    # 检查是否可以做embedding
    embedding_feasible = review_stats['total_words'].sum() > 100000
    print(f"\n   Embedding feasibility: {'✅ YES' if embedding_feasible else '❌ NO'}")
    if embedding_feasible:
        print(f"   └─ Sufficient text data ({review_stats['total_words'].sum():,} words)")
    
    # 检查是否可以做rating分析
    rating_feasible = len(restaurants_with_reviews) > 100
    print(f"\n   Rating-based analysis feasibility: {'✅ YES' if rating_feasible else '❌ NO'}")
    if rating_feasible:
        print(f"   └─ Sufficient restaurants with multiple reviews ({len(restaurants_with_reviews):,} restaurants)")
    
    # 推荐
    print(f"\n💡 Recommendations:")
    if embedding_feasible:
        print(f"   ✅ You have {review_stats['total_words'].sum():,} words → Good for embedding")
        print(f"      - Use sentence transformer or other pre-trained models")
        print(f"      - Process ~{len(df_reviews):,} reviews to get embeddings")
    else:
        print(f"   ⚠️  You have only {review_stats['total_words'].sum():,} words → May be limited for embedding")
    
    if rating_feasible:
        print(f"   ✅ You have {len(restaurants_with_reviews):,} restaurants with ≥{min_reviews_threshold} reviews")
        print(f"      - Can build rating prediction models")
        print(f"      - Can analyze rating trends by review features")
    else:
        print(f"   ⚠️  You have only {len(restaurants_with_reviews):,} restaurants with ≥{min_reviews_threshold} reviews")
    
    # 输出详细统计表
    print("\n" + "=" * 80)
    print("📋 Top 10 Restaurants by Review Volume & Content")
    print("=" * 80)
    
    top_restaurants = review_stats.nlargest(10, 'total_words')[
        ['gmap_id', 'review_count', 'total_chars', 'total_words', 'avg_rating']
    ]
    
    # 合并餐厅名称
    top_restaurants = top_restaurants.merge(
        df_meta[['gmap_id', 'name']],
        on='gmap_id',
        how='left'
    )
    
    print(f"\n{'Restaurant':<40} {'Reviews':<10} {'Words':<12} {'Avg Rating':<12}")
    print("-" * 74)
    for _, row in top_restaurants.iterrows():
        name = str(row['name'])[:37]
        print(f"{name:<40} {row['review_count']:<10} {row['total_words']:<12,} {row['avg_rating']:<12.2f}")
    
    # 输出低字数的餐厅
    print("\n" + "=" * 80)
    print("⚠️  Restaurants with Low Review Content")
    print("=" * 80)
    
    low_content = review_stats[review_stats['total_words'] < 50]
    print(f"\nRestaurants with <50 words total: {len(low_content):,} ({len(low_content)/len(review_stats)*100:.1f}%)")
    print(f"Restaurants with <100 words total: {len(review_stats[review_stats['total_words'] < 100]):,}")
    
    # 保存详细报告
    report_file = "results/review_analysis_report.csv"
    review_stats.to_csv(report_file, index=False)
    print(f"\n✅ Detailed report saved to: {report_file}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_review_data()
