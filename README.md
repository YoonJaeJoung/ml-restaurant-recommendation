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
5. **Install Git LFS** (required for large data files):
   - Install Git LFS: `brew install git-lfs`
   - Initialize in repo: `git lfs install`
   - Pull large files: `git lfs pull`
 
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
   - **ZIP-Prefix Guard**: Requires the address to end with a 5-digit ZIP whose first three digits belong to NYC (`100/101/102/103/104/110/111/112/113/114/116`). Necessary because several NYC neighborhood names also appear upstate (e.g. Clinton NY 13323, Red Hook NY 12571, Schuylerville NY 12871), so the neighborhood-name match alone would leak non-NYC restaurants. The current meta parquet and review embeddings on disk predate this guard — `src/7_similarity.py` applies the same ZIP filter at query time so stale artifacts still return NYC-only results.
   - **Status Filtering**: Automatically excludes any businesses marked as `"Permanently closed"` in the Google metadata.
   - **Fault-Tolerant Extraction**: Uses line-based checkpointing (`review_processing_checkpoint.json`). If interrupted, the script resumes from the exact position in the multi-gigabyte raw JSON file.
   - **Strict Language Filter**: 
     - Extracts English text from `(Translated by Google)` blocks.
     - **Discards ANY review containing native Chinese/CJK characters** that haven't been translated, ensuring the embedding model only sees high-quality English text.
   - **Semantic Downsampling**: Instead of taking the first 500 reviews, it sorts all valid reviews by **text length (detail)** and keeps the top 500 most descriptive reviews per restaurant.
   - **Dynamic Threshold**: Currently set to keep restaurants with at least **15 valid English reviews**.
   
   The output is saved to `data/processed/meta-NYC-restaurant.parquet` and `data/processed/review-NYC-restaurant-filtered.parquet`.

   > [!IMPORTANT]
   > **Data Versioning Notice**: Most processed artifacts (Parquets, PCA embeddings) are tracked in this repository using **Git LFS**. However, the following are **EXCLUDED** from version control due to extreme size:
   > - `data/raw/` (Raw JSON sources)
   > - `data/processed/review_embeddings.npy` (6.2GB Full Embedding Matrix)

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

## Downloading Raw Embeddings

If you do not wish to generate the embeddings locally (which can take several hours), you can download the pre-computed raw embedding package:

1. **Download the ZIP**: [NYC Restaurant Raw Embeddings](https://drive.google.com/file/d/1frL_0ib3iFE0BrlnChL4p-q0me90Pk4x/view?usp=share_link)
2. **Setup**: Unzip the contents (`review_embeddings.npy` and `meta_embeddings.npy`) into the `data/processed/` directory.

> [!IMPORTANT]
> **Production Note**: These raw 768-dimensional embeddings are only required if you intend to re-run the PCA evaluation or high-precision similarity tests. The **final production search engine** and **interactive map** operate exclusively on the PCA-reduced artifacts tracked via Git LFS and **do not require** these 6GB raw files to function.

## Semantic Search (Initial Test on Full Embeddings)

With the embeddings generated (or downloaded), we first tested semantic search directly on the full 768-dimensional vectors. This step filters the review dataset and runs cosine similarity between a user query and every review embedding.

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

**Output files** (saved to `results/pca/`):

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
| **128** | **75.5%** | **54%** | **99×** | **1.8 GB** | **0.657** |
| 256 | 93.5% | 48% | 50× | 3.7 GB | 0.555 |
| 384 | 97.5% | 48% | 34× | 5.5 GB | 0.488 |
| 512 | 99.2% | 50% | 20× | 7.3 GB | 0.433 |

**Result:** `n_components = 128` achieves the best tradeoff — **75.5%** explained variance, the highest recall (**54%**), a **99× speedup** (0.6 s vs 60.6 s per query), and an **83% size reduction** (1.8 GB vs 10.9 GB). Notably, recall *peaks* at 128 and decreases for higher component counts, suggesting that moderate PCA regularization filters out noise in the embedding space.

Detailed results and tradeoff plots are saved to `results/pca/evaluation/`:
- `pca_evaluation_results.csv` / `.json` — full metrics table.
- `pca_tradeoff_analysis.png` — four-panel chart (explained variance, accuracy vs. compression, latency, composite score).
- `pca_scree_curve.png` — cumulative explained variance elbow curve.

### Final Production Evaluation (Cleaned Dataset)

**Date**: 2026-04-20
**Hardware**: NVIDIA Tesla T4 GPU (Lightning AI)
**Framework**: RAPIDS cuML (GPU-Accelerated PCA)

#### Cleaning & Filtering Parameters
To ensure highest recommendation quality for NYC restaurants, the following filters were applied to the **final production dataset**:
- **Language Filtering**: Removed CJK (Chinese/Japanese/Korean) characters from reviews for semantic consistency.
- **Museum/Status Filtering**: Excluded "Permanently closed" establishments.
- **Engagement Threshold**: Standardized on **min 15 reviews** per restaurant (Total: **19,532** restaurants).

#### Performance Benchmarks (Full 2.15M Reviews)
Evaluation performed using the T4 GPU on the full 2.15 million review set.

| n_components | Explained Var | Recall@10 | Speedup | Size |
|:---:|:---:|:---:|:---:|:---:|
| 16 | 35.4% | 0% | 15.6x | 132 MB |
| 32 | 47.2% | 6% | 8.4x | 263 MB |
| 64 | 60.9% | 30% | 5.9x | 527 MB |
| **128** | **75.8%** | **44%** | **3.2x** | **1.1 GB** |
| **256** | **89.9%** | **56%** | **1.2x** | **2.1 GB** |
| 384 | 96.2% | 66% | 0.7x | 3.2 GB |
| 512 | 98.8% | 68% | 0.2x | 4.2 GB |

**Analysis**:
- **Semantic Coverage**: 128 components capture **75.8%** of the variance in the production database. 
- **Efficiency**: GPU mapping of 2 million rows now takes only **20.6s**, enabling rapid iteration on the full Google Maps NYC dataset.
- **Sweet Spot**: `n_components=256` provides the best recall-to-size tradeoff on the full data, while `128` remains the most efficient for low-latency production use.

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

All secondary clustering artifacts are saved to `results/clustering/evaluation/`:

| File | Description |
|---|---|
| `cluster_summary.json` | Per-cluster summary: keywords and stats |
| `clustering_scores.csv` | Silhouette scores for all experiments |
| `silhouette_vs_k.png` | Performance tradeoff plots |
| `cluster_size_dist.png` | Cluster distribution bar chart |
| `wordclouds/` | Folder containing WordCloud PNGs for all 50 clusters |
| `cluster_map.html` | Interactive Plotly map of all clusters |
| `cluster_comparison_umap.png` | UMAP visualization comparing clustering schemes |

### How Clustering Enables Efficient Search

At query time, the user's input is first matched to its nearest cluster centroid (using `cluster_centroids.npy`), then similarity search is conducted **only within that cluster** — reducing the search space by ~50× compared to full-corpus search.

## Semantic Search (Cluster-Based)

With embeddings, PCA, and Clustering in place, the production search engine (`src/7_similarity.py`) provides an interactive interface for querying the entire NYC database.

### Running the Search Engine
You can launch the interactive search CLI to ask natural language queries (e.g., "secret italian spot in Soho"):
```bash
python src/7_similarity.py
```
The CLI will target relevant clusters first and then perform high-speed PCA-reduced search within them.

### Algorithm Performance
The module provides four variants of the search algorithm:

| Function | Description | Speed |
|---|---|---|
| `search()` | Full search across all 2.1M reviews, chunked to avoid RAM overflow | Slowest |
| `search_within_clusters()` | Filters to relevant clusters first, then searches full 768-dim embeddings | ~10x faster |
| `search_pca()` | Searches all reviews using PCA-reduced 128-dim embeddings | ~99x faster |
| `search_pca_within_clusters()` | Cluster filtering + PCA-reduced search — recommended | Fastest |

All functions return detailed restaurant cards including names, similarity match, ratings, borough, descriptions, and clickable Google Maps links.

### Example Usage (Programmatic)
```python
import pandas as pd
import numpy as np
from src.7_similarity import load_model, load_pca_model, search_pca_within_clusters

reviews = pd.read_parquet('data/processed/review-NYC-restaurant-filtered.parquet')
meta = pd.read_parquet('data/processed/meta-NYC-restaurant.parquet')
embeddings_pca = np.load('results/pca/review_embeddings_pca.npy', mmap_mode='r')
pca = load_pca_model('results/pca/pca_model.pkl')
centroids = np.load('results/clustering/cluster_centroids.npy')
clusters = pd.read_csv('results/clustering/restaurant_clusters.csv')

model = load_model()
results, best_clusters = search_pca_within_clusters(
    'cozy italian restaurant for a date night',
    model, pca, embeddings_pca, reviews, meta, centroids, clusters
)
print(results)
```

## Ranking & ABSA

Layers 2–3 of the recommendation pipeline: aspect-based sentiment scoring (precomputed offline, stored directly in the meta parquet) and personalised re-ranking at query time.

### Architecture

```
Layer 1  src/7_similarity.py          → top-N candidates (cluster-aware PCA semantic search)
Layer 2  src/8_ranking.py             → offline ABSA precompute (writes 4 columns into meta parquet)
Layer 3  src/ranking.py               → query-time ranker:
                                         final = α · rating/5
                                               + β · aspect_weighted (price blended with $$ tier)
                                               + γ · log1p(reviews) / global_max
Layer 4  src/9_search_test_ranking.py → CLI that ties Layer 1 + 3 together for testing
```

Files (flat, under `src/`):

| File | Role |
|---|---|
| `src/absa.py` | Importable ABSA library: keyword tables, `get_aspect_prefs`, `precompute_all_aspect_scores`, validation helpers |
| `src/similarity.py` | `importlib` wrapper around `src/7_similarity.py` so other code can `from src.similarity import ...` despite the digit-prefix filename |
| `src/ranking.py` | Importable ranker: `rank_candidates`, `tier_to_score`, normalization helpers |
| `src/8_ranking.py` | Standalone CLI — runs `precompute_all_aspect_scores` end-to-end and writes back into `data/processed/meta-NYC-restaurant.parquet` |
| `src/9_search_test_ranking.py` | Interactive terminal CLI that runs the full search + rank pipeline |
| `src/10_query_construction.py` | CLI that builds a query string from 4 toggle questions |

### ABSA Score Semantics

Aspect scores are produced by **VADER compound sentiment** on keyword-matched review clauses, then **Bayesian-smoothed** using global priors, and finally **globally min-max normalized to [0, 1]** across the ~19.5k restaurants that pass the ≥15-review filter. The globally-normalized scores are written into the meta parquet as four new columns: `aspect_food`, `aspect_service`, `aspect_price`, `aspect_wait_time`.

Global (not per-candidate) normalization is used so the stored scores are stable per restaurant, comparable across queries, and interpretable as absolute positions within the dataset.

**Score direction:**
- `aspect_price` high → **cheap / good value**
- `aspect_wait_time` high → **short wait**
- `aspect_food`, `aspect_service` high → positive sentiment

High score always means "user-desirable" — no sign flips needed.

Restaurants with fewer than 15 reviews (not present in the review-filtered parquet) get `NaN` in all four columns.

### Query Intent Parsing

`get_aspect_prefs(query)` infers aspect importance from a natural-language query.

- **Mention = important**: any keyword hit adds `+0.20` to that aspect's weight. Negation is intentionally ignored — "no long wait" and "fast service" both mean the user cares about wait time.
- **Default weights** (used when no keywords detected):

| Aspect | Default weight |
|---|---|
| `food` | 0.40 |
| `service` | 0.30 |
| `price` | 0.20 |
| `wait_time` | 0.10 |

The returned weights are auto-normalized to sum to 1 before being applied.

### Query-Time Ranking Formula

At query time, `src/ranking.py:rank_candidates` computes:

```
aspect_weighted = w_food · aspect_food
                + w_service · aspect_service
                + w_price · (0.5 · aspect_price + 0.5 · tier_score)
                + w_wait_time · aspect_wait_time

final_score = α · (avg_rating / 5)
            + β · aspect_weighted
            + γ · (log1p(num_reviews) / global_max_log1p_reviews)
```

- User weights `w_*` are auto-normalized to sum to 1.
- `tier_score` maps Google Maps `$`/`$$`/`$$$`/`$$$$` → `1.0`/`0.75`/`0.25`/`0.0` (missing → `0.5`). Only the `price` aspect is blended with the tier, and the blend happens at query-time so the raw ABSA price score stays inspectable in the parquet.
- `global_max_log1p_reviews` is cached at startup for cross-query comparability.

**Baseline α/β/γ** (auto-normalized if the caller changes them):

| Parameter | Value | Role |
|---|---|---|
| α | 0.4 | Google rating signal |
| β | 0.5 | Aspect-weighted ABSA score |
| γ | 0.1 | Review count (popularity) |

### Running the Precompute

From project root, inside the venv:

```bash
python src/8_ranking.py
```

This takes ~5 minutes on a laptop and writes four new columns directly into `data/processed/meta-NYC-restaurant.parquet`. Re-running the script is safe — stale aspect columns are dropped and re-computed.

Phase 1 estimates global priors from a 10% sample of restaurants (no smoothing). Phase 2 computes Bayesian-smoothed scores for every restaurant with ≥15 reviews. `groupby` is used to iterate reviews by restaurant in O(n) time.

### Running the CLI Search+Rank Test

```bash
python src/9_search_test_ranking.py
```

Interactive REPL — type a query, see top 10 with each score component, auto-detected aspect preferences, and timing breakdown.

### Output

Four new columns appended to `data/processed/meta-NYC-restaurant.parquet`:

| Column | Range | Description |
|---|---|---|
| `aspect_food` | [0, 1] | Globally-normalized Bayesian-smoothed food sentiment |
| `aspect_service` | [0, 1] | Same, for service |
| `aspect_price` | [0, 1] | Raw (unblended) price sentiment — blending happens at query-time |
| `aspect_wait_time` | [0, 1] | Same, for wait time |

## Web App

A FastAPI backend + Vite / React SPA sit on top of the pipeline and expose
everything as an interactive map-based search — natural-language queries,
filter-by-borough / radius / drawn polygon / viewport, day & time filter,
aspect-based sort, inline detail panel, and a browse-all clustered map view
of the entire qualifying NYC restaurant set.

The backend imports the stable library code from `src/` (`src.absa`,
`src.similarity`, `src.ranking`) but otherwise owns its own routes,
Pydantic schemas, state singleton, and geographic / time filtering. Artifacts
are loaded once at startup and shared across requests. The old
`src/app.py` Streamlit prototype has been superseded.

👉 **See [`app/README.md`](app/README.md) for the full app guide** —
architecture diagram, module-by-module backend breakdown (main, state,
schemas, search, detail, browse, geo, hours, query_builder), frontend
structure (views + components + hooks + api), API spec, design system,
environment setup (Mapbox token), and run / smoke-test commands.

## Repo Structure

```
ml-restaurant-recommendation/
├── README.md
├── requirements.txt
├── CLAUDE.md                        # AI assistant instructions for this project
├── documents/
│   ├── writtenProposal.md
│   ├── designDocument.md
│   ├── dataDocumentation.md
│   ├── brainstorming.md
│   └── ranking_plan_final.md
├── data/                            # Large data artifacts (partially LFS tracked)
│   ├── raw/                         # Raw Google Local Reviews JSON (Excluded)
│   └── processed/                   # Cleaned datasets and precomputed artifacts
│       ├── review-NYC-...-filtered.parquet
│       └── meta-NYC-restaurant.parquet   # Now includes 4 aspect_* columns
├── notebooks/
├── results/
│   ├── pca/                         # Production PCA embeddings & models (LFS)
│   └── clustering/                  # Production cluster assignments + summary json
├── src/                             # ML pipeline (CLI scripts + importable libs)
│   ├── 1_data_processing.py         # CLI: data loading, cleaning, filtering
│   ├── 2_embedding.py               # CLI: sentence embedding generation
│   ├── 4_pca.py                     # CLI: PCA reduction (768 → 128)
│   ├── 4a_pca_evaluation.py         # CLI: PCA component-count evaluation
│   ├── 6c_clustering_evaluation.py  # CLI: consolidated evaluation & viz
│   ├── 7_similarity.py              # CLI: production search engine
│   ├── 8_ranking.py                 # CLI: offline ABSA precompute → meta parquet
│   ├── 9_search_test_ranking.py     # CLI: interactive search + rank REPL
│   ├── 10_query_construction.py     # CLI: 4-toggle query builder
│   ├── absa.py                      # Importable lib: ABSA core + get_aspect_prefs
│   ├── similarity.py                # Importable lib: importlib wrapper for 7_similarity
│   └── ranking.py                   # Importable lib: query-time ranking formula
├── app/                             # Web app — see app/README.md for details
│   ├── README.md                    # Backend + frontend architecture guide
│   ├── backend/                     # FastAPI service (routes, state, search, detail, …)
│   ├── frontend/                    # Vite + React SPA (views, components, hooks, …)
│   └── design sample/               # Early static design mocks
└── .gitattributes                   # Git LFS configuration
```
