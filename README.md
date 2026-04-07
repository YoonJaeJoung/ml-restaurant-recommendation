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
2. Download the desired state or category review JSON files (e.g., `review-New_York.json.gz` and `meta-New_York.json.gz`).
3. Place the downloaded files directly into the `data/raw/` directory in this repository.
4. Run `python src/0_data_processing.py` (ensure your environment is activated) to filter the metadata for NYC restaurants and add borough information. The output will be saved to `data/processed/meta-NYC-restaurant.json.gz`.

## Generating Embeddings

After downloading and processing the raw data, the next step is converting textual metadata and reviews into dense numerical vectors for semantic search.

1. **Run the Embedding Script**:
   ```bash
   python src/1_embedding.py
   ```

   **Embedding Pipeline Details:**
   - **Model**: [nomic-ai/nomic-embed-text-v1.5](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) (utilized for its asymmetric search capabilities: prepending "search_document" to corpus texts).
   - **Truncation**: `max_seq_length = 256` tokens (effectively capturing ~200-word reviews). By clipping the model's default 8192 context window, we massively accelerate computation and prevent OOM errors.
   - **Filtering & Downsampling**:
     - *Minimum filter*: Excludes inactive restaurants with $\le 30$ reviews.
     - *Maximum limit*: Caps highly-reviewed restaurants to an upper bound of `500` reviews to balance the dataset footprint.
   - **Hardware Acceleration**: Automatically detects and leverages Apple Silicon (`mps`) GPU if accessible, which greatly cuts down processing time alongside proper `batch_size` (e.g., 32/64).

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
   python src/2_filter_reivews.py
   ```
2. **Run Search Query on Full Embeddings**:
   ```bash
   python src/3_search_test_embedding.py
   ```
   You can modify the query inside `3_search_test_embedding.py` to try different searches.

While this produced correct results, operating on the full 768-d vectors across our dataset of ~3.7 million reviews was **extremely expensive**. The full embedding matrix (~5.4 GB) cannot be loaded entirely into RAM, so the search script uses memory-mapped files and processes similarity computation in batches (chunks of 50,000 reviews at a time), writing intermediate scores to disk-backed temporary storage. This results in significantly longer query times and heavy I/O overhead. This motivated the next step: dimensionality reduction via PCA.

## PCA Dimensionality Reduction

To address the high computational cost and memory demands of searching over full 768-dimensional embeddings, we applied **PCA (Principal Component Analysis)** to reduce the embedding vectors to a much smaller dimension. This is a **required step** before running the final search pipeline.

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
| `pca_model.pkl` | Fitted `sklearn.decomposition.PCA` model |

The fitted PCA model (`pca_model.pkl`) is saved so that **new queries can be projected into the same reduced space** at search time — no need to re-fit PCA when running the search.

The script prints the total explained variance retained after reduction so you can verify that the compressed representation still captures the essential semantic information.

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

With embeddings and PCA in place, the semantic search module (`src/similarity.py`) provides four search functions:

| Function | Description | Speed |
|---|---|---|
| `search()` | Full search across all 3.7M reviews, chunked to avoid RAM overflow | Slowest |
| `search_within_clusters()` | Filters to relevant clusters first, then searches full 768-dim embeddings | ~10x faster |
| `search_pca()` | Searches all reviews using PCA-reduced 128-dim embeddings | ~99x faster |
| `search_pca_within_clusters()` | Cluster filtering + PCA-reduced search — recommended | Fastest |

All functions take a natural language query string and return a dataframe with:
`name`, `avg_similarity`, `avg_rating`, `borough`, `latitude`, `longitude`, `gmap_id`

### Required Files
- `data/processed/review-NYC-restaurant-filtered.parquet` — filtered reviews (run `scripts/filter_reviews.py`)
- `data/processed/review_embeddings_pca.npy` — PCA-reduced embeddings (run `src/4_pca.py`)
- `data/processed/pca_model.pkl` — fitted PCA model (run `src/4_pca.py`)
- `results/clustering/cluster_centroids.npy` — cluster centroids (run `src/clustering.py`)
- `results/clustering/restaurant_clusters.csv` — cluster assignments (run `src/clustering.py`)

### Example Usage
```python
import pandas as pd
import numpy as np
from src.similarity import load_model, load_pca_model, search_pca_within_clusters

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
python src/clustering.py
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
   python src/2_filter_reivews.py
   ```
2. **Run Search Query on PCA Embeddings**:
   ```bash
   python src/5_search_test_pca.py
   ```
   Modify the query inside `5_search_test_pca.py` to try different searches. The script loads the saved PCA model, projects the query embedding into the reduced space, and then computes cosine similarity against the PCA-reduced review embeddings.

Compared to the full-embedding search, the PCA-based search is significantly faster and uses a fraction of the memory, making it practical for iterative experimentation and real-time queries.

## Interactive Map

## Repo Structure

```
ml-restaurant-recommendation/
├── README.md                  # Project overview and documentation
├── requirements.txt           # Python dependencies
├── scripts/                   # Utility scripts
│   └── merge_embedding_shards.py  # Merge review embedding shards into one .npy
├── documents/                 # Project planning and documentation
│   ├── writtenProposal.md     # Written proposal (problem + methods)
│   ├── designDocument.md      # Design document (structure, labor, stubs)
│   ├── dataDocumentation.md   # Dataset documentation and exploration notes
│   └── brainstorming.md       # Feature and method brainstorming
├── data/                      # Data directory (not tracked in git)
│   ├── raw/                   # Raw data files (e.g., Google Local Reviews JSON)
│   └── processed/             # Cleaned and processed data
│       ├── review_embeddings.npy          # Full 768-d review embeddings
│       ├── meta_embeddings.npy            # Full 768-d metadata embeddings
│       ├── review_embeddings_pca.npy      # PCA-reduced review embeddings
│       ├── meta_embeddings_pca.npy        # PCA-reduced metadata embeddings
│       └── pca_model.pkl                  # Fitted PCA model (for query projection)
├── notebooks/                 # Jupyter notebooks for exploration and analysis
│   ├── exploration.ipynb      # Initial data exploration notebook
│   └── clustering_analysis.ipynb  # Clustering results analysis and visualization
├── src/                       # Source code modules
│   ├── 0_data_processing.py   # Data loading, cleaning, and preprocessing
│   ├── 1_embedding.py         # Sentence embedding generation
│   ├── 2_filter_reivews.py    # Filter review datasets
│   ├── 3_search_test_embedding.py  # Semantic search using full embeddings
│   ├── 4_pca.py               # PCA dimensionality reduction on embeddings
│   ├── 4a_pca_evaluation.py   # PCA component-count evaluation & tradeoff analysis
│   ├── 5_search_test_pca.py   # Semantic search using PCA-reduced embeddings
│   ├── clustering.py          # K-Means / GMM clustering
│   ├── similarity.py          # Cosine similarity and retrieval
│   ├── ranking.py             # Supervised ranking model (logistic regression)
│   ├── user_profile.py        # User profile and preference management
│   ├── evaluation.py          # Model evaluation metrics and utilities
│   └── app.py                 # Interactive application / map overlay interface
└── results/                   # Output results, figures, and model artifacts
    ├── clustering/            # Clustering outputs
    │   ├── restaurant_clusters.csv        # Cluster label for each restaurant
    │   ├── cluster_summary.json           # Per-cluster keywords and statistics
    │   ├── cluster_centroids.npy          # Mean embedding per cluster (50, 768)
    │   ├── clustering_scores.csv          # Silhouette scores for all 36 experiments
    │   ├── clustering_scores_extended.csv # Extended experiment results
    │   ├── cluster_visualization.html     # Interactive 2D scatter plot
    │   ├── silhouette_vs_k.png            # Silhouette score vs k curve
    │   ├── best_cluster_distribution.png  # Cluster size distribution
    │   ├── cluster_comparison_umap.png    # UMAP visualization
    │   └── cluster_rating_size.png        # Cluster rating vs size plot
    └── review_analysis_report.csv         # Review data analysis report
```
