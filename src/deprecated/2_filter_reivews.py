import pandas as pd

# Google Translate wrapper markers. When a reviewer's text is not in the
# target locale, Google Maps returns text of the form:
#   "(Translated by Google) <english>\n\n(Original)\n<foreign text>"
# We want only the English portion for semantic search / TF-IDF.
TRANS_MARK = "(Translated by Google)"
ORIG_MARK = "(Original)"


def select_english_text(text):
    """Return the English portion of a review's text field.

    - If the text begins with '(Translated by Google)', extract the English
      translation between that marker and '(Original)'.
    - Otherwise return the text unchanged (already in the target locale).
    - None / NaN / empty -> "".
    """
    if not isinstance(text, str) or not text:
        return ""
    stripped = text.lstrip()
    if stripped.startswith(TRANS_MARK):
        after = stripped[len(TRANS_MARK):]
        english = after.split(ORIG_MARK, 1)[0]
        return english.strip()
    return text


def 1_data_processing(input_path, output_path, min_reviews=30, max_reviews=500):
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

  # 3. Extract English text for embedding / TF-IDF
  print("Extracting English text (stripping (Translated by Google) wrapper when present)...")
  text_series = review_df["text"].fillna("")
  starts_with_trans = text_series.str.lstrip().str.startswith(TRANS_MARK)
  has_original_marker = text_series.str.contains(ORIG_MARK, regex=False)
  malformed_mask = starts_with_trans & ~has_original_marker

  review_df["text_for_embedding"] = review_df["text"].map(select_english_text)

  n_translated = int(starts_with_trans.sum())
  n_malformed = int(malformed_mask.sum())
  print(
      f"  {n_translated:,} Google-translated rows "
      f"({100 * n_translated / len(review_df):.2f}%) had their wrapper stripped"
  )

  if n_malformed > 0:
      print(
          f"  [WARN] {n_malformed} malformed rows: begin with '(Translated by Google)' "
          f"but no '(Original)' marker found. Prefix stripped, remainder kept."
      )
      sample = review_df.loc[malformed_mask].head(20)
      for idx, row in sample.iterrows():
          preview = repr(str(row["text"])[:120])
          print(
              f"    row_idx={idx}  gmap_id={row['gmap_id']}  "
              f"user_id={row['user_id']}  time={row['time']}  text={preview}"
          )
      if n_malformed > 20:
          print(f"    ... and {n_malformed - 20} more (showing first 20)")

  # 4. Save the filtered dataframe
  print("Saving to parquet...")
  review_df.to_parquet(output_path, index=False)
  print(f"Successfully saved matched data ({len(review_df)} rows) to: {output_path}")

if __name__ == "__main__":
  INPUT_PATH = "./data/processed/review-NYC-restaurant.parquet"
  OUTPUT_PATH = "./data/processed/review-NYC-restaurant-filtered.parquet"

  # Using 30-500 rule to exactly match the 3,746,426 rows
  1_data_processing(INPUT_PATH, OUTPUT_PATH, min_reviews=30, max_reviews=500)
