"""
absa.py
Aspect-Based Sentiment Analysis: offline pre-computation, query intent parsing,
and validation utilities for the restaurant ranking pipeline.
"""
import re
import numpy as np
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter, defaultdict

nltk.download('punkt',   quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)

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

# Pre-lemmatize keywords to handle inflected forms (e.g. "tasted", "foods")
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
PRIOR_STRENGTH   = 5   # Bayesian smoothing hyper-parameter k


# ─────────────────────────────────────────────────────────────────────────────
# Step 0 — Frequency Analysis
# ─────────────────────────────────────────────────────────────────────────────

def frequency_analysis(reviews_df, top_n=30):
    """
    Word-frequency analysis over all reviews to validate ASPECT_KEYWORDS.
    Run this before committing to the keyword table.
    Remove keywords with < 500 occurrences; add high-frequency unlisted words.
    """
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
    """
    Split on contrast/concession words so each clause carries one sentiment signal.
    e.g. "food was great but service was slow" → ["food was great", "service was slow"]
    Limitation: only covers the listed splitters, not full syntactic parsing.
    """
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

def compute_aspect_scores_single(gmap_id, reviews_df, priors, k=PRIOR_STRENGTH):
    """
    Compute aspect sentiment scores for one restaurant.

    Pipeline:
    1. Sentence tokenize (NLTK)
    2. Clause split on contrast words
    3. Lemmatize + keyword match per clause
    4. Ambiguity: if clause hits multiple aspects, assign to the one whose
       trigger word has the highest local VADER strength
    5. VADER compound score for the whole clause
    6. Bayesian smoothing: smoothed = (n*obs + k*prior) / (n+k)
       — n=0 falls back to prior rather than 0.0
    """
    aspect_score_lists = {aspect: [] for aspect in ASPECT_KEYWORDS}
    reviews = reviews_df[reviews_df["gmap_id"] == gmap_id]["text"].dropna()

    for review in reviews:
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
    """
    Estimate global priors from a sample of restaurants (no smoothing applied).
    Used in Phase 1 of precompute_all_aspect_scores.
    """
    aggregated = defaultdict(list)
    for scores in all_scores_list:
        for aspect, val in scores.items():
            aggregated[aspect].append(val)
    return {aspect: float(np.mean(vals)) for aspect, vals in aggregated.items()}


def precompute_all_aspect_scores(reviews_df,
                                  save_path="data/processed/aspect_scores.parquet"):
    """
    Offline pre-computation of aspect scores for all restaurants.
    Results saved to parquet; loaded at query time without re-computation.

    Phase 1: estimate global priors from a random 10% sample (no smoothing)
    Phase 2: compute Bayesian-smoothed scores for all restaurants
    """
    gmap_ids = reviews_df["gmap_id"].unique()

    # Phase 1: estimate priors
    sample_ids    = np.random.choice(gmap_ids, size=max(1, len(gmap_ids) // 10), replace=False)
    sample_scores = []
    for gid in sample_ids:
        raw = {asp: [] for asp in ASPECT_KEYWORDS}
        for review in reviews_df[reviews_df["gmap_id"] == gid]["text"].dropna():
            for sentence in split_into_sentences(review):
                for clause in split_clauses(sentence):
                    lws = lemmatize_words(clause.lower().split())
                    for lw in lws:
                        for asp, kws in LEMMATIZED_KEYWORDS.items():
                            if lw in kws:
                                raw[asp].append(analyzer.polarity_scores(clause)["compound"])
                                break
        sample_scores.append({
            asp: float(np.mean(v)) if v else 0.0
            for asp, v in raw.items()
        })
    priors = compute_priors(sample_scores)
    print(f"Estimated priors: {priors}")

    # Phase 2: full computation
    records = []
    for i, gid in enumerate(gmap_ids):
        scores            = compute_aspect_scores_single(gid, reviews_df, priors)
        scores["gmap_id"] = gid
        records.append(scores)
        if i % 1000 == 0:
            print(f"Progress: {i}/{len(gmap_ids)}")

    df = pd.DataFrame(records)
    df.to_parquet(save_path, index=False)
    print(f"Aspect scores saved → {save_path}")
    return df, priors


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Query Intent Parser
# ─────────────────────────────────────────────────────────────────────────────

def get_aspect_prefs(query):
    """
    Infer user aspect preferences from a natural-language query.

    Rule: any keyword mention → +POSITIVE_BOOST (mention = this aspect matters).
    Negation detection removed: "no long wait" and "not expensive" both signal
    that the user cares about that aspect; the ABSA scores already encode
    good/bad direction (high wait_time score = short wait, high price score =
    affordable), so direction does not need to be re-detected here.

    Falls back to DEFAULT_PREFS when no keywords are detected.
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
# Step 5.2 — VADER Clause-Length Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_vader_clause_length(reviews_df, sample_n=500):
    """
    Measure word-count distribution before/after clause splitting.
    Quantifies VADER degradation on short clauses.
    If > 20% of clauses have < 5 words, note this as a known limitation.
    """
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


# ─────────────────────────────────────────────────────────────────────────────
# Step 5.3 — ABSA Keyword Precision / Recall Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_absa_accuracy(sample_sentences, human_labels):
    """
    Measure keyword-matching precision and recall against human annotations.

    sample_sentences : list of str
    human_labels     : list of sets, e.g. [{"food"}, {"service", "food"}, set()]
    Prints per-aspect Precision and Recall; flags aspects with Recall < 0.5.
    """
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


print("absa.py loaded.")
