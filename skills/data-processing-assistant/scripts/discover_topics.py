#!/usr/bin/env python3
"""Discover rough text topics with a dependency-light TF-IDF + k-means baseline."""

from __future__ import annotations

import argparse
import csv
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


def tokenize(text: str, min_n: int = 2, max_n: int = 4) -> list[str]:
    text = re.sub(r"\s+", "", str(text or ""))
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    chars = [c for c in text if not c.isspace()]
    terms: list[str] = []
    for n in range(min_n, max_n + 1):
        terms.extend("".join(chars[i : i + n]) for i in range(0, max(0, len(chars) - n + 1)))
    return terms


def build_vectors(texts: list[str], max_features: int) -> tuple[list[dict[int, float]], list[str]]:
    doc_terms = [tokenize(t) for t in texts]
    df = Counter()
    for terms in doc_terms:
        df.update(set(terms))
    vocab_terms = [term for term, _ in df.most_common(max_features)]
    vocab = {term: i for i, term in enumerate(vocab_terms)}
    n_docs = max(1, len(texts))
    idf = {term: math.log((1 + n_docs) / (1 + df[term])) + 1.0 for term in vocab_terms}
    vectors: list[dict[int, float]] = []
    for terms in doc_terms:
        counts = Counter(t for t in terms if t in vocab)
        vec = {vocab[t]: c * idf[t] for t, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({i: v / norm for i, v in vec.items()})
    return vectors, vocab_terms


def cosine_distance(vec: dict[int, float], centroid: dict[int, float]) -> float:
    sim = sum(value * centroid.get(idx, 0.0) for idx, value in vec.items())
    return 1.0 - sim


def mean_vector(vectors: list[dict[int, float]]) -> dict[int, float]:
    acc: defaultdict[int, float] = defaultdict(float)
    for vec in vectors:
        for idx, value in vec.items():
            acc[idx] += value
    if not vectors:
        return {}
    out = {idx: value / len(vectors) for idx, value in acc.items()}
    norm = math.sqrt(sum(v * v for v in out.values())) or 1.0
    return {idx: value / norm for idx, value in out.items()}


def kmeans(vectors: list[dict[int, float]], k: int, seed: int, max_iter: int = 30) -> tuple[list[int], list[dict[int, float]], float]:
    rng = random.Random(seed)
    if k <= 0:
        raise ValueError("k must be positive")
    if k > len(vectors):
        k = len(vectors)
    centroids = [vectors[i].copy() for i in rng.sample(range(len(vectors)), k)]
    labels = [0] * len(vectors)
    for _ in range(max_iter):
        changed = False
        for i, vec in enumerate(vectors):
            label = min(range(k), key=lambda c: cosine_distance(vec, centroids[c]))
            if label != labels[i]:
                labels[i] = label
                changed = True
        groups = [[] for _ in range(k)]
        for label, vec in zip(labels, vectors):
            groups[label].append(vec)
        for c, group in enumerate(groups):
            if group:
                centroids[c] = mean_vector(group)
        if not changed:
            break
    inertia = sum(cosine_distance(vec, centroids[label]) for vec, label in zip(vectors, labels))
    return labels, centroids, inertia


def choose_k(vectors: list[dict[int, float]], candidates: list[int], seed: int) -> tuple[int, list[int], list[dict[int, float]]]:
    best = None
    for k in candidates:
        if k < 2 or k > len(vectors):
            continue
        labels, centroids, inertia = kmeans(vectors, k, seed)
        counts = Counter(labels)
        balance_penalty = max(counts.values()) / max(1, min(counts.values()))
        score = inertia * (1.0 + 0.03 * balance_penalty)
        if best is None or score < best[0]:
            best = (score, k, labels, centroids)
    if best is None:
        labels, centroids, _ = kmeans(vectors, min(3, len(vectors)), seed)
        return min(3, len(vectors)), labels, centroids
    return best[1], best[2], best[3]


def top_terms_for_topic(vectors: list[dict[int, float]], labels: list[int], topic: int, vocab: list[str], top_n: int) -> list[str]:
    acc: defaultdict[int, float] = defaultdict(float)
    count = 0
    for vec, label in zip(vectors, labels):
        if label != topic:
            continue
        count += 1
        for idx, value in vec.items():
            acc[idx] += value
    if count == 0:
        return []
    return [vocab[idx] for idx, _ in sorted(acc.items(), key=lambda x: x[1], reverse=True)[:top_n]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="CSV/XLSX file")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--text-col", default="clean_text")
    ap.add_argument("--id-col", default="")
    ap.add_argument("--clusters", default="auto", help="Number of topics, or auto")
    ap.add_argument("--max-features", type=int, default=1200)
    ap.add_argument("--max-rows", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    source = Path(args.input)
    if source.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
        df = pd.read_excel(source, dtype=object)
    else:
        df = pd.read_csv(source, dtype=object, encoding="utf-8-sig")
    if args.text_col not in df.columns:
        raise ValueError(f"Missing text column: {args.text_col}")

    work = df[df[args.text_col].notna() & df[args.text_col].astype(str).str.strip().ne("")].copy()
    if len(work) > args.max_rows:
        work = work.sample(args.max_rows, random_state=args.seed).copy()
    texts = work[args.text_col].astype(str).tolist()
    if len(texts) < 2:
        raise ValueError("Need at least two non-empty text rows")

    vectors, vocab = build_vectors(texts, args.max_features)
    if args.clusters == "auto":
        if len(vectors) < 30:
            k = min(3, len(vectors))
            labels, centroids, _ = kmeans(vectors, k, args.seed)
        else:
            candidates = [k for k in range(3, min(9, len(vectors)) + 1)]
            k, labels, centroids = choose_k(vectors, candidates, args.seed)
    else:
        k = int(args.clusters)
        labels, centroids, _ = kmeans(vectors, k, args.seed)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = work.copy()
    out["topic_id"] = labels
    out["topic_distance"] = [round(cosine_distance(vec, centroids[label]), 4) for vec, label in zip(vectors, labels)]
    out.to_csv(out_dir / "topic_assignments.csv", index=False, encoding="utf-8-sig")

    summary_rows = []
    for topic in sorted(set(labels)):
        subset = out[out["topic_id"] == topic]
        examples = subset.sort_values("topic_distance")[args.text_col].astype(str).head(3).tolist()
        summary_rows.append(
            {
                "topic_id": topic,
                "count": int(len(subset)),
                "share": round(len(subset) / len(out), 4),
                "top_terms": "、".join(top_terms_for_topic(vectors, labels, topic, vocab, 12)),
                "examples": " | ".join(examples),
            }
        )
    pd.DataFrame(summary_rows).to_csv(out_dir / "topic_summary.csv", index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)
    print(out_dir)


if __name__ == "__main__":
    main()
