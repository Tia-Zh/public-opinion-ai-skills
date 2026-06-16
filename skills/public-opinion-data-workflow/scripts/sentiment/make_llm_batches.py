import argparse
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--sample-n", type=int, default=1000)
    ap.add_argument("--batch-size", type=int, default=100)
    ap.add_argument("--strata-cols", default="source,date")
    ap.add_argument("--random-state", type=int, default=42)
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    strata_cols = [c for c in args.strata_cols.split(",") if c in df.columns]

    if args.sample_n and args.sample_n < len(df) and strata_cols:
        parts = []
        per_group = max(1, args.sample_n // max(1, df.groupby(strata_cols).ngroups))
        for _, sub in df.groupby(strata_cols, dropna=False):
            parts.append(sub.sample(min(len(sub), per_group), random_state=args.random_state))
        sample = pd.concat(parts).drop_duplicates("row_id")
        if len(sample) < args.sample_n:
            remain = df[~df["row_id"].isin(sample["row_id"])]
            sample = pd.concat([sample, remain.sample(min(len(remain), args.sample_n - len(sample)), random_state=args.random_state)])
        sample = sample.sample(min(len(sample), args.sample_n), random_state=args.random_state).sort_values("row_id")
    elif args.sample_n and args.sample_n < len(df):
        sample = df.sample(args.sample_n, random_state=args.random_state).sort_values("row_id")
    else:
        sample = df.sort_values("row_id")

    sample.to_csv(out_dir / "llm_label_sample.csv", index=False, encoding="utf-8-sig")

    rows = []
    for batch_id, start in enumerate(range(0, len(sample), args.batch_size), start=1):
        sub = sample.iloc[start:start + args.batch_size]
        text = "\n".join(
            f"row_id={int(r.row_id)} | source={getattr(r, 'source', '')} | date={getattr(r, 'date', '')} | text={str(r.clean_text).replace(chr(10), ' ')}"
            for r in sub.itertuples()
        )
        rows.append({"batch_id": batch_id, "n": len(sub), "prompt_payload": text})
    pd.DataFrame(rows).to_csv(out_dir / "llm_batches.csv", index=False, encoding="utf-8-sig")
    print(out_dir / "llm_batches.csv")


if __name__ == "__main__":
    main()

