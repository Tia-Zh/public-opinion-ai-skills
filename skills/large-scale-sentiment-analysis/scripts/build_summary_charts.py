import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def setup_fonts():
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--effective-labels", required=True, help="Comma-separated labels to chart")
    ap.add_argument("--risk-labels", default="")
    args = ap.parse_args()

    setup_fonts()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.merged, encoding="utf-8-sig")
    labels = args.effective_labels.split(",")
    risk_labels = [x for x in args.risk_labels.split(",") if x]

    df["month"] = pd.to_datetime(df[args.date_col], errors="coerce").dt.to_period("M").astype(str)
    valid = df[df[args.label_col].isin(labels)].copy()
    counts = pd.crosstab(valid["month"], valid[args.label_col]).reindex(columns=labels).fillna(0)
    props = counts.div(counts.sum(axis=1), axis=0).fillna(0)
    props.to_csv(out_dir / "monthly_label_shares.csv", encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(11, 6), dpi=160)
    x = np.arange(len(props))
    bottom = np.zeros(len(props))
    for label in labels:
        vals = props[label].to_numpy()
        ax.bar(x, vals, bottom=bottom, label=label)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(props.index, rotation=30, ha="right")
    ax.set_ylim(0, 1)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_yticklabels([f"{int(v*100)}%" for v in np.linspace(0, 1, 6)])
    ax.set_ylabel("Share within effective labels")
    ax.legend(ncol=min(4, len(labels)), loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False)
    ax.grid(axis="y", color="#dddddd")
    plt.tight_layout()
    plt.savefig(out_dir / "monthly_label_structure.png", bbox_inches="tight")
    plt.close(fig)

    if risk_labels:
        risk = props[[c for c in risk_labels if c in props.columns]].sum(axis=1)
        risk.to_csv(out_dir / "monthly_risk_share.csv", encoding="utf-8-sig")
    print(out_dir)


if __name__ == "__main__":
    main()
