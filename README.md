# ML-Restaurant-Recommendation

GitHub repository for the final project of team **Noble Jaguars** — NYU Fundamentals of Machine Learning Course.

**Team:** Ashley Ying, Jake Lipner, Langyue Zhao, Yiduo Lu, Yoonjae Andrew Joung

## Project Overview

Finding a suitable restaurant is a highly time-consuming and often inaccurate process. Users currently rely on map-based rankings or social media, manually sifting through reviews, photos, and subjective star ratings. Traditional recommendation systems typically use collaborative filtering or overall numerical ratings, ignoring the rich, nuanced information hidden within textual reviews. To address this, we are building a **context-aware restaurant recommendation system** using the [Google Local Reviews dataset](https://cseweb.ucsd.edu/~jmcauley/datasets.html#google_local) (from the UCSD recommender systems repository), which contains extensive restaurant metadata alongside a massive corpus of user-written reviews.

**Core questions we aim to answer:**
- How can we automatically retrieve and rank restaurants that best match a user's highly specific, natural-language request?
- How can we proactively recommend places based on continuous post-visit feedback, or find venues similar to a given favorite?
- How can we let users specify exactly which aspects (e.g., atmosphere, service quality) they care about, immediately calibrating the system?

Results will be visualized via an **interactive map overlay interface**, making recommendations immediately actionable.

## Methods


We apply core ML algorithms from the course syllabus to natural language text data:

- **Sentence Embeddings** — Convert unstructured review texts into dense numerical feature vectors using a pre-trained model.
- **PCA (Dimensionality Reduction)** — Explore and simplify the high-dimensional embedding space.
- **K-Means Clustering / GMM (Unsupervised Learning)** — Group semantically similar restaurants into latent categories (e.g., "quiet date spots").
- **Cosine Similarity** — Retrieve relevant reviews/restaurants by measuring distance between embedded queries and reviews.
- **Aspect-Level Sentiment & Feature Weighting** — Extract sub-topics (service, food, ambience) and adjust weights based on user preferences.
- **Content-Based Filtering** — Maintain a dynamic "user embedding" built from prior positive queries.
- **Online Learning** — Update the user profile using post-visit feedback to continuously improve recommendations.
- **Logistic Regression (Supervised Ranking)** — Combine text similarity, aspect weights, historical relevance, and star ratings to rank final results.

## Setup
 
This project uses `uv` for dependency management. To set up the local environment:
 
1. **Install `uv`** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **Create a virtual environment**:
   ```bash
   uv venv
   ```
3. **Activate the environment**:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
4. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```
 
## Data Download Instructions

The raw dataset used for this project (Google Local Reviews) is extremely large and therefore not tracked or uploaded through Git. Instead, you will need to download it directly.

1. Navigate to the UCSD public dataset repository: [Google Local Reviews](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/)
2. Download the desired state or category review JSON files (e.g. in our project, we use `review-New_York_10.json.gz`(New York 10-core) and `meta-New_York.json.gz`).
3. Place the downloaded files directly into the `data/raw/` directory in this repository.
5. **Run Data Processing**:
   ```bash
   python src/1_data_processing.py
   ```
   
   **Processing Pipeline Details:**
   - **Borough Filtering**: Identifies NYC-specific restaurants and maps them to one of the 5 boroughs.
   - **Status Filtering**: Automatically excludes any businesses marked as `"Permanently closed"` in the Google metadata.
   - **Fault-Tolerant Extraction**: Uses line-based checkpointing (`review_processing_checkpoint.json`). If interrupted, the script resumes from the exact position in the multi-gigabyte raw JSON file.
   - **Strict Language Filter**: 
     - Extracts English text from `(Translated by Google)` blocks.
     - **Discards ANY review containing native Chinese/CJK characters** that haven't been translated, ensuring the embedding model only sees high-quality English text.
   - **Semantic Downsampling**: Instead of taking the first 500 reviews, it sorts all valid reviews by **text length (detail)** and keeps the top 500 most descriptive reviews per restaurant.
   - **Dynamic Threshold**: Currently set to keep restaurants with at least **15 valid English reviews**.
   
   The output is saved to `data/processed/meta-NYC-restaurant.parquet` and `data/processed/review-NYC-restaurant-filtered.parquet`.

## Generating Embeddings

After downloading and processing the raw data, the next step is converting textual metadata and reviews into dense numerical vectors for semantic search.

1. **Run the Embedding Script**:
   ```bash
   python src/2_embedding.py
   ```

   **Embedding Pipeline Details:**
   - **Model**: [nomic-ai/nomic-embed-text-v1.5](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5).
   - **Memory Management**: Uses `np.memmap` to write embeddings directly to disk, allowing millions of reviews to be processed without OOM errors.
   - **Resumability**: Includes a JSON checkpointing system to resume from specific chunks if interrupted.
   - **Filtering & Downsampling**:
     - *Minimum filter*: Excludes inactive restaurants with $\le 15$ valid English reviews.
     - *Maximum limit*: Caps highly-reviewed restaurants to the top `500` most detailed reviews per restaurant to balance the dataset footprint.
   - **Hardware Acceleration**: Automatically detects and leverages **CUDA** (remote) or **Apple Silicon (`mps`)** GPUs.

## Full Pipeline Orchestration

For a complete end-to-end run (Processing → Embedding → PCA → Clustering), use the provided unified script:

```bash
./run_pipeline.sh
```
This script is optimized for the **Lightning AI** remote environment and manages all environment variables and log redirection to `pipeline.log`.

## Merging Sharded Embeddings

Because `review_embeddings.npy` can exceed GitHub single-file limits, review embeddings may be uploaded as shard files such as:

- `data/processed/review_embeddings.part00.npy`
- `data/processed/review_embeddings.part01.npy`
- `data/processed/review_embeddings.part02.npy`

To merge them back into one file locally:

```bash
python scripts/merge_embedding_shards.py --input-dir data/processed --prefix review_embeddings.part --output review_embeddings.npy
```

After running, merged output will be created at:

- `data/processed/review_embeddings.npy`

## Semantic Search (Initial Test on Full Embeddings)

With the embeddings generated, we first tested semantic search directly on the full 768-dimensional vectors. This step filters the review dataset and runs cosine similarity between a user query and every review embedding.

1. **Filter Parquet Data**:
   ```bash
   python src/1_data_processing.py
   ```
2. **Run Search Query on Full Embeddings**:
   ```bash
   python src/3_search_test_embedding.py
   ```
   You can modify the query inside `3_search_test_embedding.py` to try different searches.

While this produced correct results, operating on the full 768-d vectors across our dataset of ~3.7 million reviews was **extremely expensive**. The full embedding matrix (~5.4 GB) cannot be loaded entirely into RAM, so the search script uses memory-mapped files and processes similarity computation in batches (chunks of 50,000 reviews at a time), writing intermediate scores to disk-backed temporary storage. This results in significantly longer query times and heavy I/O overhead. This motivated the next step: dimensionality reduction via PCA.

## PCA Dimensionality Reduction

To address the high computational cost and memory demands of searching over full 768-dimensional embeddings, we apply **Incremental PCA** to reduce the vectors to 128 dimensions. This approach allows us to process the massive embedding matrices in chunks without loading the full 10GB+ dataset into RAM.

Run the PCA script after generating or merging the embeddings:

```bash
python src/4_pca.py
```

**Configuration** (edit constants at the top of `src/4_pca.py`):

| Parameter | Default | Description |
|---|---|---|
| `N_COMPONENTS` | `128` | Target dimensionality after reduction |
| `CHUNK_SIZE` | `100,000` | Rows transformed per batch (controls peak RAM) |

**Output files** (saved to `data/processed/`):

| File | Description |
|---|---|
| `review_embeddings_pca.npy` | PCA-reduced review embeddings (N × 128) |
| `meta_embeddings_pca.npy` | PCA-reduced metadata embeddings (M × 128) |
| `pca_model.pkl` | Fitted `IncrementalPCA` model |

The fitted PCA model (`pca_model.pkl`) is saved so that **new queries can be projected into the same reduced space** at search time. The script prints the total explained variance retained after reduction to verify that the compressed representation still captures the essential semantic information.

## PCA Component-Count Evaluation

To choose the optimal number of PCA components, we ran a systematic evaluation across **7 candidate values** (16, 32, 64, 128, 256, 384, 512). For each configuration the script:

1. Fits PCA on the full 3.7M review embeddings.
2. Runs 5 diverse benchmark queries in both the full 768-d space (baseline) and the PCA-reduced space.
3. Measures **recall@10** (fraction of baseline top-10 restaurants recovered), **query latency**, and **explained variance**.

```bash
python src/4a_pca_evaluation.py
```

| n_components | Explained Var | Recall@10 | Speedup | Size | Composite |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 16 | 58.3% | 10% | 194× | 229 MB | 0.452 |
| 32 | 66.1% | 22% | 160× | 457 MB | 0.515 |
| 64 | 74.9% | 38% | 151× | 915 MB | 0.595 |
| **128** | **84.4%** | **54%** | **99×** | **1.8 GB** | **0.657** |
| 256 | 93.5% | 48% | 50× | 3.7 GB | 0.555 |
| 384 | 97.5% | 48% | 34× | 5.5 GB | 0.488 |
| 512 | 99.2% | 50% | 20× | 7.3 GB | 0.433 |

**Result:** `n_components = 128` achieves the best tradeoff — **84.4%** explained variance, the highest recall (**54%**), a **99× speedup** (0.6 s vs 60.6 s per query), and an **83% size reduction** (1.8 GB vs 10.9 GB). Notably, recall *peaks* at 128 and decreases for higher component counts, suggesting that moderate PCA regularization filters out noise in the embedding space.

Detailed results and tradeoff plots are saved to `results/`:
- `pca_evaluation_results.csv` / `.json` — full metrics table.
- `pca_tradeoff_analysis.png` — four-panel chart (explained variance, accuracy vs. compression, latency, composite score).
- `pca_scree_curve.png` — cumulative explained variance elbow curve.

## Semantic Search

With embeddings and PCA in place, the semantic search module (`src/7_similarity.py`) provides four search functions:

| Function | Description | Speed |
|---|---|---|
| `search()` | Full search across all 3.7M reviews, chunked to avoid RAM overflow | Slowest |
| `search_within_clusters()` | Filters to relevant clusters first, then searches full 768-dim embeddings | ~10x faster |
| `search_pca()` | Searches all reviews using PCA-reduced 128-dim embeddings | ~99x faster |
| `search_pca_within_clusters()` | Cluster filtering + PCA-reduced search — recommended | Fastest |

All functions take a natural language query string and return a dataframe with:
`name`, `avg_similarity`, `avg_rating`, `borough`, `latitude`, `longitude`, `gmap_id`

### Required Files
- `data/processed/review-NYC-restaurant-filtered.parquet` — filtered reviews (run `scripts/1_data_processing.py`)
- `data/processed/review_embeddings_pca.npy` — PCA-reduced embeddings (run `src/4_pca.py`)
- `data/processed/pca_model.pkl` — fitted PCA model (run `src/4_pca.py`)
- `results/clustering/cluster_centroids.npy` — cluster centroids (run `src/6_clustering.py`)
- `results/clustering/restaurant_clusters.csv` — cluster assignments (run `src/6_clustering.py`)

### Example Usage
```python
import pandas as pd
import numpy as np
from src.7_similarity import load_model, load_pca_model, search_pca_within_clusters

reviews = pd.read_parquet('data/processed/review-NYC-restaurant-filtered.parquet')
meta = pd.read_parquet('data/processed/meta-NYC-restaurant.parquet')
embeddings_pca = np.load('data/processed/review_embeddings_pca.npy', mmap_mode='r')
pca = load_pca_model('data/processed/pca_model.pkl')
centroids = np.load('results/clustering/cluster_centroids.npy')
clusters = pd.read_csv('results/clustering/restaurant_clusters.csv')

model = load_model()
results = search_pca_within_clusters(
    'cozy italian restaurant for a date night',
    model, pca, embeddings_pca, reviews, meta, centroids, clusters
)
print(results)
```

## Clustering

To enable efficient semantic search and restaurant grouping, we applied K-Means clustering on a combined feature representation of each restaurant.

### Feature Construction

Each restaurant is represented by a **combined feature vector**:
- **Meta embedding**: 768-dimensional nomic-embed-text-v1.5 vector from restaurant metadata
- **TF-IDF review keywords**: extracted from aggregated user reviews per restaurant

TF-IDF hyperparameters (optimized through systematic evaluation):

| Parameter | Value | Reason |
|---|---|---|
| `max_features` | 500 | Keep top 500 most informative terms |
| `min_df` | 5 | Term must appear in at least 5 restaurants |
| `max_df` | 0.3 | Filter terms appearing in >30% of restaurants |
| `ngram_range` | (1, 2) | Capture phrases like "fried chicken", "bubble tea" |
| `stop_words` | English + custom | Remove generic words: good, great, nice, delicious, amazing, excellent, bad, food, place, restaurant, came, got, went, time, really, just, ordered, staff, service, definitely |

Both feature sets are L2-normalized and concatenated, then reduced to **100 dimensions via PCA** before clustering.

### Experiment & Model Selection

We ran a full grid search across 4 schemes × 9 k values:
- **Schemes**: meta+kmeans, meta+gmm, combined+kmeans, combined+gmm
- **k values**: [5, 8, 10, 15, 20, 25, 30, 40, 50]
- **Evaluation metric**: Silhouette Score (sampled 3,000 restaurants)

**Results summary:**

| Scheme | Best k | Silhouette Score |
|---|---|---|
| meta+kmeans | 40 | 0.1128 |
| meta+gmm | 50 | 0.0985 |
| combined+gmm | 50 | 0.2241 |
| **combined+kmeans** | **50** | **0.2691** |

**Selected model: combined+kmeans, k=50**
- Silhouette score: **0.2691** (+82% vs initial TF-IDF parameters)
- Optimized TF-IDF parameters significantly improved cluster quality by removing generic evaluation words and enabling bigram features

### Running Clustering
```bash
python src/6_clustering.py
```

### Output Files

All clustering outputs are saved to `results/clustering/`:

| File | Description |
|---|---|
| `restaurant_clusters.csv` | Cluster label (0–49) for each restaurant, with name, borough, coordinates, avg_rating |
| `cluster_summary.json` | Per-cluster summary: size, avg_rating, top_borough, top 10 TF-IDF keywords, sample restaurants |
| `cluster_centroids.npy` | Shape (50, 768) — mean meta embedding vector per cluster, used by semantic search for fast cluster matching |
| `clustering_scores.csv` | Silhouette scores for all 36 experiments |
| `cluster_visualization.html` | Interactive 2D scatter plot (PCA), hover shows restaurant name, cluster, keywords, borough |
| `silhouette_vs_k.png` | Silhouette score vs k curve for all schemes |
| `best_cluster_distribution.png` | Cluster size distribution for the winning model |
| `cluster_comparison_umap.png` | UMAP visualization comparing clustering schemes |

### How Clustering Enables Efficient Search

At query time, the user's input is first matched to its nearest cluster centroid (using `cluster_centroids.npy`), then similarity search is conducted **only within that cluster** — reducing the search space by ~50× compared to full-corpus search.

## Semantic Search (PCA-Reduced)

With PCA-reduced embeddings in place, run the final search pipeline:

1. **Filter Parquet Data** (if not already done above):
   ```bash
   python src/1_data_processing.py
   ```
2. **Run Search Query on PCA Embeddings**:
   ```bash
   python src/5_search_test_pca.py
   ```
   Modify the query inside `5_search_test_pca.py` to try different searches. The script loads the saved PCA model, projects the query embedding into the reduced space, and then computes cosine similarity against the PCA-reduced review embeddings.

Compared to the full-embedding search, the PCA-based search is significantly faster and uses a fraction of the memory, making it practical for iterative experimentation and real-time queries.

## Ranking & ABSA

Layers 2–3 of the recommendation pipeline: aspect-based sentiment scoring and personalised re-ranking of the candidates returned by semantic search.

### Architecture

```
Layer 1  src/7_similarity.py          → top-100 candidate restaurants (semantic search)
Layer 2  src/ranking/absa.py        → per-restaurant aspect scores (offline precompute)
Layer 3  src/ranking/__init__.py    → final_score = α·avg_rating_norm
                                                   + β·aspect_weighted_norm
                                                   + γ·log(1+num_reviews)_norm
```

All ranking code lives in the `src/ranking/` package:

| File | Description |
|---|---|
| `src/ranking/__init__.py` | `rank_candidates`, `add_price_tier_score`, `sensitivity_analysis` |
| `src/ranking/absa.py` | ABSA precompute, `get_aspect_prefs`, validation helpers |
| `src/ranking/demo_search.py` | Standalone Streamlit search demo |
| `src/ranking/scripts/` | Numbered run scripts (see pipeline below) |

`src/absa.py` is a backward-compatibility shim that re-exports from `src/ranking/absa.py`.

---

### ABSA Score Semantics

Aspect scores are produced by **VADER compound sentiment** on keyword-matched review clauses, then **Bayesian-smoothed** using global priors, and finally **min-max normalized to [0, 1]** within each candidate set at ranking time.

**Score direction:**
- `price` high score → **cheap / good value** (not expensive)
- `wait_time` high score → **short wait** (not crowded/slow)
- `food`, `service` high score → positive sentiment

This means high scores always = user-desirable, so no sign-flip is needed after applying user weights.

---

### Aspect Keywords

Four aspects tracked (`ASPECT_KEYWORDS` in `src/ranking/absa.py`):

| Aspect | Example keywords |
|---|---|
| `food` | pizza, ramen, sushi, burger, taste, flavor, portion, … (42 keywords) |
| `service` | service, staff, waiter, friendly, attentive, rude, helpful, … |
| `price` | cheap, expensive, affordable, value, overpriced, reasonable, … |
| `wait_time` | wait, line, queue, slow, quick, fast, crowded, minutes, … |

`ambience` was removed after human validation showed only 28.6% recall — keyword coverage in review text was insufficient.

Keywords were validated via word-frequency analysis on the full review corpus (Step 0).

---

### Query Intent Parsing

`get_aspect_prefs(query)` infers aspect importance from a natural-language query.

**Design decisions:**
- **Mention = important**: any keyword hit adds `+POSITIVE_BOOST (0.20)` to that aspect's weight. Negation is intentionally ignored — "no long wait" and "fast service" both mean the user cares about wait time. The ABSA scores already encode direction (high wait_time = short wait), so there is no need to detect whether the user wants more or less of each aspect.
- **Default weights** (used when no keywords detected):

| Aspect | Default weight |
|---|---|
| `food` | 0.40 |
| `service` | 0.30 |
| `price` | 0.20 |
| `wait_time` | 0.10 |

---

### Per-Aspect Normalization

Before computing `aspect_weighted = Σ user_pref[aspect] × score[aspect]`, each aspect is **independently min-max normalized within the candidate set**. This ensures that different baseline means across aspects (e.g. `wait_time` is systematically lower due to negativity bias in reviews, `price` is higher after tier blending) do not distort the effect of user weights. Without this step, setting a high `wait_time` weight would have less effect than the same weight on `price`, because the raw score ranges differ.

---

### Google Maps Price Tier Fusion

In addition to ABSA price sentiment, we fuse the Google Maps price tier (`$`/`$$`/`$$$`/`$$$$`) into the `price` dimension:

| Tier | Score |
|---|---|
| `$` | 1.0 |
| `$$` | 0.75 |
| `$$$` | 0.25 |
| `$$$$` | 0.0 |
| missing | 0.5 (neutral) |

The final price score is: `0.5 × absa_price_normalized + 0.5 × tier_score`

This ensures that cheap restaurants get a price bonus even when reviewers don't explicitly mention cost — common for budget restaurants where customers already expect low prices and don't comment on them.

---

### Ranking Formula

```
final_score = α × avg_rating_norm
            + β × aspect_weighted_norm
            + γ × log(1 + num_reviews)_norm
```

**Baseline weights** (selected via sensitivity analysis):

| Parameter | Value | Role |
|---|---|---|
| α | 0.4 | Google rating signal |
| β | 0.5 | Aspect-weighted ABSA score |
| γ | 0.1 | Review count (popularity) |

All three components are independently min-max normalized within the candidate set before combining. The `demo_search.py` UI auto-normalizes α/β/γ if the user adjusts them, so they don't need to sum to 1 manually.

---

### Four-Batch Execution Pipeline

The ranking system was built and validated in four human-gated batches:

```
Batch 1 ──────────────────────────────────────────────────────────
  ①  Build all functions (Steps 0–5 code in src/ranking/)
  ②  Run frequency_analysis() → inspect word counts
      ↓
      [Human] Review frequency output → decide ASPECT_KEYWORDS updates

Batch 2 ──────────────────────────────────────────────────────────
  ③  Run precompute_all_aspect_scores() with updated keywords
      → data/processed/aspect_scores.parquet  (~1–2 h, 21,296 restaurants)
  ④  Sample 100 sentences → data/validation/sample_sentences.csv
      ↓
      [Human] Manually label 'aspects' column (before viewing system output
               to avoid confirmation bias)

Batch 3 ──────────────────────────────────────────────────────────
  ⑤  validate_absa_accuracy() + validate_query_detection()
  ⑥  sensitivity_analysis() → α/β/γ comparison table
      → results/sensitivity_analysis.csv
      ↓
      [Human] Choose α/β/γ combination

Batch 4 ──────────────────────────────────────────────────────────
  ⑦  Run demo with selected weights → top-5 per query
      → results/sensitivity_latest_blind.csv  (weight_set hidden)
      ↓
      [Human] Score results 0/1/2 (relevance to query + aspect match)
  ⑧  Compute per-weight-set average → final report
```

Run scripts in order from the project root:

```bash
python src/ranking/scripts/step0_frequency_analysis.py
python src/ranking/scripts/step1_precompute.py
python src/ranking/scripts/step2_validation.py
python src/ranking/scripts/step3_sensitivity_demo.py
```

---

### Interactive Search Demo

```bash
streamlit run src/ranking/demo_search.py
```

Features:
- Natural-language query → semantic search → top-100 candidates
- Auto-detected aspect preferences displayed as adjustable sliders (food / service / price / wait time)
- α / β / γ ranking weight expander (auto-normalized)
- Results shown on map + sortable table with price tier (`$`/`$$`) column
- Every new search resets all sliders to auto-detected values

---

### Output Files

| File | Description |
|---|---|
| `data/processed/aspect_scores.parquet` | Per-restaurant ABSA scores (Batch 2 output) |
| `data/validation/sample_sentences.csv` | 100 sentences for manual annotation |
| `data/validation/sample_sentences_labeled.csv` | Human-labeled annotation file |
| `results/sensitivity_analysis.csv` | α/β/γ grid search results |
| `results/sensitivity_latest.csv` | Per-query top-5 with weight_set labels |
| `results/sensitivity_latest_blind.csv` | Blind version for human scoring |

## 🍕 NYC Restaurant Explorer: Interactive Map（Frame, more functions coming...）
1. Features
- **Interactive Map** — Restaurants are plotted on a Mapbox map using latitude/longitude coordinates, color-coded by cluster category using a discrete color palette.
- **Cluster Filter** — A sidebar multiselect control lets users choose which restaurant clusters to display. Clusters are sorted numerically, and the first 5 are shown by default to reduce initial load time.
- **Rating Filter** — A sidebar slider lets users set a minimum average rating (1.0–5.0, default 3.5), filtering out lower-rated restaurants.
- **Restaurant Count** — The sidebar dynamically shows the total number of restaurants matching the current filters.
- **Two-Column Layout** — The main view is split into a map panel (left, 2/3 width) and a sortable restaurant details list (right, 1/3 width), displaying name, borough, average rating, and cluster.
- **Hover Details** — Hovering over a map point shows the restaurant name, cluster ID, average rating, and borough.
- **Smart Recommendation Placeholder** — A section at the bottom of the page previews a planned similarity-based recommendation feature using embedding vectors.

2.  Requirements

- Python 3.8+
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly](https://plotly.com/python/)

Install dependencies with:

```bash
pip install streamlit pandas plotly
```

---

3. Data Requirements

The app expects a CSV file at the following path:

```
results/clustering/restaurant_clusters.csv
```

The CSV must contain at least these columns:

| Column | Description |
|---|---|
| `latitude` | Restaurant latitude coordinate |
| `longitude` | Restaurant longitude coordinate |
| `cluster` | Integer cluster ID assigned by the clustering model |
| `name` | Restaurant name |
| `avg_rating` | Average user rating (1.0–5.0) |
| `borough` | NYC borough (e.g., Manhattan, Brooklyn) |

Rows with missing `latitude` or `longitude` values are automatically dropped on load.

---

4.  How to Open

From the project root directory, run:

```bash
streamlit run src/app.py
```
The app will open in your browser at `http://localhost:8501` by default.

5. API Notes

The following Plotly/Streamlit deprecations have been resolved in `src/app.py`:

- `px.scatter_mapbox` → `px.scatter_map` (Plotly MapLibre migration)
- `mapbox_style` → `map_style` in `fig.update_layout()`
- `use_container_width=True` → `width='stretch'` (Streamlit, removed after 2025-12-31)

6. Planned Features
- **Similarity-Based Recommendations** — Input a restaurant you like and find the most similar ones using embedding vector search.
## Repo Structure

```
ml-restaurant-recommendation/
├── README.md
├── requirements.txt
├── CLAUDE.md                  # AI assistant instructions for this project
├── scripts/                   # Non-ranking utility scripts
├── documents/
│   ├── writtenProposal.md
│   ├── designDocument.md
│   ├── dataDocumentation.md
│   ├── brainstorming.md
│   └── ranking_plan_final.md  # Detailed ranking pipeline design document
├── data/                      # Not tracked in git
│   ├── raw/                   # Raw Google Local Reviews JSON files
│   ├── processed/             # Cleaned data and precomputed artifacts
│   │   ├── review-NYC-restaurant-filtered.parquet
│   │   ├── meta-NYC-restaurant.parquet
│   │   ├── review_embeddings_pca.npy      # PCA-reduced review embeddings (N × 128)
│   │   ├── pca_model.pkl                  # Fitted PCA model
│   │   ├── aspect_scores.parquet          # ABSA aspect scores per restaurant
│   │   ├── word_frequency_top500.csv      # Top-500 word frequencies (Step 0 output)
│   │   └── aspect_keyword_frequency.csv   # Per-keyword frequency check
│   └── validation/
│       ├── sample_sentences.csv           # 100 sentences for manual annotation
│       └── sample_sentences_labeled.csv   # Human-labeled aspects
├── notebooks/
│   ├── exploration.ipynb
│   └── clustering_analysis.ipynb
├── src/
│   ├── 1_data_processing.py   # Data loading, cleaning, filtering, borough assignment
│   ├── 2_embedding.py         # Sentence embedding generation (nomic-embed-text-v1.5)
│   ├── 3_search_test_embedding.py  # Semantic search on full 768-d embeddings (baseline)
│   ├── 4_pca.py               # PCA dimensionality reduction (768 → 128)
│   ├── 4a_pca_evaluation.py   # PCA component-count evaluation (recall@10, speedup)
│   ├── 5_search_test_pca.py   # Semantic search on PCA-reduced embeddings
│   ├── 6a_clustering_pca.py   # K-Means clustering (PCA-reduced)
│   ├── 6b_clustering_full.py  # K-Means clustering (Full-dimensional)
│   ├── 7_similarity.py        # Cosine similarity, cluster-aware search, PCA search
│   ├── absa.py                # Shim → re-exports from src/8_ranking/absa.py
│   ├── evaluation.py          # Model evaluation metrics
│   ├── user_profile.py        # User profile management
│   ├── app.py                 # Interactive map explorer (streamlit run src/app.py)
│   └── 8_ranking/             # Ranking & ABSA package
│       ├── __init__.py        # rank_candidates, add_price_tier_score, sensitivity_analysis
│       ├── absa.py            # ABSA precompute, get_aspect_prefs, validation
│       ├── demo_search.py     # Interactive search + ranking demo (streamlit run)
│       └── scripts/           # Run in order from project root
│           ├── step0_frequency_analysis.py  # Validate ASPECT_KEYWORDS vs corpus
│           ├── step1_precompute.py          # Precompute aspect scores (~1–2 h)
│           ├── step2_validation.py          # ABSA accuracy + sensitivity analysis
│           └── step3_sensitivity_demo.py    # Compare α/β/γ weight sets
└── results/
    ├── clustering/
    │   ├── restaurant_clusters.csv        # Cluster label (0–49) per restaurant
    │   ├── cluster_summary.json           # Per-cluster keywords and stats
    │   ├── cluster_centroids.npy          # Mean meta embedding per cluster (50, 768)
    │   ├── clustering_scores.csv          # Silhouette scores for all 36 experiments
    │   ├── cluster_visualization.html     # Interactive 2D UMAP scatter plot
    │   └── …
    ├── sensitivity_analysis.csv           # α/β/γ grid search results
    ├── sensitivity_latest.csv             # Per-query top-5 with weight labels
    ├── sensitivity_latest_blind.csv       # Blind version for human scoring
    └── review_analysis_report.csv
```
