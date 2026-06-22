#!/usr/bin/env python3
"""Build deterministic diagnostics for one active-learning round."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def split_labels(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def read_csv(path: str | None) -> pd.DataFrame | None:
    if not path:
        return None
    return pd.read_csv(Path(path).expanduser().resolve(), encoding="utf-8-sig")


def label_distribution(df: pd.DataFrame, label_col: str, labels: list[str]) -> pd.DataFrame:
    if label_col not in df.columns:
        return pd.DataFrame(columns=["label", "count", "share"])
    counts = df[label_col].fillna("").astype(str).value_counts()
    order = labels or list(counts.index)
    rows = []
    total = len(df)
    for label in order:
        count = int(counts.get(label, 0))
        rows.append({"label": label, "count": count, "share": round(count / total, 4) if total else 0})
    for label, count in counts.items():
        if label not in order:
            rows.append({"label": label, "count": int(count), "share": round(int(count) / total, 4) if total else 0})
    return pd.DataFrame(rows)


def confidence_summary(df: pd.DataFrame, confidence_col: str, margin_col: str) -> pd.DataFrame:
    rows = []
    if confidence_col in df.columns:
        conf = pd.to_numeric(df[confidence_col], errors="coerce")
        rows.extend(
            [
                {"metric": "confidence_mean", "value": round(float(conf.mean()), 4) if conf.notna().any() else ""},
                {"metric": "confidence_median", "value": round(float(conf.median()), 4) if conf.notna().any() else ""},
                {"metric": "confidence_lt_0_6_share", "value": round(float(conf.lt(0.6).mean()), 4) if len(conf) else 0},
                {"metric": "confidence_lt_0_4_share", "value": round(float(conf.lt(0.4).mean()), 4) if len(conf) else 0},
            ]
        )
    if margin_col in df.columns:
        margin = pd.to_numeric(df[margin_col], errors="coerce")
        rows.extend(
            [
                {"metric": "top2_margin_mean", "value": round(float(margin.mean()), 4) if margin.notna().any() else ""},
                {"metric": "top2_margin_lt_0_15_share", "value": round(float(margin.lt(0.15).mean()), 4) if len(margin) else 0},
            ]
        )
    return pd.DataFrame(rows)


def transition_matrix(current: pd.DataFrame, previous: pd.DataFrame | None, row_id_col: str, label_col: str) -> pd.DataFrame:
    if previous is None:
        return pd.DataFrame()
    if row_id_col not in current.columns or row_id_col not in previous.columns:
        return pd.DataFrame()
    if label_col not in current.columns or label_col not in previous.columns:
        return pd.DataFrame()
    cur = current[[row_id_col, label_col]].rename(columns={label_col: "current_label"}).copy()
    prev = previous[[row_id_col, label_col]].rename(columns={label_col: "previous_label"}).copy()
    merged = prev.merge(cur, on=row_id_col, how="inner")
    if not len(merged):
        return pd.DataFrame()
    matrix = pd.crosstab(merged["previous_label"], merged["current_label"])
    return matrix.reset_index()


def audit_status(
    df: pd.DataFrame,
    label_col: str,
    confidence_col: str,
    margin_col: str,
    text_col: str,
    target_labels: list[str],
) -> pd.DataFrame:
    rows = [{"metric": "rows", "value": len(df), "status": "info", "note": ""}]
    total = len(df)

    if label_col in df.columns and total:
        counts = df[label_col].fillna("").astype(str).value_counts()
        top_label = str(counts.index[0]) if len(counts) else ""
        top_share = float(counts.iloc[0] / total) if len(counts) else 0.0
        rows.append(
            {
                "metric": "top_label_share",
                "value": round(top_share, 4),
                "status": "pause_and_audit" if top_share > 0.8 else "ok",
                "note": f"top_label={top_label}",
            }
        )
        missing = [label for label in target_labels if counts.get(label, 0) == 0]
        rows.append(
            {
                "metric": "missing_target_labels",
                "value": len(missing),
                "status": "supplement_before_training" if missing else "ok",
                "note": ",".join(missing),
            }
        )

    if confidence_col in df.columns and total:
        conf = pd.to_numeric(df[confidence_col], errors="coerce")
        low_share = float((conf.lt(0.6) | conf.isna()).mean())
        rows.append(
            {
                "metric": "low_confidence_share",
                "value": round(low_share, 4),
                "status": "diagnose_not_iterate_mechanically" if low_share > 0.9 else "info",
                "note": "Low confidence is a triage signal, not a backlog to exhaust.",
            }
        )

    if margin_col in df.columns and total:
        margin = pd.to_numeric(df[margin_col], errors="coerce")
        rows.append({"metric": "low_margin_share", "value": round(float((margin.lt(0.15) | margin.isna()).mean()), 4), "status": "info", "note": ""})

    if text_col in df.columns and total:
        key = df[text_col].fillna("").astype(str).str.strip()
        duplicate_extra_share = float((total - key.nunique()) / total)
        rows.append(
            {
                "metric": "duplicate_extra_share",
                "value": round(duplicate_extra_share, 4),
                "status": "dedupe_review_batch" if duplicate_extra_share > 0.3 else "info",
                "note": "Review unique expressions once, then map labels back to volume rows.",
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--previous-predictions", default="")
    parser.add_argument("--row-id-col", default="row_id")
    parser.add_argument("--label-col", default="predicted_label")
    parser.add_argument("--confidence-col", default="predicted_confidence")
    parser.add_argument("--margin-col", default="top2_margin")
    parser.add_argument("--text-col", default="clean_text")
    parser.add_argument("--target-labels", default="", help="Comma-separated final report labels.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    current = pd.read_csv(Path(args.predictions).expanduser().resolve(), encoding="utf-8-sig")
    previous = read_csv(args.previous_predictions)
    labels = split_labels(args.target_labels)

    label_distribution(current, args.label_col, labels).to_csv(output_dir / "round_label_distribution.csv", index=False, encoding="utf-8-sig")
    confidence_summary(current, args.confidence_col, args.margin_col).to_csv(output_dir / "round_confidence_summary.csv", index=False, encoding="utf-8-sig")
    audit_status(current, args.label_col, args.confidence_col, args.margin_col, args.text_col, labels).to_csv(
        output_dir / "round_audit_status.csv", index=False, encoding="utf-8-sig"
    )

    transitions = transition_matrix(current, previous, args.row_id_col, args.label_col)
    if len(transitions):
        transitions.to_csv(output_dir / "round_transition_matrix.csv", index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame([{"note": "No transition matrix generated; previous predictions or required columns were unavailable."}]).to_csv(
            output_dir / "round_transition_matrix_skipped.csv", index=False, encoding="utf-8-sig"
        )

    print(output_dir)


if __name__ == "__main__":
    main()
