#!/usr/bin/env python3
"""Audit an AI-labeled or to-be-labeled active-learning batch."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV batch or labeled batch.")
    parser.add_argument("--output", required=True, help="CSV summary output.")
    parser.add_argument("--label-col", default="label")
    parser.add_argument("--text-col", default="clean_text")
    parser.add_argument("--hash-col", default="text_hash")
    parser.add_argument("--max-label-share", type=float, default=0.8)
    parser.add_argument("--max-duplicate-expression-share", type=float, default=0.3)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(Path(args.input).expanduser().resolve(), encoding="utf-8-sig")
    rows = []
    failed = False

    total = len(df)
    rows.append({"metric": "rows", "value": total, "status": "info", "note": ""})

    if args.label_col in df.columns and total:
        counts = df[args.label_col].fillna("").astype(str).str.strip().value_counts()
        top_label = str(counts.index[0]) if len(counts) else ""
        top_count = int(counts.iloc[0]) if len(counts) else 0
        top_share = top_count / total if total else 0
        status = "ok"
        note = ""
        if top_share > args.max_label_share:
            status = "pause_before_training"
            note = (
                f"Top label share {top_share:.1%} exceeds "
                f"max_label_share={args.max_label_share:.0%}. Audit sampling and supplement missing labels."
            )
            failed = True
        rows.append({"metric": "top_label", "value": top_label, "status": status, "note": note})
        rows.append({"metric": "top_label_share", "value": round(top_share, 4), "status": status, "note": note})
        for label, count in counts.items():
            rows.append({"metric": f"label_count:{label}", "value": int(count), "status": "info", "note": ""})

    key_col = args.hash_col if args.hash_col in df.columns else args.text_col if args.text_col in df.columns else ""
    if key_col and total:
        key = df[key_col].fillna("").astype(str).str.strip()
        duplicate_extra = int(total - key.nunique())
        duplicate_share = duplicate_extra / total if total else 0
        status = "ok"
        note = ""
        if duplicate_share > args.max_duplicate_expression_share:
            status = "dedupe_review_batch"
            note = (
                f"Duplicate expression share {duplicate_share:.1%} exceeds "
                f"max_duplicate_expression_share={args.max_duplicate_expression_share:.0%}. "
                "Deduplicate by text expression before AI labeling."
            )
            failed = True
        rows.append({"metric": "duplicate_extra_rows", "value": duplicate_extra, "status": status, "note": note})
        rows.append({"metric": "duplicate_expression_share", "value": round(duplicate_share, 4), "status": status, "note": note})

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")

    if failed and not args.warn_only:
        raise SystemExit(f"Active-learning batch audit failed. See {out}")
    print(out)


if __name__ == "__main__":
    main()
