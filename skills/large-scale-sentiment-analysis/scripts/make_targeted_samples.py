import argparse
import json
import re
from pathlib import Path

import pandas as pd


def load_keywords(path):
    if not path:
        return {}
    p = Path(path).expanduser().resolve()
    if p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    df = pd.read_csv(p, encoding="utf-8-sig")
    if not {"label", "keyword"}.issubset(df.columns):
        raise ValueError("Keyword CSV must contain label,keyword columns")
    result = {}
    for label, group in df.groupby("label", dropna=False):
        result[str(label)] = {
            "keywords": [str(value) for value in group["keyword"].dropna()],
            "min_chars": pd.to_numeric(group.get("min_chars"), errors="coerce").dropna().min()
            if "min_chars" in group
            else None,
            "max_chars": pd.to_numeric(group.get("max_chars"), errors="coerce").dropna().max()
            if "max_chars" in group
            else None,
        }
    return result


def keyword_hits(text, keywords):
    value = str(text or "").lower()
    return [kw for kw in keywords if str(kw).lower() in value]


def normalize_keyword_config(config):
    if isinstance(config, list):
        return {"keywords": config, "min_chars": None, "max_chars": None}
    if isinstance(config, dict):
        return {
            "keywords": config.get("keywords", []),
            "min_chars": config.get("min_chars"),
            "max_chars": config.get("max_chars"),
        }
    return {"keywords": [], "min_chars": None, "max_chars": None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--text-col", default="clean_text")
    parser.add_argument("--row-id-col", default="row_id")
    parser.add_argument("--weak-label-col", default="", help="Optional existing weak/rule candidate label column")
    parser.add_argument("--keywords", default="", help="Optional JSON or CSV keyword map for targeted labels")
    parser.add_argument("--target-labels", required=True, help="Comma-separated target labels to supplement")
    parser.add_argument("--per-label", type=int, default=100)
    parser.add_argument("--min-chars", type=int, default=0, help="Global minimum text length filter")
    parser.add_argument("--max-chars", type=int, default=0, help="Global maximum text length filter; 0 disables")
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path, encoding="utf-8-sig")
    if args.text_col not in df.columns:
        raise ValueError(f"Missing text column: {args.text_col}")
    if args.row_id_col not in df.columns:
        raise ValueError(f"Missing row_id column: {args.row_id_col}")

    df["_target_text_len"] = df[args.text_col].astype(str).str.len()
    if args.min_chars:
        df = df[df["_target_text_len"] >= args.min_chars]
    if args.max_chars:
        df = df[df["_target_text_len"] <= args.max_chars]

    target_labels = [label.strip() for label in args.target_labels.split(",") if label.strip()]
    keyword_map = load_keywords(args.keywords)

    parts = []
    summary = []
    for label in target_labels:
        candidates = []
        if args.weak_label_col and args.weak_label_col in df.columns:
            candidates.append(df[df[args.weak_label_col].astype(str).eq(label)])
        if label in keyword_map:
            cfg = normalize_keyword_config(keyword_map[label])
            kws = cfg["keywords"]
            keyword_source = df
            if cfg["min_chars"] is not None:
                keyword_source = keyword_source[keyword_source["_target_text_len"] >= int(cfg["min_chars"])]
            if cfg["max_chars"] is not None:
                keyword_source = keyword_source[keyword_source["_target_text_len"] <= int(cfg["max_chars"])]
            hit_mask = keyword_source[args.text_col].astype(str).map(lambda value: bool(keyword_hits(value, kws)))
            hit_df = keyword_source[hit_mask].copy()
            hit_df["target_keyword_hits"] = hit_df[args.text_col].map(lambda value: "|".join(keyword_hits(value, kws)[:8]))
            candidates.append(hit_df)

        if candidates:
            label_df = pd.concat(candidates, ignore_index=True).drop_duplicates(args.row_id_col)
        else:
            label_df = df.head(0).copy()

        sampled = label_df.sample(min(len(label_df), args.per_label), random_state=args.random_state) if len(label_df) else label_df
        sampled = sampled.copy()
        sampled["target_label_candidate"] = label
        sampled["target_sampling_reason"] = "weak_rule_or_keyword_candidate"
        sampled["target_text_len"] = sampled["_target_text_len"] if "_target_text_len" in sampled.columns else ""
        parts.append(sampled)
        summary.append({"target_label": label, "candidate_rows": len(label_df), "sampled_rows": len(sampled)})

    out = pd.concat(parts, ignore_index=True) if parts else df.head(0).copy()
    keep_cols = [
        args.row_id_col,
        args.text_col,
        "target_label_candidate",
        "target_sampling_reason",
        "target_keyword_hits",
        "target_text_len",
    ]
    keep_cols = [col for col in keep_cols if col in out.columns]
    out[keep_cols].to_csv(out_dir / "targeted_label_candidates.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(summary).to_csv(out_dir / "targeted_sampling_summary.csv", index=False, encoding="utf-8-sig")
    print(out_dir / "targeted_label_candidates.csv")


if __name__ == "__main__":
    main()
