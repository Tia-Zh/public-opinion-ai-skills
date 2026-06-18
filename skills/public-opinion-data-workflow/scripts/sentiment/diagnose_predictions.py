#!/usr/bin/env python3
"""Summarize prediction health before deciding whether to continue iteration."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--label-col", default="predicted_label")
    parser.add_argument("--confidence-col", default="predicted_confidence")
    parser.add_argument("--margin-col", default="top2_margin")
    parser.add_argument("--text-col", default="clean_text")
    parser.add_argument("--low-confidence-threshold", type=float, default=0.6)
    parser.add_argument("--low-margin-threshold", type=float, default=0.15)
    args = parser.parse_args()

    df = pd.read_csv(Path(args.predictions).expanduser().resolve(), encoding="utf-8-sig")
    rows = [{"metric": "rows", "value": len(df), "status": "info", "note": ""}]

    if args.label_col in df.columns and len(df):
        counts = df[args.label_col].fillna("").astype(str).value_counts()
        for label, count in counts.items():
            rows.append({"metric": f"label_share:{label}", "value": round(int(count) / len(df), 4), "status": "info", "note": ""})

    low_conf_mask = pd.Series(False, index=df.index)
    if args.confidence_col in df.columns:
        conf = pd.to_numeric(df[args.confidence_col], errors="coerce")
        low_conf_mask = conf.lt(args.low_confidence_threshold) | conf.isna()
        share = float(low_conf_mask.mean()) if len(df) else 0
        status = "ok"
        note = "Use audit samples; low confidence alone is not failure."
        if share > 0.9:
            status = "diagnose_before_iterating"
            note = "Check sampling, denominator/exclusions, duplicates, threshold, calibration, and label coverage."
        rows.append({"metric": "low_confidence_share", "value": round(share, 4), "status": status, "note": note})

    if args.margin_col in df.columns:
        margin = pd.to_numeric(df[args.margin_col], errors="coerce")
        low_margin_share = float((margin.lt(args.low_margin_threshold) | margin.isna()).mean()) if len(df) else 0
        rows.append({"metric": "low_margin_share", "value": round(low_margin_share, 4), "status": "info", "note": ""})

    if args.text_col in df.columns and len(df):
        key = df[args.text_col].fillna("").astype(str).str.strip()
        duplicate_extra_share = (len(df) - key.nunique()) / len(df)
        rows.append({"metric": "duplicate_extra_share", "value": round(duplicate_extra_share, 4), "status": "info", "note": "High duplicate share means review batches should be text-deduped."})
        if args.confidence_col in df.columns and low_conf_mask.any():
            low_conf = df[low_conf_mask].copy()
            low_key = low_conf[args.text_col].fillna("").astype(str).str.strip()
            rows.append({"metric": "low_conf_unique_texts", "value": int(low_key.nunique()), "status": "info", "note": ""})
            rows.append({"metric": "low_conf_duplicate_extra_rows", "value": int(len(low_conf) - low_key.nunique()), "status": "info", "note": ""})

    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    print(out)


if __name__ == "__main__":
    main()
