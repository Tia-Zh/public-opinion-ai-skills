---
name: public-opinion-data-workflow
description: "当需要端到端处理中文舆情、社交媒体、问卷、评论或采集表格数据时使用：检查 Excel/CSV 文件，识别字段，标准化多表，清洗文本，标记重复、关键词筛选，生成图表，导出可复核结果；当情感或立场分析样本量大、全量 AI 成本高或需要复核时，转入抽样 AI 标注、分类器迁移、低置信度复核和质量摘要流程。"
---

# Public Opinion Data Workflow

Use this skill as the recommended single installable entrypoint for Chinese public-opinion data processing and large-scale comment sentiment/stance analysis. It combines the general table-processing workflow with the specialist large-scale Chinese sentiment workflow.

## Default Route

1. Inspect the source file before transforming it. For Excel workbooks, examine every relevant sheet.
2. Infer field roles: text, source/platform, date/time, ID/link/hash, author/user, metrics, category, and unknown.
3. Normalize fields across sheets only after preserving traceability: source file, source sheet, and source row.
4. De-identify before exporting or sending samples to an external AI: hash sensitive ID/user/link/location fields and mask URL, @handle, email, phone, or long numeric strings inside text.
5. Clean text, remove only clearly empty or task-irrelevant rows, mark short/duplicated rows, filter keywords when requested, and generate previewable logs.
6. Decide whether the task needs ordinary labels or the large-scale sentiment workflow.
7. If sentiment/stance labels are not defined yet, do not force positive/neutral/negative. First sample, discover expression clusters, ask AI or the user to name/merge candidate attitude labels, then confirm the label taxonomy.
8. Export new files only. Never overwrite the user's original data unless explicitly asked.

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
- `process_tabular.py`: configurable merge, clean, filter, optional dedupe, and export.
- `make_charts.py`: generate distribution and trend charts.
- `discover_topics.py`: use dependency-light TF-IDF + k-means to discover rough candidate topics when no category taxonomy is provided.
- `privacy_audit.py`: inspect likely sensitive columns and risky text patterns before AI labeling or export.

Core requirements:

- report before/after row counts for risky steps;
- keep removed rows or at least summarize why they were removed;
- preserve source sheet and row number;
- do not remove comments only because they are short; short attitude texts such as `[赞]`, `[强]`, `支持`, `赞成`, `点赞`, `反对`, or short complaint phrases may be valid public-opinion signals;
- do not collapse repeated comments silently; keep a volume view and, when useful, a deduplicated expression view with duplicate counts;
- do not run exact dedupe or prefix dedupe before sentiment/stance classification unless the user explicitly asks for a deduplicated expression view or spam cleanup;
- use understandable output column names;
- create charts with readable titles, labels, and fonts.
- do not present k-means clusters as final sentiment labels; use them for expression exploration, sampling, or draft attitude/theme naming.

## Large-Scale Sentiment Workflow

Use scripts in `scripts/sentiment/`:

- `prepare_text_data.py`: clean, hash sensitive fields, mark duplicates, and create stable `row_id`.
- `make_llm_batches.py`: create hybrid stratified AI-labeling samples and batch payloads.
- `merge_labels.py`: validate and merge AI labels.
- `train_text_classifier.py`: train a lightweight classifier from AI-reviewed labels and score confidence/margins.
- `select_uncertain.py`: select uncertain, low-confidence, sarcasm-like, and random audit rows.
- `build_summary_charts.py`: create monthly structure charts and denominator tables.
- `compare_labels.py`: optional evaluation when a reference label column already exists.

Recommended process:

1. If labels are provided, rewrite them into a compact taxonomy with definitions, inclusion/exclusion rules, examples, and edge cases.
2. If labels are not provided, create an exploratory sample and optionally run `discover_topics.py`; use clusters and keyword summaries only as evidence for drafting attitude/sentiment labels, not as final labels.
3. Confirm the label taxonomy before large-scale labeling.
4. Generate a hybrid stratified seed sample rather than sending every row to AI. Prefer platform/source and text-length coverage when available; use date/event strata only when useful and reliable.
5. Ask AI to label the sample with `row_id,label,confidence,reason,is_sarcasm`.
6. Merge and validate labels before training.
7. Validate label coverage: every final report label should have enough AI-reviewed examples before training, with a practical default of at least 20-30 examples per label.
8. Train/calibrate the classifier and score all cleaned rows.
9. Select low-confidence, boundary, sarcasm-like, and random samples for another review round.
10. Repeat until label distribution and audit consistency are stable enough for the use case.
11. Generate final tables, charts, and method notes.

Do not claim that every row was AI-labeled unless every row was actually sent to AI. If using the bundled classifier, describe it as classifier migration from AI-reviewed samples, not as full-row AI labeling.

Do not use classifier self-training as the normal path. Classifier predictions are not truth labels and should not be added back into the training set unless they have been AI-reviewed or human-confirmed. If pseudo-labeling is used only for an internal experiment, keep pseudo-labels separate, cap class additions per round, include neutral/weak-attitude samples deliberately, and do not treat the pseudo-labeled run as a deliverable result.

For three-class positive/neutral/negative runs, neutral is a real report label, not a leftover category. Include neutral examples in seed samples, uncertain samples, and audits. If many neutral rows shift to positive or negative between rounds, review those transitions before reporting.

When positive or negative shares become high, audit likely failure modes before treating the distribution as final:

- short attitude texts that may have been filtered or under-sampled;
- duplicate short texts whose repeated volume changes the share;
- questions and rhetorical questions;
- off-topic or adjacent-policy demands;
- rows that changed labels between rounds.

After each AI-labeled sample batch, check the label distribution before training. If the training sample is extremely imbalanced, such as nearly all negative or almost no neutral in a three-class task, pause and audit the labeling method before training. Do not proceed when the labels were produced by a keyword or heuristic script pretending to be AI semantic labeling. First supplement underrepresented labels, AI-review the candidates, and rerun the coverage check.

## Label Taxonomy Guidance

For public-opinion sentiment tasks, define:

- user-requested output labels, such as positive, neutral, negative, or the four categories named by the user;
- internal processing labels or flags needed for relevance, denominator, exclusion, and review, even when the user did not name them;
- exclusion labels such as irrelevant/off-topic, spam, or low-information when they should be reported separately instead of being forced into neutral;
- review statuses such as needs-review, model-uncertain, conflict, or insufficient-context when they should trigger review rather than become final report labels;
- concise criteria for each label;
- examples and counterexamples;
- how to treat sarcasm, mixed positive/negative sentiment, low-context comments, and off-topic promotional text.

Treat the user's requested labels as final output labels, not as the entire internal analysis schema. For example, when the user asks for `正面/中性/负面`, first decide whether each row is relevant and meaningful. Only relevant/effective rows enter the `正面/中性/负面` denominator. Off-topic, spam, and unusable low-information rows should be counted separately and excluded from the sentiment denominator unless the user explicitly asks to include them.

When the task is a new issue, create the taxonomy from evidence:

1. sample across platform/source, time, text length, and likely events;
2. summarize recurring attitudes and noise patterns;
3. use k-means/keywords only to reveal expression clusters;
4. merge clusters into business-meaningful attitude labels;
5. ask the user to confirm the final taxonomy before full-data classification.

## References

Load only what is needed:

- `references/workflow.md`: detailed data-processing steps.
- `references/field_inference.md`: field role inference.
- `references/output_standards.md`: export and chart standards.
- `references/sentiment_handoff.md`: route selection between general and specialist workflows.
- `references/sentiment_labeling.md`: basic sentiment label standards.
- `references/llm_labeling_prompt.md`: prompt template for AI labeling.
- `references/method_note.md`: method wording for reports.
- `references/evaluation.md`: optional reference-label comparison and audit guidance.
- `references/privacy.md`: de-identification and privacy-risk handling.

## Quality Bar

Before final delivery:

- verify output files exist and can be read back;
- explain raw rows, cleaned rows, removed rows, labeled rows, and final denominator;
- explain whether repeated comments are counted as volume or deduplicated expressions;
- explain how short attitude texts were handled;
- disclose whether labels are AI-labeled, weak-rule labels, classifier-migrated labels, or reviewed labels;
- disclose whether the label taxonomy was user-provided or built from exploratory samples;
- generate overall label distribution for every sentiment run; generate monthly/event charts only when a usable date/event column exists or the user asks for trend analysis;
- avoid presenting small-sample tests as final accuracy;
- include audit samples when results are subjective.
