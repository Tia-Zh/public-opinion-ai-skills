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
    ap.add_argument("--date-col", default="", help="Optional date column. Monthly charts are generated only when this column exists and has valid dates.")
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

    valid = df[df[args.label_col].isin(labels)].copy()
    overall_counts = valid[args.label_col].value_counts().reindex(labels).fillna(0).astype(int)
    overall_props = (overall_counts / overall_counts.sum()).fillna(0) if overall_counts.sum() else overall_counts.astype(float)
    pd.DataFrame({"label": labels, "count": overall_counts.values, "share": overall_props.values}).to_csv(
        out_dir / "overall_label_distribution.csv", index=False, encoding="utf-8-sig"
    )

    fig, ax = plt.subplots(figsize=(11, 6), dpi=160)
    x = np.arange(len(labels))
    vals = overall_props.reindex(labels).to_numpy()
    ax.bar(x, vals)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylim(0, 1)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_yticklabels([f"{int(v*100)}%" for v in np.linspace(0, 1, 6)])
    ax.set_ylabel("Share within effective labels")
    ax.grid(axis="y", color="#dddddd")
    plt.tight_layout()
    plt.savefig(out_dir / "overall_label_distribution.png", bbox_inches="tight")
    plt.close(fig)

    make_monthly = bool(args.date_col) and args.date_col in df.columns
    if make_monthly:
        parsed_dates = pd.to_datetime(df[args.date_col], errors="coerce")
        make_monthly = parsed_dates.notna().any()

    if make_monthly:
        df["month"] = parsed_dates.dt.to_period("M").astype(str)
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
    else:
        pd.DataFrame(
            [{"note": "Monthly chart skipped because no usable date column was provided."}]
        ).to_csv(out_dir / "monthly_chart_skipped.csv", index=False, encoding="utf-8-sig")

    if risk_labels:
        available_risk = [c for c in risk_labels if c in overall_props.index]
        risk_share = float(overall_props.reindex(available_risk).fillna(0).sum()) if available_risk else 0.0
        pd.DataFrame([{"risk_share": risk_share, "risk_labels": ",".join(available_risk)}]).to_csv(
            out_dir / "overall_risk_share.csv", index=False, encoding="utf-8-sig"
        )
    print(out_dir)


if __name__ == "__main__":
    main()
