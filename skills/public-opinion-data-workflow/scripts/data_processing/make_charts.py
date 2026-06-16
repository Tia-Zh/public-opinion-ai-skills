#!/usr/bin/env python3
"""Generate simple office-friendly charts from a table."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def read_table(path: Path, sheet: str | None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet or 0, dtype=object)
    if suffix == ".csv":
        return pd.read_csv(path, dtype=object, encoding="utf-8-sig")
    if suffix == ".tsv":
        return pd.read_csv(path, dtype=object, sep="\t", encoding="utf-8-sig")
    raise ValueError(f"Unsupported file type: {suffix}")


def setup_fonts() -> None:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def category_chart(df: pd.DataFrame, column: str, out_dir: Path, top_n: int) -> Path:
    counts = df[column].fillna("空值").astype(str).value_counts().head(top_n).sort_values()
    fig_height = max(4, min(10, 0.35 * len(counts) + 1.5))
    fig, ax = plt.subplots(figsize=(9, fig_height))
    counts.plot(kind="barh", ax=ax, color="#3B82F6")
    ax.set_title(f"{column}分布图")
    ax.set_xlabel("数量")
    ax.set_ylabel(column)
    fig.tight_layout()
    path = out_dir / f"{column}分布图.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def time_chart(df: pd.DataFrame, column: str, out_dir: Path) -> Path:
    dates = pd.to_datetime(df[column], errors="coerce").dropna()
    daily = dates.dt.date.value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    daily.plot(kind="line", marker="o", ax=ax, color="#16A34A")
    ax.set_title(f"{column}趋势图")
    ax.set_xlabel("日期")
    ax.set_ylabel("数量")
    fig.autofmt_xdate()
    fig.tight_layout()
    path = out_dir / f"{column}趋势图.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Excel/CSV/TSV file")
    parser.add_argument("--sheet", help="Excel sheet name")
    parser.add_argument("--category", action="append", default=[], help="Categorical column to chart; can be repeated")
    parser.add_argument("--time", action="append", default=[], help="Date/time column to chart; can be repeated")
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--out-dir", help="Output folder")
    args = parser.parse_args()

    setup_fonts()
    source = Path(args.path)
    out_dir = Path(args.out_dir) if args.out_dir else source.with_name(f"{source.stem}_图表_{datetime.now():%Y%m%d_%H%M%S}")
    out_dir.mkdir(parents=True, exist_ok=True)
    df = read_table(source, args.sheet)

    outputs = []
    for column in args.category:
        if column in df.columns:
            outputs.append(category_chart(df, column, out_dir, args.top_n))
    for column in args.time:
        if column in df.columns:
            outputs.append(time_chart(df, column, out_dir))

    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
