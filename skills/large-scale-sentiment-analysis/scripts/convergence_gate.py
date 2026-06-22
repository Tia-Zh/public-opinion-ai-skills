#!/usr/bin/env python3
"""Decide whether an active-learning sentiment run is ready to stop.

The gate is intentionally conservative. It does not judge semantics and it does
not replace AI/human review. It checks whether enough objective evidence exists
to stop, continue, or audit before another round.
"""

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


def add_reason(rows: list[dict], level: str, code: str, message: str, metric: str = "", value: object = "") -> None:
    rows.append({"level": level, "code": code, "metric": metric, "value": value, "message": message})


def label_shares(df: pd.DataFrame, label_col: str, labels: list[str]) -> dict[str, float]:
    if label_col not in df.columns or not len(df):
        return {}
    counts = df[label_col].fillna("").astype(str).value_counts()
    order = labels or list(counts.index)
    shares = {label: float(counts.get(label, 0) / len(df)) for label in order}
    for label, count in counts.items():
        shares.setdefault(str(label), float(count / len(df)))
    return shares


def write_kv(rows: list[dict], output: Path) -> None:
    pd.DataFrame(rows).to_csv(output, index=False, encoding="utf-8-sig")


def check_reviewed_coverage(
    reviewed: pd.DataFrame | None,
    labels: list[str],
    label_col: str,
    min_per_label: int,
    reasons: list[dict],
    output_dir: Path,
) -> bool:
    rows = []
    ok = True
    if reviewed is None:
        add_reason(
            reasons,
            "blocker",
            "missing_reviewed_labels",
            "No AI/human-reviewed label file was provided, so label coverage cannot be verified.",
        )
        return False
    if label_col not in reviewed.columns:
        add_reason(reasons, "blocker", "missing_review_label_col", f"Reviewed labels file has no column: {label_col}")
        return False
    counts = reviewed[label_col].fillna("").astype(str).value_counts()
    for label in labels:
        count = int(counts.get(label, 0))
        status = "ok" if count >= min_per_label else "insufficient"
        if status != "ok":
            ok = False
            add_reason(
                reasons,
                "blocker",
                "insufficient_label_coverage",
                f"Target label has fewer than {min_per_label} reviewed examples: {label}",
                metric=f"reviewed_count:{label}",
                value=count,
            )
        rows.append({"label": label, "reviewed_count": count, "min_required": min_per_label, "status": status})
    for label, count in counts.items():
        if label not in labels:
            rows.append({"label": label, "reviewed_count": int(count), "min_required": "", "status": "extra_label"})
    pd.DataFrame(rows).to_csv(output_dir / "gate_label_coverage.csv", index=False, encoding="utf-8-sig")
    return ok


def check_new_batch_balance(
    new_reviewed: pd.DataFrame | None,
    label_col: str,
    max_top_share: float,
    reasons: list[dict],
    output_dir: Path,
) -> bool:
    if new_reviewed is None:
        return True
    if label_col not in new_reviewed.columns or not len(new_reviewed):
        add_reason(reasons, "warning", "new_batch_unavailable", "New reviewed batch is empty or missing the label column.")
        return True
    counts = new_reviewed[label_col].fillna("").astype(str).value_counts()
    top_label = str(counts.index[0])
    top_share = float(counts.iloc[0] / len(new_reviewed))
    pd.DataFrame(
        [{"label": str(label), "count": int(count), "share": float(count / len(new_reviewed))} for label, count in counts.items()]
    ).to_csv(output_dir / "gate_new_batch_distribution.csv", index=False, encoding="utf-8-sig")
    if top_share > max_top_share:
        add_reason(
            reasons,
            "blocker",
            "new_batch_imbalanced",
            "Latest reviewed batch is dominated by one label; audit sampling and duplicate concentration before training or stopping.",
            metric="new_batch_top_label_share",
            value=round(top_share, 4),
        )
        add_reason(reasons, "info", "new_batch_top_label", f"Top label is {top_label}.")
        return False
    return True


def check_distribution_stability(
    current: pd.DataFrame,
    previous: pd.DataFrame | None,
    labels: list[str],
    label_col: str,
    previous_label_col: str,
    max_delta: float,
    reasons: list[dict],
    output_dir: Path,
) -> bool:
    if previous is None:
        add_reason(
            reasons,
            "blocker",
            "missing_previous_predictions",
            "No previous-round prediction file was provided; distribution stability between rounds cannot be verified.",
        )
        return False
    cur = label_shares(current, label_col, labels)
    prev = label_shares(previous, previous_label_col, labels)
    if not cur or not prev:
        add_reason(reasons, "blocker", "missing_distribution_columns", "Cannot compute label distribution stability.")
        return False
    rows = []
    ok = True
    for label in labels or sorted(set(cur) | set(prev)):
        delta = cur.get(label, 0.0) - prev.get(label, 0.0)
        abs_delta = abs(delta)
        rows.append(
            {
                "label": label,
                "previous_share": round(prev.get(label, 0.0), 6),
                "current_share": round(cur.get(label, 0.0), 6),
                "delta": round(delta, 6),
                "abs_delta": round(abs_delta, 6),
                "status": "ok" if abs_delta <= max_delta else "changed_too_much",
            }
        )
        if abs_delta > max_delta:
            ok = False
            add_reason(
                reasons,
                "blocker",
                "distribution_not_stable",
                f"Label share changed more than {max_delta:.0%} between rounds: {label}",
                metric=f"abs_delta:{label}",
                value=round(abs_delta, 4),
            )
    pd.DataFrame(rows).to_csv(output_dir / "gate_distribution_delta.csv", index=False, encoding="utf-8-sig")
    return ok


def check_transition_drift(
    current: pd.DataFrame,
    previous: pd.DataFrame | None,
    row_id_col: str,
    label_col: str,
    previous_label_col: str,
    max_class_transition_rate: float,
    reasons: list[dict],
    output_dir: Path,
) -> bool:
    if previous is None:
        return False
    needed = {row_id_col, label_col}
    if not needed.issubset(current.columns) or row_id_col not in previous.columns or previous_label_col not in previous.columns:
        add_reason(reasons, "warning", "transition_unavailable", "Cannot compute label transition matrix due to missing columns.")
        return True
    cur = current[[row_id_col, label_col]].rename(columns={label_col: "current_label"})
    prev = previous[[row_id_col, previous_label_col]].rename(columns={previous_label_col: "previous_label"})
    merged = prev.merge(cur, on=row_id_col, how="inner")
    if not len(merged):
        add_reason(reasons, "warning", "transition_empty", "No overlapping row_id values between current and previous predictions.")
        return True
    matrix = pd.crosstab(merged["previous_label"], merged["current_label"])
    matrix.to_csv(output_dir / "gate_transition_matrix.csv", encoding="utf-8-sig")
    ok = True
    for prev_label, row in matrix.iterrows():
        row_total = int(row.sum())
        if row_total == 0:
            continue
        for cur_label, count in row.items():
            if str(prev_label) == str(cur_label):
                continue
            rate = float(count / row_total)
            if rate > max_class_transition_rate:
                ok = False
                add_reason(
                    reasons,
                    "blocker",
                    "label_transition_drift",
                    f"Too many rows moved from {prev_label} to {cur_label}; review this transition before stopping.",
                    metric=f"transition_rate:{prev_label}->{cur_label}",
                    value=round(rate, 4),
                )
    return ok


def check_audit_agreement(
    audit: pd.DataFrame | None,
    predicted_col: str,
    confirmed_col: str,
    max_error_share: float,
    reasons: list[dict],
    output_dir: Path,
) -> bool:
    if audit is None:
        add_reason(
            reasons,
            "blocker",
            "missing_audit_labels",
            "No random/targeted audit label file was provided; audit agreement cannot be verified.",
        )
        return False
    if predicted_col not in audit.columns or confirmed_col not in audit.columns:
        add_reason(reasons, "blocker", "missing_audit_columns", "Audit file must contain predicted and confirmed label columns.")
        return False
    usable = audit[audit[predicted_col].notna() & audit[confirmed_col].notna()].copy()
    if not len(usable):
        add_reason(reasons, "blocker", "empty_audit_labels", "Audit file has no usable predicted/confirmed label pairs.")
        return False
    errors = usable[predicted_col].astype(str).ne(usable[confirmed_col].astype(str))
    error_share = float(errors.mean())
    pd.DataFrame(
        [
            {
                "audit_rows": len(usable),
                "error_rows": int(errors.sum()),
                "error_share": round(error_share, 4),
                "max_error_share": max_error_share,
                "status": "ok" if error_share <= max_error_share else "too_many_errors",
            }
        ]
    ).to_csv(output_dir / "gate_audit_agreement.csv", index=False, encoding="utf-8-sig")
    if error_share > max_error_share:
        add_reason(
            reasons,
            "blocker",
            "audit_error_too_high",
            "Audit sample has too many classifier-vs-review disagreements.",
            metric="audit_error_share",
            value=round(error_share, 4),
        )
        return False
    return True


def check_low_confidence(
    current: pd.DataFrame,
    confidence_col: str,
    threshold: float,
    high_share: float,
    audit_ok: bool,
    reasons: list[dict],
) -> bool:
    if confidence_col not in current.columns or not len(current):
        add_reason(reasons, "warning", "confidence_unavailable", "Confidence column is unavailable; low-confidence diagnostics skipped.")
        return True
    conf = pd.to_numeric(current[confidence_col], errors="coerce")
    share = float((conf.lt(threshold) | conf.isna()).mean())
    if share > high_share:
        level = "warning" if audit_ok else "blocker"
        code = "high_low_confidence_audited" if audit_ok else "high_low_confidence_needs_audit"
        add_reason(
            reasons,
            level,
            code,
            "Low confidence is high. It can be acceptable only after audit shows few obvious errors and the cause is explainable.",
            metric="low_confidence_share",
            value=round(share, 4),
        )
        return audit_ok
    add_reason(reasons, "info", "low_confidence_checked", "Low-confidence share checked.", "low_confidence_share", round(share, 4))
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--previous-predictions", default="")
    parser.add_argument("--reviewed-labels", default="", help="Merged AI/human-reviewed training labels.")
    parser.add_argument("--new-reviewed-labels", default="", help="Latest AI/human-reviewed batch labels.")
    parser.add_argument("--audit-labels", default="", help="Random or targeted audit rows with predicted and confirmed labels.")
    parser.add_argument("--target-labels", required=True, help="Comma-separated final report labels.")
    parser.add_argument("--row-id-col", default="row_id")
    parser.add_argument("--label-col", default="predicted_label")
    parser.add_argument("--previous-label-col", default="predicted_label")
    parser.add_argument("--review-label-col", default="label")
    parser.add_argument("--audit-predicted-col", default="predicted_label")
    parser.add_argument("--audit-confirmed-col", default="label")
    parser.add_argument("--confidence-col", default="predicted_confidence")
    parser.add_argument("--min-reviewed-per-label", type=int, default=20)
    parser.add_argument("--review-rounds", type=int, default=0, help="Number of completed AI/human review rounds.")
    parser.add_argument("--min-review-rounds", type=int, default=2)
    parser.add_argument("--max-distribution-delta", type=float, default=0.05)
    parser.add_argument("--max-audit-error-share", type=float, default=0.15)
    parser.add_argument("--max-new-batch-top-label-share", type=float, default=0.8)
    parser.add_argument("--max-class-transition-rate", type=float, default=0.2)
    parser.add_argument("--low-confidence-threshold", type=float, default=0.6)
    parser.add_argument("--high-low-confidence-share", type=float, default=0.9)
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    current = pd.read_csv(Path(args.predictions).expanduser().resolve(), encoding="utf-8-sig")
    previous = read_csv(args.previous_predictions)
    reviewed = read_csv(args.reviewed_labels)
    new_reviewed = read_csv(args.new_reviewed_labels)
    audit = read_csv(args.audit_labels)
    labels = split_labels(args.target_labels)
    reasons: list[dict] = []

    if not labels:
        add_reason(reasons, "blocker", "missing_target_labels", "Provide --target-labels so the gate can check label coverage and distribution.")

    if args.review_rounds < args.min_review_rounds:
        add_reason(
            reasons,
            "blocker",
            "not_enough_review_rounds",
            "Completed review rounds are below the minimum. Do not call the result final yet.",
            metric="review_rounds",
            value=args.review_rounds,
        )

    coverage_ok = check_reviewed_coverage(reviewed, labels, args.review_label_col, args.min_reviewed_per_label, reasons, output_dir)
    new_batch_ok = check_new_batch_balance(new_reviewed, args.review_label_col, args.max_new_batch_top_label_share, reasons, output_dir)
    distribution_ok = check_distribution_stability(
        current,
        previous,
        labels,
        args.label_col,
        args.previous_label_col,
        args.max_distribution_delta,
        reasons,
        output_dir,
    )
    transition_ok = check_transition_drift(
        current,
        previous,
        args.row_id_col,
        args.label_col,
        args.previous_label_col,
        args.max_class_transition_rate,
        reasons,
        output_dir,
    )
    audit_ok = check_audit_agreement(
        audit,
        args.audit_predicted_col,
        args.audit_confirmed_col,
        args.max_audit_error_share,
        reasons,
        output_dir,
    )
    low_conf_ok = check_low_confidence(
        current,
        args.confidence_col,
        args.low_confidence_threshold,
        args.high_low_confidence_share,
        audit_ok,
        reasons,
    )

    blocker_codes = [row["code"] for row in reasons if row["level"] == "blocker"]
    if not blocker_codes:
        status = "candidate_stop"
        can_stop = True
    elif any(code in blocker_codes for code in ["missing_audit_labels", "high_low_confidence_needs_audit", "label_transition_drift", "new_batch_imbalanced"]):
        status = "audit_needed"
        can_stop = False
    elif any(code in blocker_codes for code in ["missing_reviewed_labels", "not_enough_review_rounds", "insufficient_label_coverage", "distribution_not_stable"]):
        status = "continue"
        can_stop = False
    else:
        status = "incomplete"
        can_stop = False

    metrics = [
        {"metric": "coverage_ok", "value": coverage_ok},
        {"metric": "new_batch_ok", "value": new_batch_ok},
        {"metric": "distribution_ok", "value": distribution_ok},
        {"metric": "transition_ok", "value": transition_ok},
        {"metric": "audit_ok", "value": audit_ok},
        {"metric": "low_confidence_ok", "value": low_conf_ok},
        {"metric": "blocker_count", "value": len(blocker_codes)},
        {"metric": "warning_count", "value": len([row for row in reasons if row["level"] == "warning"])},
    ]
    write_kv(metrics, output_dir / "gate_metrics.csv")
    pd.DataFrame(reasons).to_csv(output_dir / "gate_reasons.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {
                "status": status,
                "can_stop": can_stop,
                "meaning": {
                    "candidate_stop": "Objective checks allow stopping candidate; AI/user should still confirm business acceptability.",
                    "audit_needed": "Do not stop or iterate blindly; review targeted audit samples first.",
                    "continue": "Continue labeling/retraining before final reporting.",
                    "incomplete": "Required evidence is missing; result can only be described as incomplete.",
                }[status],
                "blockers": ",".join(blocker_codes),
            }
        ]
    ).to_csv(output_dir / "gate_decision.csv", index=False, encoding="utf-8-sig")
    print(output_dir / "gate_decision.csv")


if __name__ == "__main__":
    main()
