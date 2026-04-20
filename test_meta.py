import pandas as pd
df = pd.read_parquet("data/processed/meta-NYC-restaurant.parquet")
print(df.columns)
