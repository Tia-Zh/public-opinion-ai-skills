#!/usr/bin/env python3
"""Validate denominator disclosure before sentiment/stance reporting.

This script is intentionally small and conservative. It does not decide
sentiment. It only checks whether a final row-level output has enough
denominator evidence to report sentiment/stance shares.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


IN_DENOM_ALIASES = [
    "是否纳入情感分母",
    "是否纳入立场分母",
    "纳入情感分母",
    "in_sentiment_denominator",
    "in_stance_denominator",
    "in_denominator",
    "effective_for_sentiment",
]

EXCLUSION_ALIASES = [
    "排除原因",
    "不纳入原因",
    "分母排除原因",
    "exclusion_reason",
    "denominator_exclusion_reason",
    "exclude_reason",
]

LABEL_ALIASES = [
    "情绪标签",
    "情感标签",
    "立场标签",
    "label",
    "predicted_label",
    "sentiment_label",
    "stance_label",
]

YES_VALUES = {"yes", "y", "true", "1", "是", "纳入", "有效", "include", "included"}
NO_VALUES = {"no", "n", "false", "0", "否", "不纳入", "排除", "exclude", "excluded"}


def find_col(df: pd.DataFrame, explicit: str | None, aliases: list[str]) -> str | None:
    if explicit:
        if explicit not in df.columns:
            raise SystemExit(f"Missing required column: {explicit}")
        return explicit
    lowered = {str(c).strip().lower(): c for c in df.columns}
    for alias in aliases:
        hit = lowered.get(alias.lower())
        if hit is not None:
            return hit
    return None


def normalize_flag(value: object) -> str:
    text = str(value).strip().lower()
    if text in YES_VALUES:
        return "yes"
    if text in NO_VALUES:
        return "no"
    if text in {"", "nan", "none", "null"}:
        return ""
    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Final row-level CSV/XLSX with labels and denominator fields.")
    parser.add_argument("--output", required=True, help="CSV report path.")
    parser.add_argument("--sheet", default=None, help="Excel sheet name when --input is XLSX.")
    parser.add_argument("--label-col", default=None)
    parser.add_argument("--in-denominator-col", default=None)
    parser.add_argument("--exclusion-reason-col", default=None)
    parser.add_argument("--fail-on-missing", action="store_true", default=True)
    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(input_path, sheet_name=args.sheet or 0)
    else:
        df = pd.read_csv(input_path)

    label_col = find_col(df, args.label_col, LABEL_ALIASES)
    in_col = find_col(df, args.in_denominator_col, IN_DENOM_ALIASES)
    reason_col = find_col(df, args.exclusion_reason_col, EXCLUSION_ALIASES)

    problems: list[str] = []
    if label_col is None:
        problems.append("missing_label_column")
    if in_col is None:
        problems.append("missing_in_denominator_column")
    if reason_col is None:
        problems.append("missing_exclusion_reason_column")

    total_rows = len(df)
    effective_rows = 0
    excluded_rows = 0
    unknown_flag_rows = 0
    excluded_missing_reason = 0
    effective_missing_label = 0

    if in_col is not None:
        flags = df[in_col].map(normalize_flag)
        effective_mask = flags == "yes"
        excluded_mask = flags == "no"
        unknown_flag_rows = int((flags == "unknown").sum() + (flags == "").sum())
        effective_rows = int(effective_mask.sum())
        excluded_rows = int(excluded_mask.sum())
        if reason_col is not None:
            reasons = df[reason_col].fillna("").astype(str).str.strip()
            excluded_missing_reason = int((excluded_mask & (reasons == "")).sum())
            if excluded_missing_reason:
                problems.append("excluded_rows_missing_reason")
        if label_col is not None:
            labels = df[label_col].fillna("").astype(str).str.strip()
            effective_missing_label = int((effective_mask & (labels == "")).sum())
            if effective_missing_label:
                problems.append("effective_rows_missing_label")
        if effective_rows == 0:
            problems.append("zero_effective_denominator")
        if unknown_flag_rows:
            problems.append("unknown_or_blank_denominator_flags")

    status = "pass" if not problems else "fail"
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "status",
                "problem_codes",
                "total_rows",
                "effective_denominator",
                "excluded_rows",
                "unknown_flag_rows",
                "excluded_missing_reason",
                "effective_missing_label",
                "label_col",
                "in_denominator_col",
                "exclusion_reason_col",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "status": status,
                "problem_codes": ";".join(sorted(set(problems))),
                "total_rows": total_rows,
                "effective_denominator": effective_rows,
                "excluded_rows": excluded_rows,
                "unknown_flag_rows": unknown_flag_rows,
                "excluded_missing_reason": excluded_missing_reason,
                "effective_missing_label": effective_missing_label,
                "label_col": label_col or "",
                "in_denominator_col": in_col or "",
                "exclusion_reason_col": reason_col or "",
            }
        )

    if status != "pass":
        raise SystemExit(
            "Denominator gate failed. Do not report sentiment/stance shares until "
            f"the issues are fixed. See: {output_path}"
        )
    print(f"Denominator gate passed. Report written to {output_path}")


if __name__ == "__main__":
    main()
