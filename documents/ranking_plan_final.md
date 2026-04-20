# 完整规划：从评论提取 Category 评分 + 个性化排名

---
## 给 Claude Code 的说明 
这是一个餐厅推荐系统的实现规划。请按照以下步骤顺序实现代码。 数据文件路径：data/reviews.parquet（含列 gmap_id, text, rating） 所有代码注释请用英文。 每个 Step 完成后打印一条进度信息。并且每块implement成功之后，要添加进入README.
你按照“总执行流程”分块执行，每次估算你运行多久之后需要我介入的时间。
ask clarifying questions when any place is not clear. 
需要思考怎么用到其他步骤做好的结果，特别是和semantic search, 还有app.py的可视化衔接，让这个项目衔接自然。
## 总执行流程
第一批任务 ──────────────────────────────────────
① 搭建项目结构，写好所有函数（Step 0~5 的代码）
② 运行 frequency_analysis()，打印结果
      ↓
      [你介入] 看频率结果，决定关键词表怎么改，告诉它新的 ASPECT_KEYWORDS
      ↓
第二批任务 ──────────────────────────────────────
③ 用更新后的关键词表跑 precompute_all_aspect_scores()
④ 把 100 句话存成 CSV（validate_absa_accuracy 的准备）
      ↓
      [你介入] 手动标注那 100 句话，填好 CSV
      ↓
第三批任务 ──────────────────────────────────────
⑤ 读取你的标注，跑 validate_absa_accuracy() 和 validate_query_detection()
⑥ 跑 sensitivity_analysis()，输出 α/β/γ 对比表
      ↓
      [你介入] 选定 α/β/γ 组合，告诉它用哪组
      ↓
第四批任务 ──────────────────────────────────────
⑦ 用选定权重跑 demo，生成 top-5 排名结果，存成文件
      ↓
      [你介入] 对 demo 结果打 Relevance Score（5~10 个查询的 top-5）
      ↓
⑧ Claude Code 读取你的评分，计算平均分，生成报告表格
## 系统架构概览

```
Layer 1 ── Retrieval
           用户输入查询词 → similarity search → 100 个语义相关候选餐厅
           （解决"相关性"问题，此后排名不再涉及 similarity）

Layer 2 ── ABSA 离线预计算（本文件的核心）
           全量评论 → 每家餐厅的 5 个 aspect 情感分
           （一次性跑完，存成 parquet，查询时直接读取）

Layer 3 ── Ranking Formula（无需训练模型）
           final_score = α × avg_rating
                       + β × aspect_weighted
                       + γ × log(1 + num_reviews)
           α/β/γ 通过 Sensitivity Analysis 选定
```

**三层各司其职，无循环依赖，无数据泄漏。**

---

## Step 0：词频分析（在构建关键词列表之前必须做）

**目的**：验证 `ASPECT_KEYWORDS` 里的词是否真的在评论中高频出现，而非凭直觉拍脑袋。

```python
from collections import Counter
import re

def frequency_analysis(reviews_df, top_n=30):
    """
    对全量评论做词频统计，输出每个 aspect 候选词的出现频率。
    运行本函数后，对照结果调整 ASPECT_KEYWORDS。
    """
    all_words = []
    for text in reviews_df["text"].dropna():
        words = re.findall(r'\b[a-z]+\b', text.lower())
        all_words.extend(words)

    freq = Counter(all_words)

    print("Top 30 most common words in reviews:")
    for word, count in freq.most_common(top_n):
        print(f"  {word:<20} {count:>8,}")

    print("\nFrequency check for ASPECT_KEYWORDS:")
    for aspect, keywords in ASPECT_KEYWORDS.items():
        print(f"\n[{aspect}]")
        for kw in keywords:
            print(f"  {kw:<20} {freq.get(kw, 0):>8,}")

    return freq
```

**使用方式**：运行后，删去低频词（< 500次），补充高频但尚未收录的 aspect 相关词。修改结果记录在报告中，说明关键词列表是数据驱动的，非人工猜测。

---

## Step 1：ABSA 离线预计算

### 1.1 常量定义

```python
import numpy as np
import pandas as pd
import nltk
import re
from nltk.stem import WordNetLemmatizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import defaultdict

nltk.download('punkt',   quiet=True)
nltk.download('wordnet', quiet=True)

lemmatizer = WordNetLemmatizer()
analyzer   = SentimentIntensityAnalyzer()

# ── 关键词表（根据 Step 0 词频分析结果调整） ──────────────────────────
ASPECT_KEYWORDS = {
    "food":      ["food", "dish", "meal", "taste", "flavor",
                  "cuisine", "menu", "portion", "ingredient", "quality"],
    "service":   ["service", "staff", "waiter", "waitress",
                  "server", "host", "bartender"],
    "ambience":  ["ambience", "atmosphere", "decor", "vibe",
                  "environment", "interior", "seating", "lighting", "music", "noise"],
    "price":     ["price", "cost", "cheap", "expensive",
                  "affordable", "value", "worth", "overpriced", "reasonable"],
    "wait_time": ["wait", "line", "queue", "reservation",
                  "delay", "busy", "packed", "crowded"],
}

# 预先对关键词做词形还原，避免"tasted"/"foods"等变形匹配不到
LEMMATIZED_KEYWORDS = {
    aspect: set(lemmatizer.lemmatize(kw) for kw in kws)
    for aspect, kws in ASPECT_KEYWORDS.items()
}

NEGATION_WORDS   = {"not", "no", "never", "isn't", "wasn't", "don't", "doesn't"}
CLAUSE_SPLITTERS = ["but", "however", "although", "though", "yet", "while"]

DEFAULT_PREFS = {
    "food": 0.35, "service": 0.25, "ambience": 0.20,
    "price": 0.10, "wait_time": 0.10
}

POSITIVE_BOOST   = 0.20
NEGATIVE_PENALTY = 0.10
PRIOR_STRENGTH   = 5    # Bayesian smoothing 超参数 k，Sensitivity Analysis 的调节对象之一
```

### 1.2 辅助函数

```python
def split_into_sentences(text):
    if not isinstance(text, str) or not text.strip():
        return []
    return nltk.sent_tokenize(text)


def split_clauses(sentence):
    """
    按对比/转折词拆分子句。
    e.g. "food was great but service was slow"
      → ["food was great", "service was slow"]

    局限：仅处理列表内的拆分词，不覆盖所有句法情况。
    实际效果通过 Step 3.2 的 VADER 子句验证来量化。
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
```

### 1.3 核心 ABSA 函数（含 Bayesian Smoothing）

```python
def compute_aspect_scores_single(gmap_id, reviews_df, priors, k=PRIOR_STRENGTH):
    """
    计算单家餐厅五个 aspect 的情感分。

    Pipeline：
    1. 按句拆分（NLTK）
    2. 按转折词拆子句
    3. 对每个词做词形还原后做关键词匹配
    4. 若子句匹配到多个 aspect，取情感绝对值最强的词所在 aspect（歧义处理）
    5. VADER 对子句打情感分 compound ∈ [-1, 1]
    6. 汇总后做 Bayesian Smoothing

    Bayesian Smoothing：
        smoothed = (n × observed_mean + k × prior) / (n + k)
    - n=0（无提及）：回退到全局均值 prior，而非 0.0
    - n 很大：prior 影响消失，结果接近真实观测值
    - 解决"无信息"与"真实中性情感"被同一个 0.0 混淆的问题

    歧义处理：
    "The waiter said the food was terrible"
    → service（waiter）情感中性，food（terrible）情感强烈负面
    → 归入 food ✅
    已知局限：纯关键词匹配无法解析句法结构，在报告中声明。
    """
    aspect_score_lists = {aspect: [] for aspect in ASPECT_KEYWORDS}
    reviews = reviews_df[reviews_df["gmap_id"] == gmap_id]["text"].dropna()

    for review in reviews:
        for sentence in split_into_sentences(review):
            for clause in split_clauses(sentence):
                raw_words    = clause.lower().split()
                lemma_words  = lemmatize_words(raw_words)

                # 找出这个子句里所有匹配到的 aspect，记录触发词的情感强度
                aspect_trigger_strength = {}
                for i, lemma in enumerate(lemma_words):
                    for aspect, kws in LEMMATIZED_KEYWORDS.items():
                        if lemma in kws:
                            # 用触发词上下文的 VADER 分代表该词的情感强度
                            context_start = max(0, i - 3)
                            context_end   = min(len(raw_words), i + 4)
                            context_text  = " ".join(raw_words[context_start:context_end])
                            strength = abs(analyzer.polarity_scores(context_text)["compound"])
                            # 保留该 aspect 在本子句中情感最强的触发词
                            if aspect not in aspect_trigger_strength or \
                               strength > aspect_trigger_strength[aspect]:
                                aspect_trigger_strength[aspect] = strength

                if not aspect_trigger_strength:
                    continue

                # 整个子句的情感分
                clause_sentiment = analyzer.polarity_scores(clause)["compound"]

                if len(aspect_trigger_strength) == 1:
                    # 只有一个 aspect，直接归入
                    aspect = next(iter(aspect_trigger_strength))
                    aspect_score_lists[aspect].append(clause_sentiment)
                else:
                    # 多个 aspect：只归入触发词情感最强的那个（歧义处理）
                    dominant = max(aspect_trigger_strength, key=aspect_trigger_strength.get)
                    aspect_score_lists[dominant].append(clause_sentiment)

    # Bayesian Smoothing
    smoothed = {}
    for aspect, scores in aspect_score_lists.items():
        n             = len(scores)
        observed_mean = float(np.mean(scores)) if n > 0 else 0.0
        smoothed[aspect] = (n * observed_mean + k * priors[aspect]) / (n + k)

    return smoothed


def compute_priors(all_scores_list):
    """
    在预计算开始前，先用简单均值估算全局先验。
    为避免循环，可先用一批样本餐厅（如随机 10% 不做 smoothing）估算 prior。
    """
    aggregated = defaultdict(list)
    for scores in all_scores_list:
        for aspect, val in scores.items():
            aggregated[aspect].append(val)
    return {aspect: float(np.mean(vals)) for aspect, vals in aggregated.items()}


def precompute_all_aspect_scores(reviews_df,
                                  save_path="data/processed/aspect_scores.parquet"):
    """
    离线预计算所有餐厅的 aspect scores，存入 parquet。
    查询时直接读取，不在线计算。

    两阶段：
    Phase 1：用随机 10% 餐厅（不做 smoothing）估算全局 prior
    Phase 2：对所有餐厅做 Bayesian Smoothing 预计算
    """
    gmap_ids = reviews_df["gmap_id"].unique()

    # Phase 1：估算 prior（用简单均值，无 smoothing）
    sample_ids   = np.random.choice(gmap_ids, size=max(1, len(gmap_ids) // 10), replace=False)
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

    # Phase 2：全量计算
    records = []
    for i, gid in enumerate(gmap_ids):
        scores           = compute_aspect_scores_single(gid, reviews_df, priors)
        scores["gmap_id"] = gid
        records.append(scores)
        if i % 1000 == 0:
            print(f"Progress: {i}/{len(gmap_ids)}")

    df = pd.DataFrame(records)
    df.to_parquet(save_path, index=False)
    print(f"Saved → {save_path}")
    return df, priors
```

---

## Step 2：从查询词自动推断用户偏好

```python
def get_aspect_prefs(query):
    """
    从搜索词中检测用户关心的 aspect，调整权重。

    规则：
    - 关键词匹配（词形还原后）→ +0.20
    - 关键词前 2 词内出现否定词 → 改为 -0.10（处理 "not cheap" 问题）
    - 归一化至总和 = 1.0
    - 未检测到任何关键词 → 静默回退 DEFAULT_PREFS，不提示用户

    注意：此处不用 VADER，query 表达的是用户意图（intent），不是情感。
    局限：仅处理单词级否定，无法处理"I don't want to wait"这类结构。
    """
    prefs = DEFAULT_PREFS.copy()
    for clause in split_clauses(query.lower()):
        words  = clause.split()
        lemmas = lemmatize_words(words)
        for i, lemma in enumerate(lemmas):
            for aspect, kws in LEMMATIZED_KEYWORDS.items():
                if lemma in kws:
                    context = words[max(0, i - 2):i]
                    if any(neg in context for neg in NEGATION_WORDS):
                        prefs[aspect] -= NEGATIVE_PENALTY
                    else:
                        prefs[aspect] += POSITIVE_BOOST

    total = sum(prefs.values())
    if total <= 0:
        return DEFAULT_PREFS.copy()
    return {k: v / total for k, v in prefs.items()}
```

**查询词与按钮的交互逻辑：**

| 场景                        | 行为                          |
| ------------------------- | --------------------------- |
| 查询词检测到关键词                 | 用检测到的权重，不弹出按钮               |
| 查询词无关键词，用户手动点 category 按钮 | 把被选 category 的权重乘以 1.5 后归一化 |
| 两者都无                      | 用 DEFAULT_PREFS             |

---

## Step 3：Ranking Formula

```python
def rank_candidates(candidates_df, aspect_scores_df, user_pref, alpha, beta, gamma):
    """
    candidates_df : similarity search 返回的候选集（含 gmap_id, avg_rating, num_reviews）
    aspect_scores_df : 离线预计算的 aspect scores
    user_pref        : get_aspect_prefs(query) 的输出
    alpha/beta/gamma : Sensitivity Analysis 选定的超参数

    final_score = α × avg_rating
               + β × aspect_weighted
               + γ × log(1 + num_reviews)
    """
    df = candidates_df.merge(aspect_scores_df, on="gmap_id", how="left")

    df["aspect_weighted"] = sum(
        df[aspect] * user_pref[aspect]
        for aspect in ASPECT_KEYWORDS
    )

    # 归一化各分量到 [0,1]，避免量纲差异主导结果
    for col in ["avg_rating", "aspect_weighted"]:
        col_min, col_max = df[col].min(), df[col].max()
        if col_max > col_min:
            df[col] = (df[col] - col_min) / (col_max - col_min)

    log_reviews = np.log1p(df["num_reviews"])
    log_reviews = (log_reviews - log_reviews.min()) / \
                  (log_reviews.max() - log_reviews.min() + 1e-9)

    df["final_score"] = (
        alpha * df["avg_rating"]      +
        beta  * df["aspect_weighted"] +
        gamma * log_reviews
    )

    return df.sort_values("final_score", ascending=False)
```

---

## Step 4：Sensitivity Analysis（α / β / γ）

**目的**：回答"为什么选这组权重？结论依赖于这个选择吗？"

```python
def sensitivity_analysis(candidates_df, aspect_scores_df, user_pref,
                          human_scores_dict=None):
    """
    human_scores_dict: {gmap_id: relevance_score} 来自人工评估
    若无人工评估，用排名相关系数（Spearman）作为代理指标
    """
    import itertools
    from scipy.stats import spearmanr

    weight_candidates = [0.1, 0.2, 0.3, 0.4, 0.5]
    results = []

    for alpha, beta, gamma in itertools.product(weight_candidates, repeat=3):
        if abs(alpha + beta + gamma - 1.0) > 0.01:
            continue
        ranked = rank_candidates(candidates_df, aspect_scores_df,
                                  user_pref, alpha, beta, gamma)
        if human_scores_dict:
            ranked["human"] = ranked["gmap_id"].map(human_scores_dict).fillna(0)
            metric = ranked["human"].mean()
        else:
            # 代理指标：与 avg_rating 排名的 Spearman 相关（越低说明系统越不只依赖 rating）
            rating_rank = ranked["avg_rating"].rank(ascending=False)
            final_rank  = ranked["final_score"].rank(ascending=False)
            metric, _   = spearmanr(rating_rank, final_rank)

        results.append({"alpha": alpha, "beta": beta, "gamma": gamma, "metric": metric})

    return pd.DataFrame(results).sort_values("metric", ascending=False)
```

**汇报格式：**
```
alpha  beta  gamma  human_avg
0.3    0.5   0.2    1.72   ← 最优组合
0.3    0.4   0.3    1.70
0.4    0.5   0.1    1.68
...
结论：β（aspect_weighted）权重在 0.4~0.5 时表现最稳定，
     说明 aspect 偏好信号对排名提升贡献最大，结论对 α/γ 不敏感。
```

---

## Step 5：验证套件（全部整合进流程）

### 5.1 词频验证（配合 Step 0）

运行 `frequency_analysis(reviews_df)`，对照输出结果：
- 关键词出现次数 < 500 → 考虑删除
- Top-30 高频词中未被收录但属于某 aspect → 补充进关键词表
- 结果截图放入报告

### 5.2 VADER 子句长度验证

**动机**：VADER 设计用于完整句子，拆出的子句可能过短而降低准确性。

```python
def validate_vader_clause_length(reviews_df, sample_n=500):
    """
    统计拆分后子句的词数分布，量化 VADER 在短句上的退化程度。
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

    print(f"句子平均词数（拆分前）：{np.mean(lengths_before):.1f}")
    print(f"子句平均词数（拆分后）：{np.mean(lengths_after):.1f}")
    print(f"含拆分的句子比例：{np.mean([c > 1 for c in split_counts]):.1%}")
    print(f"子句词数 < 5 的比例：{np.mean([l < 5 for l in lengths_after]):.1%}")

    # 若 < 5词的子句比例 > 20%，在报告中说明这是 VADER 的已知局限，
    # 并说明 "无需解决，只需量化并声明"
```

**预期结论格式**：
> "拆分后子句平均 8.3 词，词数 < 5 的占 12%。VADER 在短句上的准确率下降已知，
> 本系统接受这一局限并在验证中量化其影响（见 5.3 精确率/召回率）。"

### 5.3 关键词匹配精确率 / 召回率验证

```python
# 步骤一（自动）：随机抽 100 句，存成 CSV
sample_sentences = reviews_df["text"].dropna().sample(100, random_state=42).tolist()
pd.Series(sample_sentences).to_csv("data/validation/sample_sentences.csv", index=False)

# 步骤二（人工）：打开 CSV，标注每句的 aspect（可多选，无关标 none）
# 规则：先标注，再跑系统。不能边看系统结果边标注（会引入确认偏误）

# 步骤三（自动）：运行验证
def validate_absa_accuracy(sample_sentences, human_labels):
    """
    human_labels: list of sets, e.g. [{"food"}, {"service","food"}, set()]
    报告每个 aspect 的 Precision 和 Recall。
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
            if in_true  and in_pred:  tp[aspect] += 1
            if not in_true and in_pred: fp[aspect] += 1
            if in_true and not in_pred: fn[aspect] += 1

    print(f"\n{'Aspect':<12} {'Precision':>10} {'Recall':>10}")
    print("-" * 35)
    for aspect in ASPECT_KEYWORDS:
        p = tp[aspect] / (tp[aspect] + fp[aspect]) if tp[aspect] + fp[aspect] > 0 else 0.0
        r = tp[aspect] / (tp[aspect] + fn[aspect]) if tp[aspect] + fn[aspect] > 0 else 0.0
        flag = "  ⚠ low recall" if r < 0.5 else ""
        print(f"{aspect:<12} {p:>10.1%} {r:>10.1%}{flag}")
```

### 5.4 Query Detection 验证（Standard B）

```python
def validate_query_detection(test_cases):
    """
    Standard B（修正版）：
    被检测到的 aspect 必须在5个维度中排名前2，才算正确。
    原 Standard A（只要 weight > default）过于宽松，几乎总能通过。
    """
    correct, total = 0, 0

    print(f"\n{'Query':<45} {'Expected':<20} {'Result'}")
    print("-" * 80)

    for case in test_cases:
        query    = case["query"]
        detected = get_aspect_prefs(query)

        # Standard B：排名前2
        sorted_aspects = sorted(detected.items(), key=lambda x: x[1], reverse=True)
        top2 = {a for a, _ in sorted_aspects[:2]}

        boosted    = case.get("expected_boosted",    [])
        suppressed = case.get("expected_suppressed", [])
        case_results = []

        for aspect in boosted:
            total += 1
            ok = aspect in top2
            correct += int(ok)
            case_results.append(f"{aspect}↑{'✅' if ok else '❌'}")

        for aspect in suppressed:
            total += 1
            bottom2 = {a for a, _ in sorted_aspects[-2:]}
            ok = aspect in bottom2
            correct += int(ok)
            case_results.append(f"{aspect}↓{'✅' if ok else '❌'}")

        print(f"{query:<45} {', '.join(case_results)}")

    accuracy = correct / total if total > 0 else 0.0
    print(f"\nQuery Detection Accuracy: {correct}/{total} = {accuracy:.1%}")
    return accuracy


# 测试用例示例（构造 100 个覆盖不同场景）
TEST_CASES = [
    {"query": "I want something cheap",
     "expected_boosted": ["price"]},
    {"query": "looking for fast service",
     "expected_boosted": ["wait_time", "service"]},
    {"query": "not looking for expensive places",
     "expected_suppressed": ["price"]},
    {"query": "cozy atmosphere for a date",
     "expected_boosted": ["ambience"]},
    {"query": "best ramen with amazing food",
     "expected_boosted": ["food"]},
]
```

### 5.5 端到端人工评估

**目的**：在没有真实用户点击数据的情况下，证明本系统优于纯 avg_rating 排名。

**Baseline 定义**（必须明确，否则教授会问）：
```
Baseline A：纯 avg_rating 降序排名
Baseline B：纯 similarity 降序排名（Layer 1 未经 re-ranking）
本系统：final_score 排名
```

**打分标准（Relevance Score）**：
```
2分 = 和查询词相关，且符合用户指定的 aspect 偏好
1分 = 和查询词相关，但不符合 aspect 偏好
0分 = 和查询词不相关
```

**流程**：
1. 选 5~10 个**未在任何验证步骤中出现过**的测试查询
2. 对每个查询，生成三个排名的 top-5（Baseline A / B / 本系统）
3. 由 2~3 人独立打分，取平均
4. 对比三组平均分

**汇报格式**：
```
Query: "cheap ramen with fast service"

           Baseline A    Baseline B    本系统
Top-5 avg    0.8           1.2          1.8

结论：本系统在 N 个查询上平均 Relevance Score 为 X.X，
     高于 Baseline A（avg_rating 排名）和 Baseline B（similarity 排名）。
```

---

## Step 6：Demo 展示格式

```
Query: "cheap ramen with fast service"
用户偏好（自动检测）：{price: 0.28, wait: 0.22, service: 0.20, food: 0.18, ambience: 0.12}

=== Baseline（纯 avg_rating） ===    === 本系统（final_score） ===
1. Nobu        ⭐4.8                  1. Ivan Ramen   ⭐4.2
   price_score: -0.3 ❌                  price_score: 0.8 ✅
   wait_score:  0.1  ❌                  wait_score:  0.7 ✅

2. Ivan Ramen  ⭐4.2                  2. Totto Ramen  ⭐4.5
   ...                                   ...

人工评估 Relevance Score：Baseline 0.8 → 本系统 1.8 ✅
```

---

## 局限性（报告中必须说明）

| 局限                  | 说明                                                         |
| ------------------- | ---------------------------------------------------------- |
| 关键词匹配无语义理解          | "The waiter said the food was terrible" 等歧义句仍有误判，已用触发词强度缓解 |
| VADER 短句退化          | 子句拆分后部分句子较短，VADER 准确率下降，已在 5.2 验证中量化                       |
| 否定词窗口有限             | 仅检测关键词前 2 词内的否定，"I don't want to wait long" 无法捕获           |
| 人工评估主观性             | 样本量小（5~10 查询），结论仅作方向性参考，未来可用 A/B Test 验证                   |
| Bayesian prior 估算偏差 | Prior 由 10% 样本估算，若样本不具代表性会引入偏差                             |