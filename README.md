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
   - **Truncation**: `max_seq_length = 256` tokens (effectively capturing ~200-word reviews). By clipping the model’s default 8192 context window, we massively accelerate computation and prevent OOM errors.
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

## Semantic Search

To test the semantic search capabilities locally, follow these two steps:

1. **Filter Parquet Data**:
   Run the following script to create a filtered version of the dataset required for the search:
   ```bash
   python src/2_filter_reivews.py
   ```

2. **Run Search Query**:
   Execute the search test script. You can modify the query inside `3_search_test.py` directly to try different searches against the processed data:
   ```bash
   python src/3_search_test.py
   ```

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
├── notebooks/                 # Jupyter notebooks for exploration and analysis
│   └── exploration.ipynb      # Initial data exploration notebook
├── src/                       # Source code modules
│   ├── 0_data_processing.py   # Data loading, cleaning, and preprocessing
│   ├── 1_embedding.py         # Sentence embedding generation
│   ├── 2_filter_reivews.py    # Filter review datasets
│   ├── 3_search_test.py       # Local testing for semantic similarities
│   ├── clustering.py          # K-Means / GMM clustering
│   ├── similarity.py          # Cosine similarity and retrieval
│   ├── ranking.py             # Supervised ranking model (logistic regression)
│   ├── user_profile.py        # User profile and preference management
│   ├── evaluation.py          # Model evaluation metrics and utilities
│   └── app.py                 # Interactive application / map overlay interface
└── results/                   # Output results, figures, and model artifacts
```
