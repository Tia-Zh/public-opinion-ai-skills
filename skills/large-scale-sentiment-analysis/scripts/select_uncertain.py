import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--confidence-col", default="confidence")
    ap.add_argument("--margin-col", default="top2_margin")
    ap.add_argument("--uncertain-label", default="uncertain")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--random-per-class", type=int, default=50)
    ap.add_argument("--low-confidence-n", type=int, default=400)
    ap.add_argument("--low-margin-n", type=int, default=400)
    ap.add_argument("--weak-label-col", default="", help="Optional weak/rule candidate label column")
    ap.add_argument("--weak-per-class", type=int, default=80)
    ap.add_argument("--disagreement-n", type=int, default=300)
    args = ap.parse_args()

    df = pd.read_csv(Path(args.merged).expanduser().resolve(), encoding="utf-8-sig")
    if args.confidence_col in df.columns:
        df[args.confidence_col] = pd.to_numeric(df[args.confidence_col], errors="coerce")
    if args.margin_col in df.columns:
        df[args.margin_col] = pd.to_numeric(df[args.margin_col], errors="coerce")

    parts = []
    if args.label_col in df.columns:
        parts.append(df[df[args.label_col].eq(args.uncertain_label)])
    if args.confidence_col in df.columns:
        parts.append(df.sort_values(args.confidence_col, na_position="first").head(args.low_confidence_n))
    if args.margin_col in df.columns:
        parts.append(df.sort_values(args.margin_col, na_position="first").head(args.low_margin_n))
    if "is_sarcasm" in df.columns:
        parts.append(df[df["is_sarcasm"].astype(str).str.upper().isin(["TRUE", "1", "YES"])])
    if args.label_col in df.columns:
        for _, sub in df.groupby(args.label_col, dropna=False):
            parts.append(sub.sample(min(len(sub), args.random_per_class), random_state=42))

    if args.weak_label_col and args.weak_label_col in df.columns:
        weak_df = df[df[args.weak_label_col].notna() & df[args.weak_label_col].astype(str).str.strip().ne("")]
        for _, sub in weak_df.groupby(args.weak_label_col, dropna=False):
            parts.append(sub.sample(min(len(sub), args.weak_per_class), random_state=43))
        if args.label_col in df.columns:
            disagreement = weak_df[
                weak_df[args.label_col].notna()
                & weak_df[args.weak_label_col].astype(str).ne(weak_df[args.label_col].astype(str))
            ]
            if len(disagreement):
                parts.append(disagreement.sample(min(len(disagreement), args.disagreement_n), random_state=44))

    out = pd.concat(parts).drop_duplicates("row_id").head(args.n)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(args.output)


if __name__ == "__main__":
    main()
