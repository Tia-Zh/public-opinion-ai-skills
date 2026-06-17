#!/usr/bin/env python3
"""Compare predicted labels against an existing reference label column."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def read_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
        return pd.read_excel(path, dtype=object)
    return pd.read_csv(path, encoding="utf-8-sig", dtype=object)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--reference-col", required=True)
    parser.add_argument("--predicted-col", required=True)
    parser.add_argument("--id-col", default="")
    parser.add_argument("--text-col", default="")
    parser.add_argument("--sample-size", type=int, default=200)
    args = parser.parse_args()

    source = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = read_input(source)
    for col in [args.reference_col, args.predicted_col]:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    work = df[df[args.reference_col].notna() & df[args.predicted_col].notna()].copy()
    work["_reference"] = work[args.reference_col].astype(str).str.strip()
    work["_predicted"] = work[args.predicted_col].astype(str).str.strip()
    work["_match"] = work["_reference"].eq(work["_predicted"])

    total = len(work)
    matched = int(work["_match"].sum())
    accuracy = matched / total if total else 0.0
    pd.DataFrame(
        [
            {"metric": "rows_compared", "value": total},
            {"metric": "matched_rows", "value": matched},
            {"metric": "agreement_rate", "value": round(accuracy, 4)},
            {"metric": "reference_column", "value": args.reference_col},
            {"metric": "predicted_column", "value": args.predicted_col},
        ]
    ).to_csv(out_dir / "label_comparison_summary.csv", index=False, encoding="utf-8-sig")

    confusion = pd.crosstab(work["_reference"], work["_predicted"], dropna=False)
    confusion.to_csv(out_dir / "confusion_matrix.csv", encoding="utf-8-sig")

    cols = [c for c in [args.id_col, args.text_col, args.reference_col, args.predicted_col] if c and c in work.columns]
    disagreements = work[~work["_match"]].copy()
    if args.sample_size and len(disagreements) > args.sample_size:
        disagreements = disagreements.sample(args.sample_size, random_state=42)
    disagreements[cols].to_csv(out_dir / "disagreement_sample.csv", index=False, encoding="utf-8-sig")
    print(out_dir)


if __name__ == "__main__":
    main()
