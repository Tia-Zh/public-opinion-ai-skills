import argparse
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


def try_sklearn_backend(
    train_df,
    df,
    text_col,
    label_col,
    confidence_threshold,
    margin_threshold,
    sklearn_max_features,
    progress_every,
):
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
    except Exception as exc:
        raise RuntimeError(f"scikit-learn unavailable: {exc}") from exc

    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(analyzer="char", ngram_range=(1, 2), min_df=1, max_features=sklearn_max_features)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(train_df[text_col].astype(str), train_df[label_col].astype(str))
    labels = list(model.classes_)

    predicted = []
    confidence = []
    margin = []
    texts = df[text_col].astype(str)
    total = len(texts)
    batch_size = progress_every or total
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        probabilities = model.predict_proba(texts.iloc[start:end])
        for row in probabilities:
            order = row.argsort()[::-1]
            top = order[0]
            second = order[1] if len(order) > 1 else top
            predicted.append(labels[top])
            confidence.append(float(row[top]))
            margin.append(float(row[top] - row[second]) if len(order) > 1 else float(row[top]))
        if progress_every:
            print(f"scored {end}/{total}", file=sys.stderr, flush=True)

    out = df.copy()
    out["predicted_label"] = predicted
    out["predicted_confidence"] = [round(v, 4) for v in confidence]
    out["top2_margin"] = [round(v, 4) for v in margin]
    out["needs_review"] = (
        (out["predicted_confidence"] < confidence_threshold)
        | (out["top2_margin"] < margin_threshold)
    )
    return out, "sklearn-logistic-regression"


def char_ngrams(text, min_n=1, max_n=2, max_chars=600):
    text = re.sub(r"\s+", "", str(text or ""))[:max_chars]
    chars = list(text)
    feats = []
    for n in range(min_n, max_n + 1):
        feats.extend("".join(chars[i : i + n]) for i in range(0, max(0, len(chars) - n + 1)))
    return feats


def train_fast_nb(train_df, text_col, label_col, max_vocab_per_label=3500, max_chars=600):
    label_counts = Counter(train_df[label_col].astype(str))
    raw_token_counts = defaultdict(Counter)
    for _, row in train_df.iterrows():
        raw_token_counts[str(row[label_col])].update(char_ngrams(row[text_col], max_chars=max_chars))

    token_counts = {}
    vocab = set()
    for label, counts in raw_token_counts.items():
        trimmed = Counter(dict(counts.most_common(max_vocab_per_label)))
        token_counts[label] = trimmed
        vocab.update(trimmed)

    total_tokens = {label: sum(counts.values()) for label, counts in token_counts.items()}
    labels = sorted(label_counts)
    total_docs = sum(label_counts.values())
    priors = {label: math.log(label_counts[label] / total_docs) for label in labels}
    vocab_size = max(1, len(vocab))
    return labels, priors, token_counts, total_tokens, vocab, vocab_size


def predict_one_fast_nb(text, model, max_chars=600):
    labels, priors, token_counts, total_tokens, vocab, vocab_size = model
    feats = [feat for feat in char_ngrams(text, max_chars=max_chars) if feat in vocab]
    feat_counts = Counter(feats)
    scores = {}
    for label in labels:
        denom = total_tokens[label] + vocab_size
        score = priors[label]
        counts = token_counts[label]
        for feat, count in feat_counts.items():
            score += count * math.log((counts[feat] + 1) / denom)
        scores[label] = score

    max_score = max(scores.values())
    exp_scores = {label: math.exp(score - max_score) for label, score in scores.items()}
    z = sum(exp_scores.values()) or 1.0
    probs = {label: value / z for label, value in exp_scores.items()}
    ranked = sorted(probs.items(), key=lambda item: item[1], reverse=True)
    top_label, top_prob = ranked[0]
    second_prob = ranked[1][1] if len(ranked) > 1 else 0.0
    return top_label, top_prob, top_prob - second_prob


def fast_nb_backend(
    train_df,
    df,
    text_col,
    label_col,
    confidence_threshold,
    margin_threshold,
    max_vocab_per_label,
    max_chars,
    progress_every,
):
    model = train_fast_nb(train_df, text_col, label_col, max_vocab_per_label=max_vocab_per_label, max_chars=max_chars)
    preds = []
    total = len(df)
    for idx, value in enumerate(df[text_col].astype(str), start=1):
        preds.append(predict_one_fast_nb(value, model, max_chars=max_chars))
        if progress_every and idx % progress_every == 0:
            print(f"scored {idx}/{total}", file=sys.stderr, flush=True)

    out = df.copy()
    out["predicted_label"] = [p[0] for p in preds]
    out["predicted_confidence"] = [round(float(p[1]), 4) for p in preds]
    out["top2_margin"] = [round(float(p[2]), 4) for p in preds]
    out["needs_review"] = (
        (out["predicted_confidence"] < confidence_threshold)
        | (out["top2_margin"] < margin_threshold)
    )
    return out, "fast-char-ngram-naive-bayes"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="CSV containing clean text and any available labels")
    ap.add_argument("--output", required=True)
    ap.add_argument("--text-col", default="clean_text")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--confidence-threshold", type=float, default=0.6)
    ap.add_argument("--margin-threshold", type=float, default=0.15)
    ap.add_argument("--backend", choices=["auto", "sklearn", "fast-nb"], default="auto")
    ap.add_argument("--max-vocab-per-label", type=int, default=3500)
    ap.add_argument("--max-chars", type=int, default=600)
    ap.add_argument("--sklearn-max-features", type=int, default=60000)
    ap.add_argument("--progress-every", type=int, default=10000)
    args = ap.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    if args.text_col not in df.columns:
        raise ValueError(f"Missing text column: {args.text_col}")
    if args.label_col not in df.columns:
        raise ValueError(f"Missing label column: {args.label_col}")

    train_df = df[df[args.label_col].notna() & df[args.label_col].astype(str).str.strip().ne("")].copy()
    if train_df[args.label_col].nunique() < 2:
        raise ValueError("Need at least two labels to train a classifier")

    if args.backend in {"auto", "sklearn"}:
        try:
            out, backend_used = try_sklearn_backend(
                train_df,
                df,
                args.text_col,
                args.label_col,
                args.confidence_threshold,
                args.margin_threshold,
                args.sklearn_max_features,
                args.progress_every,
            )
        except RuntimeError:
            if args.backend == "sklearn":
                raise
            print("scikit-learn not available; falling back to fast-nb", file=sys.stderr, flush=True)
            out, backend_used = fast_nb_backend(
                train_df,
                df,
                args.text_col,
                args.label_col,
                args.confidence_threshold,
                args.margin_threshold,
                args.max_vocab_per_label,
                args.max_chars,
                args.progress_every,
            )
    else:
        out, backend_used = fast_nb_backend(
            train_df,
            df,
            args.text_col,
            args.label_col,
            args.confidence_threshold,
            args.margin_threshold,
            args.max_vocab_per_label,
            args.max_chars,
            args.progress_every,
        )

    out["classifier_backend"] = backend_used
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(args.output)


if __name__ == "__main__":
    main()
