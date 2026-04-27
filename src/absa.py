"""
absa.py
Aspect-Based Sentiment Analysis: offline pre-computation, query intent parsing,
and validation utilities.

Precompute output writes four per-aspect columns
(aspect_food, aspect_service, aspect_price, aspect_wait_time)
directly into data/processed/meta-NYC-restaurant.parquet.
Each column is globally min-max normalized to [0,1] across the restaurants
that pass the ≥15-review filter. Restaurants without reviews get NaN.

Price is stored *unblended* here — blending with the Google Maps tier ($/$$/…)
happens at query-time inside the ranker so it stays transparent.
"""
import re
import numpy as np
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter, defaultdict
from tqdm import tqdm

nltk.download('punkt',    quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet',  quiet=True)

lemmatizer = WordNetLemmatizer()
analyzer   = SentimentIntensityAnalyzer()

# ── Aspect keyword table (update after running frequency_analysis in Step 0) ──
ASPECT_KEYWORDS = {
    "food":      ["food", "dish", "meal", "taste", "flavor",
                  "cuisine", "menu", "portion", "ingredient", "quality",
                  "pizza", "chicken", "coffee", "cheese", "burger", "sauce",
                  "fries", "rice", "salad", "sandwich", "meat", "soup",
                  "sushi", "wine", "steak", "fish", "bread", "pork",
                  "ramen", "tacos", "beef", "wings", "shrimp", "pasta",
                  "dessert", "noodles", "seafood", "dumplings", "bagels", "beer",
                  "drinks", "cocktails"],
    "service":   ["service", "staff", "waiter", "waitress",
                  "server", "host", "bartender", "manager", "employees",
                  "friendly", "attentive", "rude", "helpful"],
    "price":     ["price", "cost", "cheap", "expensive",
                  "affordable", "value", "worth", "overpriced", "reasonable",
                  "pricey", "priced", "money"],
    "wait_time": ["wait", "waiting", "line", "queue", "reservation",
                  "delay", "busy", "packed", "crowded",
                  "hour", "slow", "minutes", "quick", "fast"],
}

LEMMATIZED_KEYWORDS = {
    aspect: set(lemmatizer.lemmatize(kw) for kw in kws)
    for aspect, kws in ASPECT_KEYWORDS.items()
}

NEGATION_WORDS   = {"not", "no", "never", "isn't", "wasn't", "don't", "doesn't"}
CLAUSE_SPLITTERS = ["but", "however", "although", "though", "yet", "while"]

DEFAULT_PREFS = {
    "food": 0.40, "service": 0.30, "price": 0.20, "wait_time": 0.10,
}

POSITIVE_BOOST = 0.20
PRIOR_STRENGTH = 5   # Bayesian smoothing hyper-parameter k

ASPECT_COLS = [f"aspect_{a}" for a in ASPECT_KEYWORDS]   # 4 cols written into meta


# ─────────────────────────────────────────────────────────────────────────────
# Step 0 — Frequency Analysis
# ─────────────────────────────────────────────────────────────────────────────

def frequency_analysis(reviews_df, top_n=30):
    """Word-frequency audit to validate ASPECT_KEYWORDS."""
    all_words = []
    for text in reviews_df["text"].dropna():
        words = re.findall(r'\b[a-z]+\b', text.lower())
        all_words.extend(words)

    freq = Counter(all_words)

    print(f"Top {top_n} most common words in reviews:")
    for word, count in freq.most_common(top_n):
        print(f"  {word:<20} {count:>8,}")

    print("\nFrequency check for ASPECT_KEYWORDS:")
    for aspect, keywords in ASPECT_KEYWORDS.items():
        print(f"\n[{aspect}]")
        for kw in keywords:
            count = freq.get(kw, 0)
            flag  = "  ⚠ low (<500)" if count < 500 else ""
            print(f"  {kw:<20} {count:>8,}{flag}")

    return freq


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — ABSA Helpers
# ─────────────────────────────────────────────────────────────────────────────

def split_into_sentences(text):
    if not isinstance(text, str) or not text.strip():
        return []
    return nltk.sent_tokenize(text)


def split_clauses(sentence):
    result = [sentence]
    for splitter in CLAUSE_SPLITTERS:
        new_result = []
        for clause in result:
            parts = clause.split(f" {splitter} ")
            new_result.extend(parts)
        result = new_result
    return [c.strip() for c in result if c.strip()]


def lemmatize_words(words):
    return [lemmatizer.lemmatize(w) for w in words]


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Core ABSA (with Bayesian Smoothing)
# ─────────────────────────────────────────────────────────────────────────────

def compute_aspect_scores_from_texts(texts, priors, k=PRIOR_STRENGTH):
    """
    Compute aspect sentiment scores from an iterable of review texts.
    Logic identical to compute_aspect_scores_single but decoupled from
    the review dataframe — the caller does the grouping.

    Returns {aspect: smoothed_score} covering all ASPECT_KEYWORDS.
    """
    aspect_score_lists = {aspect: [] for aspect in ASPECT_KEYWORDS}

    for review in texts:
        for sentence in split_into_sentences(review):
            for clause in split_clauses(sentence):
                raw_words   = clause.lower().split()
                lemma_words = lemmatize_words(raw_words)

                aspect_trigger_strength = {}
                for i, lemma in enumerate(lemma_words):
                    for aspect, kws in LEMMATIZED_KEYWORDS.items():
                        if lemma in kws:
                            context_start = max(0, i - 3)
                            context_end   = min(len(raw_words), i + 4)
                            context_text  = " ".join(raw_words[context_start:context_end])
                            strength = abs(analyzer.polarity_scores(context_text)["compound"])
                            if aspect not in aspect_trigger_strength or \
                               strength > aspect_trigger_strength[aspect]:
                                aspect_trigger_strength[aspect] = strength

                if not aspect_trigger_strength:
                    continue

                clause_sentiment = analyzer.polarity_scores(clause)["compound"]

                if len(aspect_trigger_strength) == 1:
                    aspect = next(iter(aspect_trigger_strength))
                    aspect_score_lists[aspect].append(clause_sentiment)
                else:
                    dominant = max(aspect_trigger_strength, key=aspect_trigger_strength.get)
                    aspect_score_lists[dominant].append(clause_sentiment)

    smoothed = {}
    for aspect, scores in aspect_score_lists.items():
        n             = len(scores)
        observed_mean = float(np.mean(scores)) if n > 0 else 0.0
        smoothed[aspect] = (n * observed_mean + k * priors[aspect]) / (n + k)

    return smoothed


def compute_priors(all_scores_list):
    """Estimate global priors from a sample of restaurants (no smoothing applied)."""
    aggregated = defaultdict(list)
    for scores in all_scores_list:
        for aspect, val in scores.items():
            aggregated[aspect].append(val)
    return {aspect: float(np.mean(vals)) for aspect, vals in aggregated.items()}


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Precompute All Aspects + Write to Meta Parquet
# ─────────────────────────────────────────────────────────────────────────────

def precompute_all_aspect_scores(
    reviews_df,
    meta_path="data/processed/meta-NYC-restaurant.parquet",
    prior_sample_frac=0.10,
    random_state=42,
):
    """
    Compute per-restaurant ABSA scores and write four aspect columns
    (aspect_food, aspect_service, aspect_price, aspect_wait_time) directly
    into the meta parquet at `meta_path`, globally min-max normalized to [0,1].

    Only restaurants present in `reviews_df` (i.e. those that passed the
    ≥15-review filter upstream) are scored; all other meta rows get NaN
    in the aspect columns.

    Returns (priors_dict, n_scored).
    """
    # Pre-group by gmap_id ONCE — avoids O(n²) linear scans per restaurant
    print("Grouping reviews by gmap_id...")
    texts_by_gid = (
        reviews_df[["gmap_id", "text"]]
        .dropna(subset=["text"])
        .groupby("gmap_id")["text"]
        .apply(list)
    )
    gmap_ids = texts_by_gid.index.to_numpy()
    n_total  = len(gmap_ids)
    print(f"Will score {n_total:,} restaurants (≥15 reviews).")

    # ── Phase 1: prior estimation (no smoothing, 10% sample) ──
    rng = np.random.default_rng(random_state)
    sample_size = max(1, int(len(gmap_ids) * prior_sample_frac))
    sample_ids  = rng.choice(gmap_ids, size=sample_size, replace=False)

    print(f"\nPhase 1/2: estimating priors on {sample_size:,} sampled restaurants...")
    sample_scores = []
    for gid in tqdm(sample_ids, desc="priors"):
        raw = {asp: [] for asp in ASPECT_KEYWORDS}
        for review in texts_by_gid.loc[gid]:
            for sentence in split_into_sentences(review):
                for clause in split_clauses(sentence):
                    lws = lemmatize_words(clause.lower().split())
                    for lw in lws:
                        for asp, kws in LEMMATIZED_KEYWORDS.items():
                            if lw in kws:
                                raw[asp].append(
                                    analyzer.polarity_scores(clause)["compound"])
                                break
        sample_scores.append({
            asp: float(np.mean(v)) if v else 0.0
            for asp, v in raw.items()
        })
    priors = compute_priors(sample_scores)
    print(f"Estimated priors: { {k: round(v, 4) for k, v in priors.items()} }")

    # ── Phase 2: smoothed scores for every restaurant ──
    print(f"\nPhase 2/2: computing Bayesian-smoothed aspect scores for all {n_total:,}...")
    records = []
    for gid in tqdm(gmap_ids, desc="aspects"):
        smoothed = compute_aspect_scores_from_texts(texts_by_gid.loc[gid], priors)
        smoothed["gmap_id"] = gid
        records.append(smoothed)

    scores_df = pd.DataFrame(records)
    # fix: Percentile-based normalization per aspect (robust to outliers) ──
    # Clip at [1st, 99th] percentile then min-max on the clipped range.
    # Done once against the full database so rankings are stable across queries.
    for aspect in ASPECT_KEYWORDS:
        col = scores_df[aspect]
        lo  = col.quantile(0.01)
        hi  = col.quantile(0.99)
        clipped = col.clip(lower=lo, upper=hi)
        if hi > lo:
            scores_df[f"aspect_{aspect}"] = (clipped - lo) / (hi - lo)
        else:
            scores_df[f"aspect_{aspect}"] = 0.5

    # Percentile rank for price and wait_time (display only, not used in ranking)
    for aspect in ("price", "wait_time"):
        scores_df[f"aspect_{aspect}_pct"] = (
            scores_df[f"aspect_{aspect}"].rank(pct=True) * 100
        ).round(0).astype("Int64")

    PCT_COLS = ["aspect_price_pct", "aspect_wait_time_pct"]
    out_cols = ["gmap_id"] + ASPECT_COLS + PCT_COLS

    # ── Merge into meta parquet: drop any stale aspect_* columns first ──
    print(f"\nLoading meta from {meta_path} to merge aspect columns...")
    meta = pd.read_parquet(meta_path)
    stale = [c for c in ASPECT_COLS if c in meta.columns]
    if stale:
        print(f"  Dropping stale columns: {stale}")
        meta = meta.drop(columns=stale)
    merged = meta.merge(scores_df[out_cols], on="gmap_id", how="left")
    assert len(merged) == len(meta), "merge changed row count"

    merged.to_parquet(meta_path, index=False)
    covered = merged[ASPECT_COLS[0]].notna().sum()
    print(f"Wrote {merged.shape[0]:,} rows to {meta_path} "
          f"({covered:,} with aspect scores, "
          f"{merged.shape[0] - covered:,} without reviews → NaN).")

    return priors, int(covered)


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Query Intent Parser
# ─────────────────────────────────────────────────────────────────────────────

def get_aspect_prefs(query):
    """
    Infer user aspect preferences from a natural-language query.
    Returns a dict {food, service, price, wait_time} that sums to 1.0.
    """
    prefs = DEFAULT_PREFS.copy()
    triggered = False
    for clause in split_clauses(query.lower()):
        lemmas = lemmatize_words(clause.split())
        for lemma in lemmas:
            for aspect, kws in LEMMATIZED_KEYWORDS.items():
                if lemma in kws:
                    prefs[aspect] += POSITIVE_BOOST
                    triggered = True

    if not triggered:
        return DEFAULT_PREFS.copy()
    total = sum(prefs.values())
    return {k: v / total for k, v in prefs.items()}


# ─────────────────────────────────────────────────────────────────────────────
# Validation helpers — kept as tools, not part of the precompute path
# ─────────────────────────────────────────────────────────────────────────────

def validate_vader_clause_length(reviews_df, sample_n=500):
    lengths_before = []
    lengths_after  = []
    split_counts   = []

    for text in reviews_df["text"].dropna().sample(sample_n, random_state=42):
        for sentence in split_into_sentences(text):
            lengths_before.append(len(sentence.split()))
            clauses = split_clauses(sentence)
            split_counts.append(len(clauses))
            for c in clauses:
                lengths_after.append(len(c.split()))

    print(f"Avg words per sentence (before split): {np.mean(lengths_before):.1f}")
    print(f"Avg words per clause  (after split):   {np.mean(lengths_after):.1f}")
    print(f"Sentences that were split:             {np.mean([c > 1 for c in split_counts]):.1%}")
    print(f"Clauses with < 5 words:                {np.mean([l < 5 for l in lengths_after]):.1%}")


def validate_absa_accuracy(sample_sentences, human_labels):
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)

    for sentence, true_aspects in zip(sample_sentences, human_labels):
        predicted = set()
        for lemma in lemmatize_words(sentence.lower().split()):
            for aspect, kws in LEMMATIZED_KEYWORDS.items():
                if lemma in kws:
                    predicted.add(aspect)

        for aspect in ASPECT_KEYWORDS:
            in_true = aspect in true_aspects
            in_pred = aspect in predicted
            if in_true and in_pred:       tp[aspect] += 1
            if not in_true and in_pred:   fp[aspect] += 1
            if in_true and not in_pred:   fn[aspect] += 1

    print(f"\n{'Aspect':<12} {'Precision':>10} {'Recall':>10}")
    print("-" * 35)
    for aspect in ASPECT_KEYWORDS:
        p    = tp[aspect] / (tp[aspect] + fp[aspect]) if tp[aspect] + fp[aspect] > 0 else 0.0
        r    = tp[aspect] / (tp[aspect] + fn[aspect]) if tp[aspect] + fn[aspect] > 0 else 0.0
        flag = "  ⚠ low recall" if r < 0.5 else ""
        print(f"{aspect:<12} {p:>10.1%} {r:>10.1%}{flag}")
