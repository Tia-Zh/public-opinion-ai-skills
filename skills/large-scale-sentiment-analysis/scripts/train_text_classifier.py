import argparse
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


def char_ngrams(text, min_n=1, max_n=2):
    text = re.sub(r"\s+", "", str(text or ""))
    chars = list(text)
    feats = []
    for n in range(min_n, max_n + 1):
        feats.extend("".join(chars[i : i + n]) for i in range(0, max(0, len(chars) - n + 1)))
    return feats


def train_nb(train_df, text_col, label_col):
    label_counts = Counter(train_df[label_col].astype(str))
    token_counts = defaultdict(Counter)
    total_tokens = Counter()
    vocab = set()

    for row in train_df.itertuples(index=False):
        text = getattr(row, text_col)
        label = str(getattr(row, label_col))
        feats = char_ngrams(text)
        token_counts[label].update(feats)
        total_tokens[label] += len(feats)
        vocab.update(feats)

    labels = sorted(label_counts)
    vocab_size = max(1, len(vocab))
    total_docs = sum(label_counts.values())
    priors = {label: math.log(label_counts[label] / total_docs) for label in labels}
    return labels, priors, token_counts, total_tokens, vocab_size


def predict_one(text, model):
    labels, priors, token_counts, total_tokens, vocab_size = model
    feats = char_ngrams(text)
    scores = {}
    for label in labels:
        denom = total_tokens[label] + vocab_size
        score = priors[label]
        for feat in feats:
            score += math.log((token_counts[label][feat] + 1) / denom)
        scores[label] = score

    max_score = max(scores.values())
    exp_scores = {label: math.exp(score - max_score) for label, score in scores.items()}
    z = sum(exp_scores.values()) or 1.0
    probs = {label: value / z for label, value in exp_scores.items()}
    ranked = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    top_label, top_prob = ranked[0]
    second_prob = ranked[1][1] if len(ranked) > 1 else 0.0
    return top_label, top_prob, top_prob - second_prob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="CSV containing clean text and any available labels")
    ap.add_argument("--output", required=True)
    ap.add_argument("--text-col", default="clean_text")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--confidence-threshold", type=float, default=0.6)
    ap.add_argument("--margin-threshold", type=float, default=0.15)
    args = ap.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    if args.text_col not in df.columns:
        raise ValueError(f"Missing text column: {args.text_col}")
    if args.label_col not in df.columns:
        raise ValueError(f"Missing label column: {args.label_col}")

    train_df = df[df[args.label_col].notna() & df[args.label_col].astype(str).str.strip().ne("")].copy()
    if train_df[args.label_col].nunique() < 2:
        raise ValueError("Need at least two labels to train a classifier")

    safe_text_col = args.text_col.replace("-", "_")
    safe_label_col = args.label_col.replace("-", "_")
    work = df.rename(columns={args.text_col: safe_text_col, args.label_col: safe_label_col})
    train_work = train_df.rename(columns={args.text_col: safe_text_col, args.label_col: safe_label_col})

    model = train_nb(train_work, safe_text_col, safe_label_col)
    preds = [predict_one(text, model) for text in work[safe_text_col]]

    out = df.copy()
    out["predicted_label"] = [p[0] for p in preds]
    out["predicted_confidence"] = [round(float(p[1]), 4) for p in preds]
    out["top2_margin"] = [round(float(p[2]), 4) for p in preds]
    out["needs_review"] = (
        (out["predicted_confidence"] < args.confidence_threshold)
        | (out["top2_margin"] < args.margin_threshold)
    )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(args.output)


if __name__ == "__main__":
    main()
