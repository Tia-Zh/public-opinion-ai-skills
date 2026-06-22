#!/usr/bin/env python3
"""Profile text quality before labeling or reporting.

This script does not classify sentiment. It gives deterministic counts for
empty text, short text, emoji/bracket-token-only rows, duplicate expressions,
URL/mention/contact-like rows, and question-like rows.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


BRACKET_TOKEN_RE = re.compile(r"^(\[[^\]]{1,12}\]\s*)+$")
URL_RE = re.compile(r"https?://|www\.", re.I)
MENTION_RE = re.compile(r"@\S+")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d{9}(?!\d)|(?<!\d)\d{7,12}(?!\d)")
QUESTION_RE = re.compile(r"[?？]|吗\b|么\b|是不是|难道|哪里|怎么|为什么")
COMMON_LOW_INFO = {
    "好的",
    "收到",
    "了解",
    "知道了",
    "谢谢",
    "感谢分享",
    "早安",
    "晚安",
    "哈哈",
    "呵呵",
    "转发",
    "分享",
    "666",
    "888",
}


def read_table(path: Path, sheet: str | None = None) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet or 0)
    return pd.read_csv(path, encoding="utf-8-sig")


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def info_len(text: str) -> int:
    stripped = re.sub(r"\[[^\]]+\]", "", text)
    stripped = re.sub(r"https?://\S+|www\.\S+", "", stripped, flags=re.I)
    stripped = re.sub(r"@\S+", "", stripped)
    stripped = re.sub(r"[\s\W_]+", "", stripped, flags=re.UNICODE)
    return len(stripped)


def is_bracket_token_only(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return bool(compact) and bool(BRACKET_TOKEN_RE.fullmatch(compact))


def is_emoji_or_symbol_only(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    if not compact:
        return False
    if is_bracket_token_only(compact):
        return True
    return info_len(compact) == 0


def contains_any(regex: re.Pattern[str], text: str) -> bool:
    return bool(regex.search(text))


def write_sample(df: pd.DataFrame, mask: pd.Series, output: Path, n: int) -> None:
    sample = df.loc[mask].head(n).copy()
    if len(sample):
        sample.to_csv(output, index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--text-col", default="clean_text")
    parser.add_argument("--sheet")
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--short-threshold", type=int, default=6)
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    df = read_table(input_path, args.sheet)
    if args.text_col not in df.columns:
        raise ValueError(f"Missing text column: {args.text_col}")

    text = df[args.text_col].apply(normalize_text)
    profiled = df.copy()
    profiled["_quality_text"] = text
    profiled["info_len"] = text.apply(info_len)
    profiled["empty_text"] = text.eq("")
    profiled["short_text_candidate"] = profiled["info_len"].lt(args.short_threshold) & ~profiled["empty_text"]
    profiled["emoji_or_symbol_only"] = text.apply(is_emoji_or_symbol_only)
    profiled["bracket_token_only"] = text.apply(is_bracket_token_only)
    profiled["common_low_info_text"] = text.isin(COMMON_LOW_INFO)
    profiled["contains_url"] = text.apply(lambda x: contains_any(URL_RE, x))
    profiled["contains_mention"] = text.apply(lambda x: contains_any(MENTION_RE, x))
    profiled["contains_email"] = text.apply(lambda x: contains_any(EMAIL_RE, x))
    profiled["contains_phone_or_long_number"] = text.apply(lambda x: contains_any(PHONE_RE, x))
    profiled["question_like"] = text.apply(lambda x: contains_any(QUESTION_RE, x))
    profiled["duplicate_count"] = text.groupby(text).transform("size")
    profiled["duplicate_expression"] = profiled["duplicate_count"].gt(1)

    total = len(profiled)
    rows = []
    for col in [
        "empty_text",
        "short_text_candidate",
        "emoji_or_symbol_only",
        "bracket_token_only",
        "common_low_info_text",
        "contains_url",
        "contains_mention",
        "contains_email",
        "contains_phone_or_long_number",
        "question_like",
        "duplicate_expression",
    ]:
        count = int(profiled[col].sum())
        rows.append({"metric": col, "count": count, "share": round(count / total, 4) if total else 0})

    rows.extend(
        [
            {"metric": "rows", "count": total, "share": 1.0 if total else 0},
            {"metric": "unique_texts", "count": int(text.nunique()), "share": round(text.nunique() / total, 4) if total else 0},
            {"metric": "duplicate_extra_rows", "count": int(total - text.nunique()), "share": round((total - text.nunique()) / total, 4) if total else 0},
        ]
    )

    pd.DataFrame(rows).to_csv(output_dir / "text_quality_profile.csv", index=False, encoding="utf-8-sig")
    profiled.to_csv(output_dir / "text_quality_flags.csv", index=False, encoding="utf-8-sig")

    sample_specs = {
        "sample_empty_text.csv": profiled["empty_text"],
        "sample_short_text.csv": profiled["short_text_candidate"],
        "sample_emoji_or_symbol_only.csv": profiled["emoji_or_symbol_only"],
        "sample_common_low_info.csv": profiled["common_low_info_text"],
        "sample_question_like.csv": profiled["question_like"],
        "sample_duplicate_expression.csv": profiled["duplicate_expression"],
        "sample_privacy_risk.csv": profiled["contains_url"]
        | profiled["contains_mention"]
        | profiled["contains_email"]
        | profiled["contains_phone_or_long_number"],
    }
    for filename, mask in sample_specs.items():
        write_sample(profiled, mask, output_dir / filename, args.sample_size)

    print(output_dir / "text_quality_profile.csv")


if __name__ == "__main__":
    main()
