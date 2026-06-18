---
name: data-processing-assistant
description: "当用户需要处理 Excel、CSV、TSV、多工作表表格、采集数据、问卷、评论、日志或运营表时使用：检查文件结构，识别字段，合并多表，清洗文本，必要时去重或标记重复，关键词筛选，打标签，汇总统计，生成图表并导出可复核结果。本 skill 不绑定固定领域，应先理解数据结构和任务目标；如果遇到大规模中文评论情感、立场或舆情分类，且全量 AI 标注成本高或需要复核，应转入 large-scale-sentiment-analysis 专项流程。"
---

# Data Processing Assistant

## Overview

Use this skill for general-purpose data processing work. Do not assume the data is about comments, public opinion, social media, or any fixed domain; first inspect the file, infer the schema, and ask only for decisions that cannot be safely inferred.

The goal is to make Codex behave like a careful data-processing colleague: understandable steps, previewable outputs, no hidden destructive edits, and export files that a non-technical user can open and trust.

## Default Workflow

1. Inspect the source file before transforming it. For Excel workbooks, examine every relevant sheet separately.
2. Identify the user's actual goal: cleaning, merging, extracting columns, filtering samples, deduplicating, labeling, clustering, summarizing, charting, exporting, or diagnosing a failed run.
3. Infer candidate roles for columns, but present them as recommendations when the choice affects results.
4. Decide whether ordinary labeling is enough or whether a specialist workflow is needed.
5. Preserve traceability unless the user asks otherwise: source file, source sheet, source row number, and processing notes are useful for auditing.
6. If data contains user-generated comments, account fields, links, IDs, locations, or contact-like fields, run a privacy/de-identification check before AI labeling or external sharing.
7. Apply transformations in small named steps. After each risky step, report before/after row counts and a small preview.
8. Export a new file. Never overwrite the user's original data unless explicitly requested.
9. Keep explanations plain-language and user-facing. Avoid exposing implementation details unless the user asks why something happened.

## Specialist Handoff

For sentiment, stance, or public-opinion classification, first choose the route:

- Stay in this main skill when the dataset is small, the label set is simple, the user accepts full AI labeling, or the task only needs broad positive/neutral/negative labels.
- Use the `large-scale-sentiment-analysis` workflow when the dataset is large, Chinese comments are semantically difficult, full AI labeling would be too costly, labels are more detailed than positive/neutral/negative, or the user needs low-confidence review, boundary cases, sarcasm review, audit samples, and denominator disclosure.

When handing off, prepare:

- input file path;
- text column;
- optional source/platform, date/time, and ID/link/hash columns;
- proposed label taxonomy;
- raw row count and cleaned row count if already known;
- output folder.

After the specialist workflow returns outputs, continue this main workflow to merge the specialist results into the final workbook, charts, and plain-language summary.

## When To Ask

Ask a concise question when:

- The main processing column cannot be inferred from the data.
- Multiple sheets appear structurally different and merging would be ambiguous.
- A filter could mean "any term matched" or "all terms matched".
- A dedupe rule could delete materially different records.
- Labeling is requested but the label set or judgment standard is unclear.

Otherwise, make a reasonable assumption, state it briefly, and continue.

## Common Operations

- **Inspect**: summarize sheets, columns, row counts, null rates, examples, and likely column roles.
- **Normalize fields**: map differently named columns into common output names when the user wants a combined table.
- **Merge sheets**: combine sheets only after aligning columns and preserving source sheet and source row.
- **Clean text**: trim spaces, normalize newlines, remove empty values, optionally strip URLs, mentions, emoji, or boilerplate.
- **Duplicate handling**: mark duplicates by hash/count by default when repeated volume may matter; deduplicate by exact text, normalized text, prefix length, selected key columns, or fuzzy similarity only when justified by the task or requested by the user.
- **Filter**: keywords with any/all matching, date range, numeric range, category inclusion/exclusion, missing/non-missing values.
- **Semantic judgment**: field recognition, exclusion-word suggestions, sentiment labels, topic labels, summaries, and clustering labels.
- **Topic discovery**: when the user has no preset categories, use rough clustering to discover candidate themes, then ask the user or an LLM to name/merge the clusters before treating them as report categories.
- **Privacy audit**: inspect likely sensitive columns and risky text patterns before AI labeling or export.
- **Large-scale sentiment handoff**: for high-volume or nuanced Chinese comments, use active-learning sentiment analysis instead of full-row AI labeling.
- **Analyze**: distributions, crosstabs, time trends, grouped summaries, top terms, and outlier checks.
- **Visualize**: bar charts, line charts, stacked charts, heatmaps, scatter plots, and cluster maps when suitable.
- **Export**: processed data, removed rows, step log, charts, and a short explanation sheet.

## Script Shortcuts

Use bundled scripts when they fit; patch or extend them for the user's exact task when needed.

Before running scripts, reuse an existing Python environment that already has the needed packages instead of reinstalling in every new session. For table work, `pandas` is the core dependency and `openpyxl` is needed for Excel read/write. If the current environment is missing them, check other available Python commands such as `python`, `python3`, or `py` before asking the user to install packages. Only install packages after user approval.

- `scripts/inspect_tabular.py`: inspect Excel/CSV/TSV files and produce a schema summary.
- `scripts/process_tabular.py`: run configurable cleaning, merging, filtering, duplicate marking or optional dedupe, and export.
- `scripts/make_charts.py`: generate common charts from processed tables.
- `scripts/discover_topics.py`: use dependency-light TF-IDF + k-means to discover rough candidate topics when no category taxonomy is provided.
- `scripts/privacy_audit.py`: identify likely sensitive columns and text patterns that should be hashed, masked, or dropped.

Example:

```powershell
python C:\Users\tiazhai\.codex\skills\data-processing-assistant\scripts\inspect_tabular.py "input.xlsx"
```

## References

Read only the reference needed for the current task:

- `references/workflow.md`: detailed step-by-step processing procedure.
- `references/field_inference.md`: generic field role inference and alias guidance.
- `references/ai_interface.md`: how Codex should use its own judgment safely for labels, topics, and suggestions.
- `references/sentiment_labeling.md`: sentiment label standards and output format.
- `references/sentiment_handoff.md`: when and how to route from this main skill to the large-scale sentiment specialist skill.
- `references/output_standards.md`: export, chart, and audit-log conventions.

## Quality Bar

Before final delivery, verify that:

- The output file exists and opens or can be read back.
- Row counts are explainable.
- Removed rows, if any, are either exported separately or summarized.
- Column names are understandable to non-technical users.
- Charts have meaningful titles, axis labels, and readable text.
- Judgment-based labels include confidence or review notes when the task is subjective.
- Large-scale sentiment outputs disclose raw rows, cleaned rows, excluded/uncertain rows, and the denominator used for percentages.
