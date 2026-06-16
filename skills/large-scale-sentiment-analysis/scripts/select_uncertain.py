import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--confidence-col", default="confidence")
    ap.add_argument("--uncertain-label", default="uncertain")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--random-per-class", type=int, default=50)
    args = ap.parse_args()

    df = pd.read_csv(args.merged, encoding="utf-8-sig")
    df[args.confidence_col] = pd.to_numeric(df[args.confidence_col], errors="coerce")

    parts = []
    parts.append(df[df[args.label_col].eq(args.uncertain_label)])
    parts.append(df.sort_values(args.confidence_col, na_position="first").head(args.n))
    if "is_sarcasm" in df.columns:
        parts.append(df[df["is_sarcasm"].astype(str).str.upper().isin(["TRUE", "1", "YES"])])
    for _, sub in df.groupby(args.label_col, dropna=False):
        parts.append(sub.sample(min(len(sub), args.random_per_class), random_state=42))

    out = pd.concat(parts).drop_duplicates("row_id").head(args.n)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(args.output)


if __name__ == "__main__":
    main()

