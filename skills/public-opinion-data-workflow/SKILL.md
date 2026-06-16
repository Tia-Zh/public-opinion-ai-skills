---
name: public-opinion-data-workflow
description: "当需要端到端处理中文舆情、社交媒体、问卷、评论或采集表格数据时使用：检查 Excel/CSV 文件，识别字段，标准化多表，清洗文本，去重，关键词筛选，生成图表，导出可复核结果；当情感或立场分析样本量大、全量 AI 成本高或需要复核时，转入抽样 AI 标注、分类器迁移、低置信度复核和质量摘要流程。"
---

# Public Opinion Data Workflow

Use this skill as the single integrated workflow for public-opinion data processing. It combines the general table-processing workflow with the specialist large-scale Chinese sentiment workflow.

## Default Route

1. Inspect the source file before transforming it. For Excel workbooks, examine every relevant sheet.
2. Infer field roles: text, source/platform, date/time, ID/link/hash, author/user, metrics, category, and unknown.
3. Normalize fields across sheets only after preserving traceability: source file, source sheet, and source row.
4. Clean text, remove empty or low-information rows, deduplicate, filter keywords, and generate previewable logs.
5. Decide whether the task needs ordinary labels or the large-scale sentiment workflow.
6. Export new files only. Never overwrite the user's original data unless explicitly asked.

## Route Selection

Stay in the general workflow when:

- the task is cleaning, merging, deduplication, keyword filtering, charting, or exporting;
- the dataset is small enough for direct review or full AI labeling;
- labels are simple, such as positive/neutral/negative;
- the user does not need uncertainty review, sarcasm review, or denominator disclosure.

Switch to the large-scale sentiment workflow when:

- there are thousands or tens of thousands of Chinese comments;
- full-row AI labeling would be too costly or unstable;
- labels are more nuanced than positive/neutral/negative;
- sarcasm, mixed sentiment, low-context comments, or risk/stance categories matter;
- the user needs low-confidence samples, boundary samples, random audit samples, and report-ready denominator notes.

## General Data Processing Workflow

Use scripts in `scripts/data_processing/` when they fit:

- `inspect_tabular.py`: inspect Excel/CSV/TSV structure and likely field roles.
- `process_tabular.py`: configurable merge, clean, filter, dedupe, and export.
- `make_charts.py`: generate distribution and trend charts.

Core requirements:

- report before/after row counts for risky steps;
- keep removed rows or at least summarize why they were removed;
- preserve source sheet and row number;
- use understandable output column names;
- create charts with readable titles, labels, and fonts.

## Large-Scale Sentiment Workflow

Use scripts in `scripts/sentiment/`:

- `prepare_text_data.py`: clean, hash sensitive fields, deduplicate, and create stable `row_id`.
- `make_llm_batches.py`: create stratified AI-labeling samples and batch payloads.
- `merge_labels.py`: validate and merge AI labels.
- `train_text_classifier.py`: train a dependency-light baseline classifier and score confidence/margins.
- `select_uncertain.py`: select uncertain, low-confidence, sarcasm-like, and random audit rows.
- `build_summary_charts.py`: create monthly structure charts and denominator tables.

Recommended process:

1. Define a stable label taxonomy before labeling.
2. Generate a stratified seed sample rather than sending every row to AI.
3. Ask AI to label the sample with `row_id,label,confidence,reason,is_sarcasm`.
4. Merge and validate labels before training.
5. Train/calibrate the classifier and score all cleaned rows.
6. Select low-confidence, boundary, sarcasm-like, and random samples for another review round.
7. Repeat until label distribution and audit consistency are stable enough for the use case.
8. Generate final tables, charts, and method notes.

Do not claim that every row was AI-labeled unless every row was actually sent to AI. If using the bundled classifier, describe it as a lightweight baseline or rule-enhanced classifier, not as a production model.

## Label Taxonomy Guidance

For public-opinion sentiment tasks, define:

- final labels, such as positive, neutral, negative, risk concern, irrelevant/low-information, and uncertain;
- concise criteria for each label;
- examples and counterexamples;
- how to treat sarcasm, mixed positive/negative sentiment, low-context comments, and off-topic promotional text.

## References

Load only what is needed:

- `references/workflow.md`: detailed data-processing steps.
- `references/field_inference.md`: field role inference.
- `references/output_standards.md`: export and chart standards.
- `references/sentiment_handoff.md`: route selection between general and specialist workflows.
- `references/sentiment_labeling.md`: basic sentiment label standards.
- `references/llm_labeling_prompt.md`: prompt template for AI labeling.
- `references/method_note.md`: method wording for reports.

## Quality Bar

Before final delivery:

- verify output files exist and can be read back;
- explain raw rows, cleaned rows, removed rows, labeled rows, and final denominator;
- disclose whether labels are AI-labeled, weak-rule labels, classifier-migrated labels, or reviewed labels;
- avoid presenting small-sample tests as final accuracy;
- include audit samples when results are subjective.
