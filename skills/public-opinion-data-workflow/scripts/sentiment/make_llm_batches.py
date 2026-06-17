import argparse
from pathlib import Path

import pandas as pd


def add_text_len_bucket(df):
    if "clean_text" not in df.columns:
        return df
    length = df["clean_text"].fillna("").astype(str).str.len()
    df = df.copy()
    df["text_len_bucket"] = pd.cut(
        length,
        bins=[-1, 10, 30, 80, 200, 10**9],
        labels=["very_short", "short", "medium", "long", "very_long"],
    ).astype(str)
    return df


def stratified_sample(df, strata_cols, sample_n, random_state, min_per_stratum, max_per_stratum):
    if not sample_n or sample_n >= len(df) or not strata_cols:
        return df.sample(sample_n, random_state=random_state).sort_values("row_id") if sample_n and sample_n < len(df) else df.sort_values("row_id")

    grouped = list(df.groupby(strata_cols, dropna=False))
    parts = []
    used = set()

    # Coverage pass: ensure minority strata can appear without letting tiny strata dominate.
    for _, sub in grouped:
        take = min(len(sub), min_per_stratum, max_per_stratum)
        if take > 0:
            sampled = sub.sample(take, random_state=random_state)
            parts.append(sampled)
            used.update(sampled["row_id"].tolist())

    sample = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=df.columns)
    if len(sample) > sample_n:
        return sample.sample(sample_n, random_state=random_state).sort_values("row_id")

    # Proportional fill: preserve the overall volume structure after coverage.
    remain = df[~df["row_id"].isin(used)]
    need = sample_n - len(sample)
    if need > 0 and len(remain) > 0:
        fill = remain.sample(min(len(remain), need), random_state=random_state)
        sample = pd.concat([sample, fill], ignore_index=True)

    return sample.drop_duplicates("row_id").sample(min(len(sample), sample_n), random_state=random_state).sort_values("row_id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--sample-n", type=int, default=1000)
    ap.add_argument("--batch-size", type=int, default=100)
    ap.add_argument("--strata-cols", default="source,text_len_bucket")
    ap.add_argument("--min-per-stratum", type=int, default=5)
    ap.add_argument("--max-per-stratum", type=int, default=80)
    ap.add_argument("--random-state", type=int, default=42)
    args = ap.parse_args()

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(Path(args.input).expanduser().resolve(), encoding="utf-8-sig")
    df = add_text_len_bucket(df)
    strata_cols = [c for c in args.strata_cols.split(",") if c in df.columns]
    for col in strata_cols:
        df[col] = df[col].astype(str).fillna("")

    sample = stratified_sample(
        df=df,
        strata_cols=strata_cols,
        sample_n=args.sample_n,
        random_state=args.random_state,
        min_per_stratum=args.min_per_stratum,
        max_per_stratum=args.max_per_stratum,
    )

    sample.to_csv(out_dir / "llm_label_sample.csv", index=False, encoding="utf-8-sig")

    rows = []
    for batch_id, start in enumerate(range(0, len(sample), args.batch_size), start=1):
        sub = sample.iloc[start:start + args.batch_size]
        text = "\n".join(
            f"row_id={str(r.row_id).strip()} | source={getattr(r, 'source', '')} | date={getattr(r, 'date', '')} | text={str(r.clean_text).replace(chr(10), ' ')}"
            for r in sub.itertuples()
        )
        rows.append({"batch_id": batch_id, "n": len(sub), "prompt_payload": text})
    pd.DataFrame(rows).to_csv(out_dir / "llm_batches.csv", index=False, encoding="utf-8-sig")
    print(out_dir / "llm_batches.csv")


if __name__ == "__main__":
    main()
