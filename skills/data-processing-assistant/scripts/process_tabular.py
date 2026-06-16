#!/usr/bin/env python3
"""Configurable table processing: merge, clean, filter, dedupe, export."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_tables(path: Path, sheets: Any = "all") -> list[tuple[str, pd.DataFrame]]:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        data = pd.read_excel(path, sheet_name=None, dtype=object)
        if sheets != "all":
            wanted = {str(s) for s in sheets}
            data = {name: df for name, df in data.items() if str(name) in wanted}
        return [(str(name), df) for name, df in data.items()]
    if suffix == ".csv":
        return [("数据", pd.read_csv(path, dtype=object, encoding="utf-8-sig"))]
    if suffix == ".tsv":
        return [("数据", pd.read_csv(path, dtype=object, sep="\t", encoding="utf-8-sig"))]
    raise ValueError(f"Unsupported file type: {suffix}")


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    text = text.replace("\u3000", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def keyword_mask(series: pd.Series, terms: list[str], mode: str) -> pd.Series:
    cleaned_terms = [t.strip() for t in terms if str(t).strip()]
    if not cleaned_terms:
        return pd.Series([True] * len(series), index=series.index)
    text = series.fillna("").astype(str)
    masks = [text.str.contains(re.escape(term), case=False, na=False) for term in cleaned_terms]
    result = masks[0]
    for mask in masks[1:]:
        result = result & mask if mode == "all" else result | mask
    return result


def combine_tables(source: Path, config: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for sheet_name, df in read_tables(source, config.get("sheets", "all")):
        df = df.copy()
        df.insert(0, "来源行号", range(2, len(df) + 2))
        df.insert(0, "来源工作表", sheet_name)
        rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True, sort=False)


def process(config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    source = Path(config["source"])
    df = combine_tables(source, config)
    removed_parts: list[pd.DataFrame] = []
    log: list[dict[str, Any]] = []

    def record(step: str, before: int, after: int, params: Any = None) -> None:
        log.append({"步骤": step, "处理前行数": before, "处理后行数": after, "删除行数": before - after, "参数": json.dumps(params or {}, ensure_ascii=False)})

    rename_map = config.get("rename_map") or {}
    if rename_map:
        df = df.rename(columns=rename_map)

    text_columns = [c for c in config.get("text_columns", []) if c in df.columns]
    if text_columns:
        before = len(df)
        for col in text_columns:
            df[f"{col}_清洗后"] = df[col].map(clean_text)
        record("清洗文本", before, len(df), {"text_columns": text_columns})

    primary = config.get("primary_column")
    primary_clean = f"{primary}_清洗后" if primary and f"{primary}_清洗后" in df.columns else primary

    if config.get("drop_empty_primary") and primary_clean in df.columns:
        before = len(df)
        mask = df[primary_clean].fillna("").astype(str).str.strip().ne("")
        removed = df.loc[~mask].copy()
        removed["删除原因"] = "主要列为空"
        removed_parts.append(removed)
        df = df.loc[mask].copy()
        record("删除主要列为空", before, len(df), {"column": primary_clean})

    min_chars = config.get("min_chars")
    if min_chars and primary_clean in df.columns:
        before = len(df)
        mask = df[primary_clean].fillna("").astype(str).str.len() >= int(min_chars)
        removed = df.loc[~mask].copy()
        removed["删除原因"] = f"少于{min_chars}字"
        removed_parts.append(removed)
        df = df.loc[mask].copy()
        record("删除过短文本", before, len(df), {"column": primary_clean, "min_chars": min_chars})

    date_filter = config.get("date_filter") or {}
    date_col = date_filter.get("column")
    if date_col in df.columns and (date_filter.get("start") or date_filter.get("end")):
        before = len(df)
        dates = pd.to_datetime(df[date_col], errors="coerce")
        mask = dates.notna()
        if date_filter.get("start"):
            mask &= dates >= pd.to_datetime(date_filter["start"])
        if date_filter.get("end"):
            mask &= dates <= pd.to_datetime(date_filter["end"]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        removed = df.loc[~mask].copy()
        removed["删除原因"] = "不在日期范围内"
        removed_parts.append(removed)
        df = df.loc[mask].copy()
        record("日期筛选", before, len(df), date_filter)

    keyword_filter = config.get("keyword_filter") or {}
    terms = keyword_filter.get("terms") or []
    mode = keyword_filter.get("mode", "any")
    keyword_col = keyword_filter.get("column") or primary_clean
    if terms and keyword_col in df.columns:
        before = len(df)
        mask = keyword_mask(df[keyword_col], terms, mode)
        removed = df.loc[~mask].copy()
        removed["删除原因"] = "关键词未命中"
        removed_parts.append(removed)
        df = df.loc[mask].copy()
        df["命中关键词"] = df[keyword_col].fillna("").astype(str).map(lambda x: "、".join([t for t in terms if t and t.lower() in x.lower()]))
        record("关键词筛选", before, len(df), keyword_filter)

    dedupe = config.get("dedupe") or {}
    if dedupe.get("exact") and primary_clean in df.columns:
        before = len(df)
        duplicated = df.duplicated(subset=[primary_clean], keep="first")
        removed = df.loc[duplicated].copy()
        removed["删除原因"] = "完全相同去重"
        removed_parts.append(removed)
        df = df.loc[~duplicated].copy()
        record("完全相同去重", before, len(df), {"column": primary_clean})

    prefix_n = dedupe.get("prefix_n")
    if prefix_n and primary_clean in df.columns:
        before = len(df)
        helper = df[primary_clean].fillna("").astype(str).str.slice(0, int(prefix_n))
        duplicated = helper.duplicated(keep="first")
        removed = df.loc[duplicated].copy()
        removed["删除原因"] = f"前{prefix_n}字相同去重"
        removed_parts.append(removed)
        df = df.loc[~duplicated].copy()
        record(f"前{prefix_n}字相同去重", before, len(df), {"column": primary_clean, "prefix_n": prefix_n})

    keep_columns = config.get("keep_columns")
    if keep_columns:
        existing = [c for c in keep_columns if c in df.columns]
        df = df[existing].copy()

    removed_df = pd.concat(removed_parts, ignore_index=True, sort=False) if removed_parts else pd.DataFrame()
    return df, removed_df, log


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="JSON config path")
    args = parser.parse_args()
    config = load_config(Path(args.config))

    output = Path(config.get("output") or f"处理结果_{datetime.now():%Y%m%d_%H%M%S}.xlsx")
    output.parent.mkdir(parents=True, exist_ok=True)
    result, removed, log = process(config)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result.to_excel(writer, sheet_name="处理结果", index=False)
        if not removed.empty:
            removed.to_excel(writer, sheet_name="删除记录", index=False)
        pd.DataFrame(log).to_excel(writer, sheet_name="处理日志", index=False)
    print(str(output))


if __name__ == "__main__":
    main()
