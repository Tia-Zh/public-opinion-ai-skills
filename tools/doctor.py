#!/usr/bin/env python3
"""Repository health check for the public opinion AI skills."""

from __future__ import annotations

import argparse
import py_compile
import importlib.util
import sys
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "data-processing-assistant": [
        "SKILL.md",
        "agents/openai.yaml",
        "scripts/inspect_tabular.py",
        "scripts/process_tabular.py",
        "scripts/make_charts.py",
        "scripts/discover_topics.py",
        "scripts/privacy_audit.py",
    ],
    "large-scale-sentiment-analysis": [
        "SKILL.md",
        "agents/openai.yaml",
        "scripts/prepare_text_data.py",
        "scripts/make_llm_batches.py",
        "scripts/merge_labels.py",
        "scripts/train_text_classifier.py",
        "scripts/select_uncertain.py",
        "scripts/build_summary_charts.py",
        "scripts/compare_labels.py",
    ],
    "public-opinion-data-workflow": [
        "SKILL.md",
        "agents/openai.yaml",
        "scripts/data_processing/inspect_tabular.py",
        "scripts/data_processing/process_tabular.py",
        "scripts/data_processing/make_charts.py",
        "scripts/data_processing/discover_topics.py",
        "scripts/data_processing/privacy_audit.py",
        "scripts/sentiment/prepare_text_data.py",
        "scripts/sentiment/train_text_classifier.py",
        "scripts/sentiment/compare_labels.py",
    ],
}
DOCS = ["README.md", "INSTALL.md", "QUICKSTART.md", "METHOD.md", "PRIVACY.md", "EVALUATION.md", "ROADMAP.md"]
EXAMPLES = ["examples/sample_comments.csv", "examples/demo_prompts.md"]
ZIPS = [
    "data-processing-assistant-installable.zip",
    "large-scale-sentiment-analysis-installable.zip",
    "public-opinion-data-workflow-integrated-installable.zip",
]


def ok(message: str) -> None:
    print(f"[OK] {message}")


def fail(message: str) -> None:
    print(f"[FAIL] {message}")


def check_file(path: Path) -> bool:
    if path.exists() and path.stat().st_size > 0:
        ok(str(path.relative_to(ROOT)))
        return True
    fail(str(path.relative_to(ROOT)))
    return False


def check_skill(skill: str, files: list[str]) -> bool:
    good = True
    base = ROOT / "skills" / skill
    for rel in files:
        good &= check_file(base / rel)
    skill_md = base / "SKILL.md"
    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8")
        good &= "name:" in text.split("---", 2)[1] and "description:" in text.split("---", 2)[1]
    return good


def check_zip(name: str) -> bool:
    path = ROOT / "dist" / name
    if not check_file(path):
        return False
    with ZipFile(path) as z:
        names = set(z.namelist())
        if "SKILL.md" not in names:
            fail(f"{name}: missing SKILL.md")
            return False
    ok(f"{name}: installable structure")
    return True


def check_docs() -> bool:
    good = True
    print("\n# docs")
    for rel in DOCS:
        good &= check_file(ROOT / rel)
    print("\n# examples")
    for rel in EXAMPLES:
        good &= check_file(ROOT / rel)
    return good


def check_compile() -> bool:
    print("\n# python script compile")
    good = True
    scripts = list((ROOT / "skills").glob("*/scripts/**/*.py")) + list((ROOT / "tools").glob("*.py"))
    for script in scripts:
        try:
            py_compile.compile(str(script), doraise=True)
            ok(f"compile: {script.relative_to(ROOT)}")
        except Exception as exc:
            fail(f"compile: {script.relative_to(ROOT)} ({exc})")
            good = False
    return good


def check_demo(demo_dir: Path | None) -> bool:
    if not demo_dir:
        return True
    print("\n# local demo package")
    required = [
        "README.md",
        "RUNBOOK.md",
        "raw_sample/synthetic_public_opinion_raw.csv",
        "deidentified_sample/synthetic_public_opinion_deidentified.csv",
        "outputs/quality_summary.md",
        "test_log.csv",
        "issue_log.csv",
    ]
    good = True
    for rel in required:
        path = demo_dir / rel
        if path.exists() and path.stat().st_size > 0:
            ok(str(path))
        else:
            fail(str(path))
            good = False
    return good


def check_python_deps() -> bool:
    required = ["pandas", "openpyxl"]
    optional = ["matplotlib", "sklearn", "jieba"]
    good = True
    for mod in required:
        found = importlib.util.find_spec(mod) is not None
        good &= found
        (ok if found else fail)(f"python dependency: {mod}")
    for mod in optional:
        found = importlib.util.find_spec(mod) is not None
        print(f"[INFO] optional dependency {mod}: {'available' if found else 'not installed'}")
    return good


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-deps", action="store_true")
    ap.add_argument("--skip-compile", action="store_true")
    ap.add_argument("--demo-dir")
    args = ap.parse_args()
    good = True
    good &= check_docs()
    for skill, files in SKILLS.items():
        print(f"\n# {skill}")
        good &= check_skill(skill, files)
    print("\n# installable zips")
    for name in ZIPS:
        good &= check_zip(name)
    if not args.skip_deps:
        print("\n# python environment")
        good &= check_python_deps()
    if not args.skip_compile:
        good &= check_compile()
    if args.demo_dir:
        good &= check_demo(Path(args.demo_dir))
    print("\nPASS" if good else "\nCHECK FAILED")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
