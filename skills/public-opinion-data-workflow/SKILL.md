---
name: public-opinion-data-workflow
description: "当需要端到端处理中文舆情、社交媒体、问卷、评论或采集表格数据时使用：检查 Excel/CSV 文件，识别字段，标准化多表，清洗文本，标记重复、关键词筛选，生成图表，导出可复核结果；当情感或立场分析样本量大、全量 AI 成本高或需要复核时，转入抽样 AI 标注、分类器迁移、低置信度复核和质量摘要流程。"
---

# Public Opinion Data Workflow

Use this skill as the recommended single installable entrypoint for Chinese public-opinion data processing and large-scale comment sentiment/stance analysis. It combines the general table-processing workflow with the specialist large-scale Chinese sentiment workflow.

## Operating Contract

Run stable scripts for mechanical work; use AI for semantic judgment. Scripts may inspect files, clean text, de-identify, mark duplicates, create batches, merge labels, train classifiers, select review samples, and validate gates. Scripts must not invent sentiment labels and call them AI labeling.

For sentiment or stance runs, do not output final percentages until all three gates are satisfied:

1. label evidence exists: labels come from AI semantic labeling or human review, not unreviewed keywords or classifier guesses;
2. convergence evidence exists: `convergence_gate.py` returns `candidate_stop`, or the run is clearly marked incomplete/diagnostic;
3. denominator evidence exists: `validate_denominator_gate.py` passes, with row-level denominator inclusion, exclusion reason, and effective denominator.

Route large sentiment/stance datasets to the large-scale workflow even when the requested labels are only `positive/neutral/negative`. Label simplicity does not remove the need for active learning when full AI labeling is costly or unstable.

Use `validate_final_package.py` as the last scripted check before delivery.

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
- the sentiment/stance dataset is small enough for direct full AI labeling or direct review;
- the user only needs a small-sample/basic labeling result and accepts that active-learning evidence is not being produced.

Switch to the large-scale sentiment workflow when:

- there are thousands or tens of thousands of Chinese comments;
- full-row AI labeling would be too costly or unstable;
- the task is sentiment/stance classification at large scale, even if the requested output labels are only positive/neutral/negative;
- labels are nuanced, rare, easily confused, or business-critical;
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

- `find_python_environment.py`: find an existing local Python environment with the needed packages before installing anything.
- `check_dependencies.py`: check current Python for core and recommended packages.
- `install_optional_dependencies.py`: install core/recommended packages only after user approval.
- `prepare_text_data.py`: clean, hash sensitive fields, mark duplicates, and create stable `row_id`.
- `profile_text_quality.py`: profile empty, short, emoji-only, low-information, duplicate, privacy-risk, and question-like rows.
- `make_llm_batches.py`: create hybrid stratified AI-labeling samples and batch payloads.
- `merge_labels.py`: validate and merge AI labels.
- `audit_active_learning_batch.py`: check label imbalance and duplicate concentration in newly labeled batches.
- `train_text_classifier.py`: train a lightweight classifier from AI-reviewed labels and score confidence/margins.
- `select_uncertain.py`: select uncertain, low-confidence, sarcasm-like, and random audit rows.
- `propagate_duplicate_labels.py`: map labels from unique reviewed expressions back to repeated rows.
- `diagnose_predictions.py`: summarize low-confidence, margin, label, and duplicate health before continuing iteration.
- `summarize_active_learning_round.py`: summarize each round's label distribution, confidence, audit status, and label transitions.
- `convergence_gate.py`: decide whether to continue, audit first, mark incomplete, or allow a stopping candidate.
- `validate_denominator_gate.py`: hard-check that final sentiment/stance outputs include denominator inclusion and exclusion-reason fields before shares are reported.
- `validate_final_package.py`: final delivery gate for readable outputs, denominator evidence, and required artifacts.
- `build_summary_charts.py`: create monthly structure charts and denominator tables.
- `compare_labels.py`: optional evaluation when a reference label column already exists.

Recommended process:

1. Reuse an existing working Python environment. Run `python scripts/sentiment/find_python_environment.py`; if it finds a `best_python`, use that executable or command for later scripts.
2. Check dependencies with `python scripts/sentiment/check_dependencies.py`. `pandas` is a core dependency for tabular processing, `openpyxl` is needed for Excel, and `scikit-learn` is the recommended classifier backend. If packages are missing from every usable Python environment, ask the user before running `python scripts/sentiment/install_optional_dependencies.py`.
3. If labels are provided, rewrite them into a compact taxonomy with definitions, inclusion/exclusion rules, examples, and edge cases.
4. If labels are not provided, create an exploratory sample and optionally run `discover_topics.py`; use clusters and keyword summaries only as evidence for drafting attitude/sentiment labels, not as final labels.
5. Confirm the label taxonomy before large-scale labeling.
6. Run `profile_text_quality.py` when short text, repeated expressions, platform emoji, URL/mention/contact text, or question-like rows may affect the denominator or error pattern.
7. Generate a hybrid stratified seed sample rather than sending every row to AI. Prefer platform/source and text-length coverage when available; use date/event strata only when useful and reliable.
8. Ask AI to label the sample with `row_id,label,confidence,reason,is_sarcasm`. Optionally export the same seed, boundary, transition, or audit samples for user review/correction; user labels can be a minimal `row_id,label` file.
9. Merge and validate AI/human-reviewed labels before training. For user-corrected labels, use `merge_labels.py --allow-minimal-labels --label-source human_reviewed`.
10. Audit batch health and validate label coverage: every final report label should have enough AI/human-reviewed examples before training, with a practical default of at least 20-30 examples per label.
11. Train/calibrate the classifier and score all cleaned rows.
12. Run `summarize_active_learning_round.py` after scoring, especially when comparing rounds or diagnosing label drift.
13. Select low-confidence, boundary, sarcasm-like, and random samples for another review round.
14. Repeat until label distribution and audit consistency are stable enough for the use case.
15. Before stopping, run `convergence_gate.py` with current predictions, previous predictions, merged reviewed labels, latest reviewed batch if available, and audit labels. Read `gate_decision.csv` first, then `gate_reasons.csv`. Do not call the run final unless the gate returns `candidate_stop`, or clearly disclose why the run stopped early.
16. Run `validate_denominator_gate.py` on the final row-level output. Do not report sentiment/stance shares until it passes.
17. Generate final tables, charts, and method notes.
18. Run `validate_final_package.py` on the deliverable folder before calling the output final.

Do not claim that every row was AI-labeled unless every row was actually sent to AI. If using the bundled classifier, describe it as classifier migration from AI-reviewed samples, not as full-row AI labeling.

Do not hard-code labels in Python, CSV, JSON, or dictionaries and present them as AI semantic labels. Scripts can prepare batches, preserve `row_id`, validate files, merge AI outputs, train classifiers, and generate summaries. They must not replace the semantic decision step. The sampled text must be read and labeled by the current AI agent's natural-language understanding or by an external LLM/API. Rule-generated labels are only candidates or diagnostics until AI-reviewed or human-confirmed.

Do not use classifier self-training as the normal path. Classifier predictions are not truth labels and should not be added back into the training set unless they have been AI-reviewed or human-confirmed. User-provided corrections are optional but should be treated as high-quality reviewed labels when present. If pseudo-labeling is used only for an internal experiment, keep pseudo-labels separate, cap class additions per round, include neutral/weak-attitude samples deliberately, and do not treat the pseudo-labeled run as a deliverable result.

For three-class positive/neutral/negative runs, neutral is a real report label, not a leftover category. Include neutral examples in seed samples, uncertain samples, and audits. If many neutral rows shift to positive or negative between rounds, review those transitions before reporting.

When positive or negative shares become high, audit likely failure modes before treating the distribution as final:

- short attitude texts that may have been filtered or under-sampled;
- duplicate short texts whose repeated volume changes the share;
- questions and rhetorical questions;
- off-topic or adjacent-policy demands;
- rows that changed labels between rounds.

After each AI-labeled sample batch, check the label distribution before training. If the training sample is extremely imbalanced, such as nearly all negative or almost no neutral in a three-class task, pause and audit the labeling method before training. Do not proceed when the labels were produced by a keyword or heuristic script pretending to be AI semantic labeling. First supplement underrepresented labels, AI-review the candidates, and rerun the coverage check.

For large subjective datasets, avoid tiny seed samples but do not overload the current AI agent. As practical defaults, use 200-400 AI-reviewed seed examples for 10,000-100,000 rows and 300-500 for larger or multi-platform datasets, split into batches of 50-100. Do not ask the current AI agent to label more than 500 seed examples in one pass. Smaller seeds are acceptable only for smoke tests and should not be presented as final quality.

When selecting uncertain samples for review, use unique text expressions first and preserve `duplicate_count` or equivalent volume fields. If many rows have the same `text_hash` or `clean_text`, label that expression once, then map the confirmed label back to all duplicate rows. This avoids spending review effort on repeated identical wording while still allowing repeated comments to count in the final volume denominator.

Active-learning guardrails: if one label is more than 80% of a newly AI-labeled batch, pause before training and audit sampling, duplicates, label definitions, and missing-class coverage. Do not estimate required rounds by `low-confidence row count / review batch size`. If more than 90% of rows are low-confidence after a round, first diagnose sampling strategy, denominator/exclusion handling, duplicate expressions, confidence threshold, probability calibration, and label coverage.

Use the bundled scripts for these guardrails: `audit_active_learning_batch.py` before training on a new batch, `propagate_duplicate_labels.py` after labeling unique duplicate expressions, and `diagnose_predictions.py` when low-confidence share is high or a run appears stuck.

Low-confidence rows do not need to be eliminated. Treat confidence as a triage signal, not calibrated truth. If many rows remain low-confidence or marked for review, first diagnose repeated expressions, low-information rows, threshold settings, probability calibration, label coverage, and sampling strategy. Do not estimate required rounds by dividing low-confidence row count by review batch size. A run can be usable when the main distribution is stable, audit samples show few clear errors, and remaining low-confidence cases are separately reported or explainable. If low-confidence cases contain many obvious misclassifications or change the distribution materially after audit, continue targeted sampling or schema refinement.

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

Short text is not deleted for being short; separate it into explicit plain-text attitude signals and low-information candidates. Explicit plain-text attitude signals enter the sentiment denominator. Low-information candidates are counted separately, sampled for review, and not forced into neutral by default. Do not put pure acknowledgements, greetings, or emoji-only rows into `中性` by default. Rows made only of emoji or bracketed platform emoji such as `[赞]`, `[强]`, `[捂脸]`, `[玫瑰]` should be removed from the prepared sentiment sample by default and counted separately. Short plain-text attitude signals such as `支持`, `赞成`, `反对`, and `不支持` should stay in the denominator and receive the corresponding attitude label.

Do not strip emoji inside longer text during initial cleaning, because they may help interpret tone. Only rows made solely of emoji or bracketed platform emoji should be removed from the prepared sentiment sample by default and logged separately.

When the task is a new issue, create the taxonomy from evidence:

1. sample across platform/source, time, text length, and likely events;
2. summarize recurring attitudes and noise patterns;
3. use k-means/keywords only to reveal expression clusters;
4. merge clusters into business-meaningful attitude labels;
5. ask the user to confirm the final taxonomy before full-data classification.

## Denominator Gate (Hard Requirement)

For any sentiment, attitude, stance, or positive/neutral/negative output, first create a row-level denominator decision before reporting percentages. This requirement is domain-general: it applies to three-class sentiment, four-class stance, custom issue labels, and large-scale classifier migration.

Every final row-level output must include:

- a field equivalent to `是否纳入情感分母` / `in_denominator`;
- a field equivalent to `排除原因` / `exclusion_reason`;
- enough summary evidence to state the final effective denominator.

Rows that are irrelevant, off-topic, spam, unusable, pure contextless replies, low-information, or emoji-only should be excluded or flagged according to the denominator policy, then reported separately. Do not force them into neutral or any other final report label just because the user requested only a limited output label set.

Run:

```powershell
python scripts/sentiment/validate_denominator_gate.py --input final_predictions.csv --output denominator_gate_report.csv
```

If the gate fails, stop before charts and percentages. Fix the row-level fields, audit exclusions, or disclose the run as incomplete/diagnostic. Do not present sentiment or stance shares as final until the gate passes.

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
- for every sentiment/stance run, include row-level denominator inclusion, exclusion reason, and an effective-denominator summary; if `validate_denominator_gate.py` fails, do not report class percentages as final;
- explain whether repeated comments are counted as volume or deduplicated expressions;
- explain how short attitude texts were handled;
- disclose whether labels are AI-labeled, weak-rule labels, classifier-migrated labels, or reviewed labels;
- disclose whether the label taxonomy was user-provided or built from exploratory samples;
- generate overall label distribution for every sentiment run; generate monthly/event charts only when a usable date/event column exists or the user asks for trend analysis;
- avoid presenting small-sample tests as final accuracy;
- include audit samples when results are subjective;
- run `validate_final_package.py` when packaging final deliverables.
