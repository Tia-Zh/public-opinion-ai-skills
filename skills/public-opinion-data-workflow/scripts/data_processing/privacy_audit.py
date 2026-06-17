#!/usr/bin/env python3
"""Audit tabular data for common privacy risks before export or AI labeling."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


SENSITIVE_COLUMN_HINTS = [
    "昵称",
    "用户",
    "账号",
    "作者",
    "主页",
    "链接",
    "网址",
    "url",
    "id",
    "uid",
    "位置",
    "地址",
    "ip",
    "邮箱",
    "手机",
    "电话",
]

TEXT_PATTERNS = {
    "url": re.compile(r"https?://\S+|www\.\S+", re.I),
    "mention": re.compile(r"@[\w\u4e00-\u9fa5_-]+"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "phone_or_long_id": re.compile(r"(?<!\d)(?:\+?\d[\d\-\s()]{7,}\d)(?!\d)"),
}


def read_input(path: Path, sheet: str | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        return pd.read_excel(path, sheet_name=sheet or 0, dtype=object)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t", encoding="utf-8-sig", dtype=object)
    return pd.read_csv(path, encoding="utf-8-sig", dtype=object)


def column_matches(name: str, hints: list[str]) -> bool:
    lower = name.lower()
    for hint in hints:
        key = hint.lower()
        if key.isascii() and len(key) <= 3:
            tokens = [t for t in re.split(r"[^a-z0-9]+", lower) if t]
            if key in tokens:
                return True
        elif key in lower:
            return True
    return False


def sample_masked(value: Any, limit: int = 80) -> str:
    text = "" if pd.isna(value) else str(value)
    for pattern_name, pattern in TEXT_PATTERNS.items():
        text = pattern.sub(f"[{pattern_name.upper()}]", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--sheet")
    parser.add_argument("--text-col", action="append", default=[])
    parser.add_argument("--column-hints", default="\n".join(SENSITIVE_COLUMN_HINTS))
    parser.add_argument("--sample-size", type=int, default=5000)
    args = parser.parse_args()

    source = Path(args.input)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = read_input(source, args.sheet)
    if len(df) > args.sample_size:
        sample = df.sample(args.sample_size, random_state=42).copy()
    else:
        sample = df.copy()

    hints = [x.strip() for x in re.split(r"[\n,，]+", args.column_hints) if x.strip()]
    text_cols = [c for c in args.text_col if c in sample.columns]
    if not text_cols:
        text_cols = [
            c
            for c in sample.columns
            if any(k in str(c) for k in ["正文", "内容", "评论", "文本", "翻译", "留言"])
        ]

    column_rows = []
    for col in sample.columns:
        if column_matches(str(col), hints):
            nonblank = int(sample[col].notna().sum())
            unique = int(sample[col].dropna().astype(str).nunique())
            column_rows.append(
                {
                    "column": str(col),
                    "risk_type": "sensitive_column_name",
                    "nonblank_rows": nonblank,
                    "unique_values": unique,
                    "recommended_action": "hash_or_drop_if_not_needed",
                }
            )

    text_rows = []
    for col in text_cols:
        values = sample[col].fillna("").astype(str)
        for pattern_name, pattern in TEXT_PATTERNS.items():
            hit_mask = values.map(lambda x: bool(pattern.search(x)))
            hits = int(hit_mask.sum())
            if hits:
                examples = [sample_masked(v) for v in values[hit_mask].head(3).tolist()]
                text_rows.append(
                    {
                        "column": str(col),
                        "pattern": pattern_name,
                        "hit_rows": hits,
                        "sample_masked_examples": " | ".join(examples),
                        "recommended_action": "mask_in_text_before_ai_or_export",
                    }
                )

    pd.DataFrame(column_rows).to_csv(out_dir / "privacy_column_risks.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(text_rows).to_csv(out_dir / "privacy_text_risks.csv", index=False, encoding="utf-8-sig")
    summary = {
        "input": str(source),
        "rows": int(len(df)),
        "sample_rows_checked": int(len(sample)),
        "sensitive_column_count": len(column_rows),
        "text_risk_pattern_count": len(text_rows),
        "text_columns_checked": [str(c) for c in text_cols],
        "outputs": ["privacy_column_risks.csv", "privacy_text_risks.csv"],
    }
    (out_dir / "privacy_audit_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_dir)


if __name__ == "__main__":
    main()
