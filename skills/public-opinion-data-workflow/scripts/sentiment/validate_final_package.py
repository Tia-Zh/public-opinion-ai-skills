#!/usr/bin/env python3
"""Validate a public-opinion workflow output package before delivery.

This script does not judge sentiment quality. It checks whether the output
package contains the minimum evidence needed to present results responsibly.
Use it as the last scripted gate after convergence and denominator checks.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

import pandas as pd


def read_table(path: Path, sheet: str | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet or 0)
    return pd.read_csv(path)


def add(rows: list[dict[str, str]], check: str, status: str, evidence: str, action: str = "") -> None:
    rows.append({"check": check, "status": status, "evidence": evidence, "action": action})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, help="Directory containing run outputs.")
    parser.add_argument("--mode", choices=["general", "sentiment"], default="sentiment")
    parser.add_argument("--final-output", default="", help="Final row-level CSV/XLSX to validate.")
    parser.add_argument("--sheet", default=None, help="Excel sheet for --final-output when needed.")
    parser.add_argument(
        "--require-files",
        default="",
        help="Comma-separated artifacts that must exist relative to --output-dir.",
    )
    parser.add_argument("--report", default="final_package_validation.csv")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []

    if out_dir.exists():
        add(rows, "output_dir_exists", "pass", str(out_dir))
    else:
        add(rows, "output_dir_exists", "fail", str(out_dir), "Create the output directory.")

    final_output = Path(args.final_output) if args.final_output else None
    if final_output is not None and not final_output.is_absolute():
        final_output = out_dir / final_output

    if final_output:
        if final_output.exists():
            try:
                df = read_table(final_output, args.sheet)
                add(rows, "final_output_readable", "pass", f"{final_output} rows={len(df)} cols={len(df.columns)}")
            except Exception as exc:  # noqa: BLE001 - report validation failure cleanly
                add(rows, "final_output_readable", "fail", str(final_output), f"Cannot read file: {exc}")
        else:
            add(rows, "final_output_exists", "fail", str(final_output), "Create or pass the final row-level output.")
    else:
        add(rows, "final_output_provided", "warn", "", "Pass --final-output for final delivery validation.")

    for rel in [x.strip() for x in args.require_files.split(",") if x.strip()]:
        p = out_dir / rel
        if p.exists():
            add(rows, f"required_file:{rel}", "pass", str(p))
        else:
            add(rows, f"required_file:{rel}", "fail", str(p), "Generate this artifact or remove it from --require-files.")

    if args.mode == "sentiment":
        if final_output and final_output.exists():
            gate_script = Path(__file__).with_name("validate_denominator_gate.py")
            gate_report = out_dir / "denominator_gate_report.csv"
            cmd = [
                sys.executable,
                str(gate_script),
                "--input",
                str(final_output),
                "--output",
                str(gate_report),
            ]
            if args.sheet:
                cmd.extend(["--sheet", args.sheet])
            proc = subprocess.run(cmd, text=True, capture_output=True)
            if proc.returncode == 0:
                add(rows, "denominator_gate", "pass", str(gate_report))
            else:
                add(
                    rows,
                    "denominator_gate",
                    "fail",
                    str(gate_report),
                    "Fix denominator fields before reporting final sentiment/stance shares.",
                )
        else:
            add(rows, "denominator_gate", "fail", "", "Requires --final-output for sentiment mode.")

    statuses = {r["status"] for r in rows}
    overall = "fail" if "fail" in statuses else ("warn" if "warn" in statuses else "pass")
    add(rows, "overall", overall, "", "Deliver as final only when overall is pass.")

    report = Path(args.report)
    if not report.is_absolute():
        report = out_dir / report
    with report.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "status", "evidence", "action"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Final package validation: {overall}. Report written to {report}")
    if overall == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
