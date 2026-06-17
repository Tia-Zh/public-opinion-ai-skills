#!/usr/bin/env python3
"""Validate labeled-sample coverage before training a sentiment classifier."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def split_labels(value: str) -> list[str]:
    return [x.strip() for x in value.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", required=True, help="CSV file containing AI-reviewed labels.")
    parser.add_argument("--label-col", default="label")
    parser.add_argument("--target-labels", required=True, help="Comma-separated final report labels.")
    parser.add_argument("--min-per-label", type=int, default=20)
    parser.add_argument("--max-class-share", type=float, default=0.8)
    parser.add_argument("--output", required=True)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    df = pd.read_csv(args.labels, encoding="utf-8-sig")
    if args.label_col not in df.columns:
        raise SystemExit(f"Missing label column: {args.label_col}")

    labels = split_labels(args.target_labels)
    counts = df[args.label_col].astype(str).value_counts()
    total = int(counts.reindex(labels).fillna(0).sum())
    rows = []
    failed = False

    for label in labels:
        count = int(counts.get(label, 0))
        share = count / total if total else 0
        status = "ok"
        notes = []
        if count < args.min_per_label:
            status = "needs_targeted_sampling"
            notes.append(f"below min_per_label={args.min_per_label}")
            failed = True
        if share > args.max_class_share and len(labels) > 1:
            status = "audit_required"
            notes.append(f"class share {share:.1%} exceeds max_class_share={args.max_class_share:.0%}")
            failed = True
        rows.append({"label": label, "count": count, "share": share, "status": status, "note": "; ".join(notes)})

    unknown = sorted(set(counts.index) - set(labels))
    if unknown:
        rows.append({"label": "__unknown_or_non_target__", "count": int(counts.reindex(unknown).fillna(0).sum()), "share": "", "status": "check_schema", "note": ",".join(unknown)})

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")

    if failed and not args.warn_only:
        raise SystemExit(f"Label coverage check failed. See {out}")
    print(out)


if __name__ == "__main__":
    main()
