import argparse
import json
from pathlib import Path

import pandas as pd


def normalize_row_id(series):
    return series.astype(str).str.strip()


def load_label_map(path):
    if not path:
        return {}
    p = Path(path).expanduser().resolve()
    if p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    df = pd.read_csv(p, encoding="utf-8-sig")
    if not {"alias", "canonical_label"}.issubset(df.columns):
        raise ValueError("Label map CSV must contain alias,canonical_label columns")
    return dict(zip(df["alias"].astype(str), df["canonical_label"].astype(str)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepared", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--valid-labels", required=True, help="Comma-separated labels")
    ap.add_argument("--label-map", default="", help="Optional JSON or CSV alias-to-canonical label map")
    args = ap.parse_args()

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    prepared = pd.read_csv(Path(args.prepared).expanduser().resolve(), encoding="utf-8-sig")
    labels = pd.read_csv(Path(args.labels).expanduser().resolve(), encoding="utf-8-sig")
    labels.columns = [str(c).strip() for c in labels.columns]

    required = ["row_id", "label", "confidence", "reason", "is_sarcasm"]
    missing_cols = [c for c in required if c not in labels.columns]
    if missing_cols:
        raise ValueError(f"Missing label columns: {missing_cols}")

    prepared["row_id"] = normalize_row_id(prepared["row_id"])
    labels["row_id"] = normalize_row_id(labels["row_id"])

    label_map = load_label_map(args.label_map)
    if label_map:
        labels["label"] = labels["label"].astype(str).map(lambda value: label_map.get(value, value))

    valid_labels = {label.strip() for label in args.valid_labels.split(",") if label.strip()}
    invalid = labels[~labels["label"].isin(valid_labels)]
    dupes = labels[labels["row_id"].duplicated(keep=False)]
    missing_ids = sorted(set(prepared["row_id"]) - set(labels["row_id"]))

    merged = prepared.merge(labels, on="row_id", how="left")
    merged.to_csv(out_dir / "merged_labels.csv", index=False, encoding="utf-8-sig")

    summary = pd.DataFrame(
        [
            ["prepared_rows", len(prepared)],
            ["label_rows", len(labels)],
            ["missing_row_ids", len(missing_ids)],
            ["duplicate_row_ids", labels["row_id"].duplicated().sum()],
            ["invalid_labels", len(invalid)],
            ["mean_confidence", pd.to_numeric(labels["confidence"], errors="coerce").mean()],
        ],
        columns=["metric", "value"],
    )
    summary.to_csv(out_dir / "label_quality_summary.csv", index=False, encoding="utf-8-sig")
    invalid.to_csv(out_dir / "invalid_labels.csv", index=False, encoding="utf-8-sig")
    dupes.to_csv(out_dir / "duplicate_row_ids.csv", index=False, encoding="utf-8-sig")
    pd.Series(missing_ids, name="missing_row_id").to_csv(out_dir / "missing_row_ids.csv", index=False, encoding="utf-8-sig")
    print(out_dir / "merged_labels.csv")


if __name__ == "__main__":
    main()
