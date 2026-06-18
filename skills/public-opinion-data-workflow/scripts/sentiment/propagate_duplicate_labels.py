#!/usr/bin/env python3
"""Map labels from unique reviewed expressions back to all duplicate rows."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepared", required=True, help="prepared_texts.csv with row_id and text_hash/clean_text.")
    parser.add_argument("--reviewed-labels", required=True, help="AI-reviewed labels for unique expressions.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--key-col", default="text_hash", help="Preferred key for mapping labels back.")
    parser.add_argument("--text-col", default="clean_text", help="Fallback key if key-col is unavailable.")
    parser.add_argument("--label-col", default="label")
    parser.add_argument("--confidence-col", default="confidence")
    args = parser.parse_args()

    prepared = pd.read_csv(Path(args.prepared).expanduser().resolve(), encoding="utf-8-sig")
    labels = pd.read_csv(Path(args.reviewed_labels).expanduser().resolve(), encoding="utf-8-sig")

    key_col = args.key_col if args.key_col in prepared.columns and args.key_col in labels.columns else args.text_col
    if key_col not in prepared.columns or key_col not in labels.columns:
        raise SystemExit(f"Mapping key not found in both files: {args.key_col} or {args.text_col}")
    if args.label_col not in labels.columns:
        raise SystemExit(f"Missing label column in reviewed labels: {args.label_col}")

    prepared_key = prepared[key_col].fillna("").astype(str).str.strip()
    label_key = labels[key_col].fillna("").astype(str).str.strip()
    prepared = prepared.copy()
    labels = labels.copy()
    prepared["_map_key"] = prepared_key
    labels["_map_key"] = label_key

    duplicate_label_keys = labels[labels["_map_key"].duplicated(keep=False)].copy()
    labels_unique = labels.drop_duplicates("_map_key", keep="first")

    keep_cols = ["_map_key", args.label_col]
    if args.confidence_col in labels_unique.columns:
        keep_cols.append(args.confidence_col)
    if "reason" in labels_unique.columns:
        keep_cols.append("reason")
    if "is_sarcasm" in labels_unique.columns:
        keep_cols.append("is_sarcasm")

    out = prepared.merge(labels_unique[keep_cols], on="_map_key", how="left", suffixes=("", "_reviewed"))
    out["label_source"] = out[args.label_col].notna().map({True: "reviewed_expression_mapped", False: ""})
    out = out.drop(columns=["_map_key"])

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / "propagated_duplicate_labels.csv", index=False, encoding="utf-8-sig")

    summary = pd.DataFrame(
        [
            ["prepared_rows", len(prepared)],
            ["reviewed_label_rows", len(labels)],
            ["unique_reviewed_expressions", labels_unique["_map_key"].nunique()],
            ["duplicate_review_label_keys", len(duplicate_label_keys)],
            ["mapped_rows", int(out[args.label_col].notna().sum())],
            ["unmapped_rows", int(out[args.label_col].isna().sum())],
            ["mapping_key", key_col],
        ],
        columns=["metric", "value"],
    )
    summary.to_csv(out_dir / "duplicate_label_propagation_summary.csv", index=False, encoding="utf-8-sig")
    duplicate_label_keys.to_csv(out_dir / "duplicate_review_label_keys.csv", index=False, encoding="utf-8-sig")
    print(out_dir / "propagated_duplicate_labels.csv")


if __name__ == "__main__":
    main()
