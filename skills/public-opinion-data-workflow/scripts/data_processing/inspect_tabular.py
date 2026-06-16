#!/usr/bin/env python3
"""Inspect Excel/CSV/TSV files and print a compact schema summary."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def read_tables(path: Path) -> dict[str, pd.DataFrame]:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(path, sheet_name=None, dtype=object)
    if suffix == ".csv":
        return {"数据": pd.read_csv(path, dtype=object, encoding="utf-8-sig")}
    if suffix == ".tsv":
        return {"数据": pd.read_csv(path, dtype=object, sep="\t", encoding="utf-8-sig")}
    raise ValueError(f"Unsupported file type: {suffix}")


def sample_values(series: pd.Series, limit: int = 3) -> list[str]:
    values = []
    for value in series.dropna().astype(str):
        text = re.sub(r"\s+", " ", value).strip()
        if text and text not in values:
            values.append(text[:80])
        if len(values) >= limit:
            break
    return values


def infer_role(name: str, series: pd.Series) -> str:
    lower = str(name).lower()
    non_null = series.dropna()
    as_text = non_null.astype(str).str.strip()
    unique_ratio = float(as_text.nunique() / max(len(as_text), 1))
    avg_len = float(as_text.str.len().mean() or 0)

    if any(k in lower for k in ["url", "link", "链接", "网址"]):
        return "link"
    if any(k in lower for k in ["time", "date", "时间", "日期"]):
        return "time"
    if any(k in lower for k in ["content", "text", "body", "comment", "内容", "正文", "文本", "评论", "描述", "说明"]):
        return "text"
    if any(k in lower for k in ["user", "author", "name", "用户", "作者", "昵称", "账号"]):
        return "person"
    if any(k in lower for k in ["source", "platform", "channel", "来源", "平台", "渠道"]):
        return "source"

    numeric = pd.to_numeric(non_null, errors="coerce")
    if len(non_null) and numeric.notna().mean() >= 0.85:
        return "numeric"
    parsed_dates = pd.to_datetime(non_null, errors="coerce")
    if len(non_null) and parsed_dates.notna().mean() >= 0.75:
        return "time"
    if avg_len >= 30:
        return "text"
    if unique_ratio <= 0.25:
        return "category"
    if unique_ratio >= 0.9:
        return "id_or_key"
    return "unknown"


def inspect(path: Path) -> dict[str, Any]:
    tables = read_tables(path)
    result: dict[str, Any] = {"file": str(path), "tables": []}
    for sheet_name, df in tables.items():
        columns = []
        for col in df.columns:
            series = df[col]
            columns.append(
                {
                    "name": str(col),
                    "role_guess": infer_role(str(col), series),
                    "non_empty": int(series.notna().sum()),
                    "missing_pct": round(float(series.isna().mean() * 100), 2) if len(series) else 0,
                    "examples": sample_values(series),
                }
            )
        result["tables"].append(
            {
                "name": str(sheet_name),
                "rows": int(len(df)),
                "columns": int(len(df.columns)),
                "column_summary": columns,
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Excel/CSV/TSV file to inspect")
    parser.add_argument("--json-out", help="Optional path to write JSON summary")
    args = parser.parse_args()

    summary = inspect(Path(args.path))
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
