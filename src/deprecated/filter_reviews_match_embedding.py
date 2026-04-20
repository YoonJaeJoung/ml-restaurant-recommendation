import pandas as pd

def filter_reviews(input_path, output_path, min_reviews=30, max_reviews=500):
    print("Loading data...")
    review_df = pd.read_parquet(input_path)
    print(f"Original shape: {len(review_df)}")
    
    # 1. Filter out restaurants with too few reviews (> 30)
    print(f"Filtering: keeping only restaurants with > {min_reviews} reviews...")
    review_counts = review_df.groupby('gmap_id').size()
    valid_gmap_ids = review_counts[review_counts > min_reviews].index
    
    review_df = review_df[review_df['gmap_id'].isin(valid_gmap_ids)]
    print(f"After min_reviews shape: {len(review_df)}")
    
    # 2. Downsampling: Keep at most max_reviews per restaurant (<= 500)
    if max_reviews is not None:
        print(f"Downsampling: keeping maximum {max_reviews} reviews per restaurant...")
        review_df = review_df.groupby('gmap_id').head(max_reviews).reset_index(drop=True)
        print(f"Final shape after max limit: {len(review_df)}")
    
    # 3. Save the filtered dataframe
    print("Saving to parquet...")
    review_df.to_parquet(output_path, index=False)
    print(f"Successfully saved matched data ({len(review_df)} rows) to: {output_path}")

if __name__ == "__main__":
    INPUT_PATH = "./data/processed/review-NYC-restaurant.parquet"
    OUTPUT_PATH = "./data/processed/review-NYC-restaurant-filtered.parquet"
    
    # Using 30-500 rule to exactly match the 3,746,426 rows
    filter_reviews(INPUT_PATH, OUTPUT_PATH, min_reviews=30, max_reviews=500)
