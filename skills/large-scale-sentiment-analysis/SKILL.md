---
name: "large-scale-sentiment-analysis"
description: "当需要处理大规模中文文本、评论、舆情、情感或立场分类，且全量人工或全量 AI 逐条标注成本过高、耗时过长或需要复核时使用。提供可复用的主动学习流程：清洗脱敏，分层抽样，让 AI 标注高价值样本，训练或校准自动分类器，抽取低置信度、边界、反讽和随机样本继续复核，合并标签，审计质量，并生成可汇报的统计表和图表。"
---

# Large-Scale Sentiment Analysis

Use this skill for large comment, review, survey, post, or public-opinion datasets where labels require semantic judgment but full LLM labeling is too expensive or unstable.

This skill can be called directly, or as the specialist workflow from `data-processing-assistant` when general data processing reaches high-volume or nuanced Chinese sentiment/stance classification.

Core method:

1. Clean and de-identify text, while preserving both raw volume and optional deduplicated views.
2. If labels are missing, explore samples and expression clusters to draft a task-specific sentiment/stance taxonomy.
3. Define a small, stable label taxonomy with edge cases.
4. Ask an LLM to label a stratified seed sample.
5. Train, calibrate, or rule-calibrate an automatic classifier.
6. Run the classifier on all data only after at least one AI-labeled seed batch exists.
7. Select uncertain/boundary/sarcasm-like samples for another LLM labeling round.
8. Repeat active-learning rounds until the quality checks converge. If the available AI cannot label the requested sample carefully, reduce batch size, split batches, or use an external LLM/API; do not replace AI semantic labeling with rules.
9. Run final full-data classification only after convergence criteria are met or clearly disclose why the run stopped early.
10. Audit low-confidence, uncertain, and random class samples.
11. Generate report-ready tables and charts.

Recommended wording:

> This analysis uses a large-model-assisted, auditable classification workflow. A large model labels stratified and uncertainty-selected samples to establish category boundaries. A calibrated automatic classifier then applies the learned coding rules to the full dataset. Low-confidence, uncertain, sarcasm-like, and random samples are reviewed to improve reliability.

Avoid saying "the LLM manually labeled every row" unless every row was actually sent to an LLM.

## Label Taxonomy

For every task, define:

- task-specific label roles, not just label names;
- user-requested output labels that will appear in the final report distribution, such as `正面/中性/负面`;
- internal processing labels that may be necessary for relevance, denominator, exclusion, or quality control even when the user did not name them;
- exclusion labels such as irrelevant, spam, or low-information when they are part of the denominator policy;
- review statuses such as needs-review, ambiguous, conflict, or model-uncertain when they should trigger review rather than become ordinary classifier labels;
- canonical label names and allowed aliases;
- concise criteria, examples, and counterexamples for each final or exclusion label.

Do not begin with keyword matching. Begin with label definitions and edge cases.

Before the first LLM batch, create or update a `label_schema.md` or equivalent table in the output directory. Use one language for canonical labels throughout the run. If a later LLM batch returns aliases or another language, normalize labels before training the classifier.

At schema time, decide which labels are report labels and which are review statuses. Do not hard-code a label named `uncertain`; different tasks may use names such as `ambiguous`, `needs_review`, `mixed`, `insufficient_context`, `irrelevant`, or local Chinese equivalents. If a category is a final report bucket, include enough confirmed examples and define it in the schema. If it only means "the model is unsure and this row needs review", keep it as a review status derived from confidence, margin, disagreement, short/context-poor text, or audit results, not as an ordinary classifier label.

Treat the user's requested labels as the output schema, not necessarily the full internal analysis schema. If the user says "classify as positive/neutral/negative" or gives four report categories, still add internal categories or flags when needed:

- `相关性`: relevant vs irrelevant/off-topic;
- `有效性`: meaningful vs low-information/spam;
- `复核状态`: needs-review/model-uncertain/conflict;
- optional exclusion labels that are reported separately and excluded from the final output denominator.

Do not force irrelevant, off-topic, spam, pure contextless replies, or insufficient-context rows into `中性` just because the user only requested `正面/中性/负面`. `中性` means relevant but with no clear positive or negative attitude. Exclusion rows should be counted and disclosed separately, then removed from the denominator used for the requested output labels unless the user explicitly wants them included.

Treat pure acknowledgements, greetings, and emoji-only rows as denominator/exclusion candidates, not as ordinary `中性`. A row that contains only one or more emoji, or only bracketed platform emoji such as `[赞]`, `[强]`, `[捂脸]`, `[玫瑰]`, should not be treated as a complete attitude by itself. Remove emoji-only rows from the prepared sentiment sample by default, write them to a removed/audit file, and report the count. Short plain-text rows with explicit attitude words, such as `支持`, `赞成`, `反对`, or `不支持`, should be kept and labeled by attitude.

Do not use vague words such as "maybe", "possibly", or "not sure" alone to find ambiguity/review samples; long texts can contain those words while still having a clear stance. Prefer task-specific strategies such as very short context-poor texts, conflicting cues, missing context, weak-rule/model disagreement, or label-specific anchors.

If the user does not provide labels, do not default blindly to positive/neutral/negative. First inspect stratified samples and, if useful, rough clusters from a topic-discovery script. Treat clusters as evidence about common expressions, not as final sentiment labels. Draft labels that match the business question, such as `employment anxiety`, `technical optimism`, `policy demand`, `sarcasm`, `irrelevant/low-information`, or a simpler three-class taxonomy when that is enough.

Do not start interpreting full classifier results until every target report label has enough AI-labeled examples to be learnable. As a practical default, aim for at least 20-30 AI-labeled examples per final label, and more for subtle or rare labels such as criticism, neutral analysis, or sarcasm. If a label has fewer examples, run targeted sampling for that label before treating a zero or near-zero prediction share as meaningful. Apply this rule to ambiguity/insufficient-context categories only when they are intentionally used as final report labels, not when they are only review flags.

Use targeted supplementation when any plausible label is missing or underrepresented. Targeted supplementation means: use weak rules, anchor phrases, keyword candidates, or cluster examples to find likely examples of an underrepresented label; send those candidates to the LLM or a human reviewer; then add only the confirmed labels to the training pool. Do not add weak-rule labels directly as truth.

Design targeted supplementation per label. Different labels need different candidate strategies: criticism may use words such as "excuse", "hype", "cover for layoffs", or "actually"; neutral analysis may use balanced framing and report-like language; ambiguity/insufficient-context buckets may use short context-poor texts, conflicting cues, or missing context rather than generic uncertainty words.

## Workflow

When invoked by `data-processing-assistant`, expect the main skill to provide the input file path, text column, optional source/date/hash columns, proposed labels, and output folder. Return cleaned data, label quality checks, audit samples, charts, and denominator notes so the main skill can package the final workbook/report.

### 1. Prepare Data

Use `scripts/prepare_text_data.py` to normalize text, hash sensitive source fields, mark short/duplicated rows, and assign stable `row_id`.

Do not remove comments only because they are short. Short text is not deleted for being short; it must be separated into explicit plain-text attitude signals and low-information candidates. Explicit plain-text attitude signals enter the sentiment denominator. Low-information candidates are counted separately, sampled for review, and not forced into neutral by default. In public-opinion data, short texts such as `支持`, `赞成`, `点赞`, `反对`, or short complaint phrases can be real attitude signals. The default preparation script does not filter by length, but it does remove emoji-only rows from `prepared_texts.csv` and logs them separately. If a task uses `--min-info-len`, keep rows with short plain-text attitude signals and record how many short rows were removed or retained.

The preparation script marks contextless acknowledgement candidates with `low_information_candidate` and removes emoji-only rows by default into `removed_emoji_only_rows.csv`. Use the removed file for count disclosure or optional audit, not as part of the effective sentiment denominator.

Do not strip emoji inside longer text during initial cleaning, because they may help interpret tone. Only rows made solely of emoji or bracketed platform emoji should be removed from the prepared sentiment sample by default.

Do not collapse repeated comments silently. Repetition may be spam, but it may also be real public-opinion volume: ten people saying `赞成` should not automatically become one person. Keep all rows by default and add `text_hash` and `duplicate_count`. If an expression-level deduplicated analysis is needed, use a dedupe mode deliberately and report both:

- volume denominator: repeated comments counted as repeated voices;
- unique-expression denominator: repeated identical text counted once or weighted by `duplicate_count`.

For sentiment/stance reporting, prefer the volume denominator unless the user explicitly asks for deduplicated expression analysis or spam removal.

Input can be CSV/XLSX. Required text column must be specified. Optional columns:

- platform/source
- timestamp/date
- link/url/id to hash
- event/window grouping

Output:

- `prepared_texts.csv`
- `data_summary.csv`

### 2. Create LLM Batches

Use `scripts/make_llm_batches.py` to create stratified or full batches. Prefer hybrid stratified seed batches first: cover important strata, then fill the remaining sample randomly so the seed still roughly reflects the full dataset.

- platform/source when available;
- text length bucket, especially very short and long comments;
- month/date or event window only when the task is time-sensitive and the column is reliable;
- random sample.

If platform/source volumes are highly imbalanced, do not rely on pure overall random sampling because small platforms may disappear from the seed. Also do not use pure equal-platform sampling as the only basis because tiny platforms may be overrepresented. Use a hybrid approach: minimum coverage for each meaningful platform/source, caps for tiny strata, and random/proportional fill for the remaining sample. Final result shares must still use the chosen denominator, usually the volume denominator.

For subjective large-scale sentiment/stance tasks, do not start with a tiny seed unless the user explicitly asks for a smoke test. Practical defaults:

- under 10,000 rows: 100-200 AI-reviewed seed examples;
- 10,000-100,000 rows: 200-400 AI-reviewed seed examples;
- above 100,000 rows or many platforms/topics: 300-500 AI-reviewed seed examples.

Do not ask the current AI agent to label more than 500 seed examples in one pass. Split seed labeling into batches of 50-100 rows. These are starting points, not stopping rules: label coverage per final output label and audit quality decide whether more targeted samples are needed. Prefer adding smaller, targeted review batches in later rounds over forcing a huge first seed batch.

For active learning rounds, batch only uncertain/boundary cases.

### 3. AI Semantic Labeling

Use the current AI agent's natural-language understanding, or an available LLM/API if the environment provides one, to label the batch according to the schema. The AI must read each sampled text, understand the full meaning, tone, negation, sarcasm, context, and dominant attitude, then choose the best label from the schema. Do not write a keyword-rule script and treat its output as AI labeling.

Do not create a Python script, CSV, or hard-coded dictionary that contains guessed labels and call it AI semantic labeling. Scripts may help split batches, preserve `row_id`, format prompts, validate label files, merge AI outputs, or train classifiers, but the label decision itself must come from AI reading the sampled text in natural language or from an external LLM/API response. If labels are typed by a human, disclose them as manual labels. If labels are generated by rules, disclose them as rule candidates or diagnostic baselines and do not add them to the training set until AI-reviewed or human-confirmed.

Use the prompt template in `references/llm_labeling_prompt.md` when you need a separate prompt or external model call. The labeling task must include:

- label taxonomy;
- output schema;
- input batch file;
- instruction to preserve `row_id`;
- instruction to return CSV/JSON only.

Required output columns:

```text
row_id,label,confidence,reason,is_sarcasm
```

### 4. Merge And Validate Labels

Use `scripts/merge_labels.py` to validate:

- missing row_id;
- duplicate row_id;
- invalid labels;
- confidence parse errors;
- output coverage.

Never proceed to charts before row_id coverage is checked.

Before training, validate that the AI-reviewed sample covers every final report label. Use `scripts/validate_label_coverage.py` after merging labels. As a practical default, require at least 20-30 AI-reviewed examples per final label before treating the classifier result as meaningful; use more examples for subtle or easily confused labels such as neutral, criticism, sarcasm, or policy demands.

Example:

```powershell
python scripts/validate_label_coverage.py --labels merged_labels.csv --label-col label --target-labels "正面,中性,负面" --min-per-label 30 --output label_coverage.csv
```

If coverage fails, do not train as if the sample is ready. Run targeted supplementation for missing or underrepresented labels, label those candidates with AI semantic labeling, merge confirmed labels, and rerun coverage validation.

### 5. Classifier Or Rule Calibration

Train or calibrate a classifier from AI-labeled samples and use probabilities as uncertainty. Do not replace this step with pure keyword classification. If the classifier cannot run, stop and report the blocker or ask to install dependencies; do not produce a final sentiment result from keyword rules.

Before training on large datasets, run:

```powershell
python scripts/check_dependencies.py
```

If recommended packages are missing, ask the user whether to install them. Do not install dependencies silently. If the user agrees, run:

```powershell
python scripts/install_optional_dependencies.py
```

Use `scripts/train_text_classifier.py` directly. It supports:

- `--backend auto` (default): use `scikit-learn` logistic regression when available; otherwise fall back to fast character n-gram Naive Bayes.
- `--backend sklearn`: require `scikit-learn`; fail if unavailable.
- `--backend fast-nb`: use the dependency-light fallback.

`scikit-learn` is the Python package name; it is imported as `sklearn`. It is the preferred local classifier backend because it vectorizes text features and runs much faster than pure Python loops on large files. If the environment allows installing dependencies, prefer:

```powershell
python -m pip install scikit-learn
```

If installation is not allowed, the Python version is unsupported, or the sklearn backend is too slow in the current environment, use `--backend fast-nb` and disclose it in the quality note. For large files, keep `--progress-every 10000` enabled so the user can see that scoring is still running. If `fast-nb` is still slow, lower `--max-chars` to 200-400 and record that choice in the quality note.

For each round:

1. Validate AI-reviewed label coverage.
2. Train/calibrate classifier on current labeled sample only after coverage is acceptable.
3. Score unlabeled/full data.
4. Select uncertain rows:
   - low maximum probability;
   - close top-2 class probabilities;
   - sarcasm marker;
   - category-specific risk words;
   - weak-rule candidates for underrepresented labels;
   - examples where weak-rule label and model prediction disagree;
   - rows whose predicted label changed between rounds, especially neutral-to-positive or neutral-to-negative drift;
   - short but attitude-bearing rows;
   - question/反问-like rows, such as `?`, `？`, `吗`, `难道`, `不好吗`, or `哪里不好`;
   - random audit sample.
5. Send selected rows to LLM.
6. Merge labels, rerun coverage validation, and repeat.

When selecting samples for review, prefer unique text expressions first so AI effort is not spent repeatedly labeling identical comments. Keep `duplicate_count` or equivalent volume fields so repeated comments still contribute to final volume shares. Review duplicate-heavy expressions separately only when repetition itself may be spam, coordinated behavior, or an important signal.

Do not use self-training as the default active-learning mechanism. Classifier predictions are not truth labels. Add rows to the training set only after AI semantic labeling or human review confirms them. If pseudo-labeling is used only for an internal experiment, apply all of these guardrails and do not treat it as a deliverable result:

- mark pseudo-labels separately from AI-reviewed labels;
- cap how many pseudo-labels each class can add per round;
- keep class additions reasonably balanced, especially for neutral or weak-attitude classes;
- never let one class expand only because its classifier confidence is high;
- run an audit batch before the next round and remove pseudo-labels that fail review;
- stop and review if the class distribution shifts sharply between rounds.

For three-class positive/neutral/negative tasks, treat neutral as a real target class, not a leftover bucket. Neutral samples often have lower confidence because they lack strong sentiment words; this makes them vulnerable to being squeezed into positive or negative during self-training. Include neutral examples in seed samples, targeted supplementation, uncertain batches, and fixed audit sets.

Avoid class starvation. If a target label is absent or nearly absent in the AI-labeled sample, uncertainty sampling alone will not recover it because the classifier has not learned that class. Use weak rules, anchor phrases, keyword candidates, or clustering to find possible examples for that label, then ask the LLM to judge them. Treat weak rules as candidate generators, not final labels.

For targeted supplementation, use `scripts/make_targeted_samples.py` when a weak label column or keyword map is available. Example:

```powershell
python scripts/make_targeted_samples.py --input prepared_texts.csv --output-dir targeted_round --text-col clean_text --target-labels "质疑批评,理性中立" --keywords targeted_keywords.csv --per-label 100
```

The keyword CSV may include optional `min_chars` and `max_chars` columns for label-specific strategies, such as short context-poor candidates. The output `targeted_label_candidates.csv` is a review batch, not final labels. Label it with the AI semantic labeling schema, merge confirmed labels, then retrain.

Do not stop because a fixed number of rounds has been reached. Also do not treat low-confidence rows as a backlog that must be exhausted one by one. Active learning is not "clear every uncertain row"; it is "use high-value uncertain rows to test and improve the label boundaries." Stop only when the quality evidence is stable enough for the use case:

- the remaining low-confidence/boundary share is understood, sampled, and acceptable for the task;
- a new AI review batch largely agrees with the classifier's predictions;
- the full-data label distribution changes only slightly between rounds;
- random audit samples show few obvious errors;
- key categories such as employment anxiety, risk concern, sarcasm, and neutral information no longer frequently confuse with each other;
- every target label has enough labeled examples or has been deliberately merged/removed with a documented reason;
- the user explicitly asks to stop and accepts that the run is incomplete.

If stopping after only one round, do not call the result final. Label it as an incomplete test run and report the missing review steps.

Treat model confidence as a triage signal, not as calibrated truth. Raw Naive Bayes or logistic-regression probabilities may be overconfident, underconfident, or poorly calibrated for short Chinese comments, emoji-heavy rows, repeated text, and low-information replies. Do not infer that a run needs hundreds of rounds by dividing the number of low-confidence rows by the review batch size. If low-confidence share is high, first diagnose duplicate expressions, low-information rows, threshold settings, probability calibration, label coverage, and sampling strategy. Prefer `top2_margin`, disagreement samples, fixed audit sets, and random audits for quality judgment.

If a predicted distribution drops plausible labels to zero, do not accept it silently. Check labeled-sample coverage first. A zero or near-zero category often means the active-learning sample missed that class, not that the class is absent in the data.

If an exclusion or low-information bucket becomes unusually large, especially with low confidence, do not accept it silently. Audit that bucket before reporting. A high low-information share may mean the classifier is dumping hard-to-classify but relevant texts into the exclusion bucket. Sample low-confidence exclusion predictions and relevant-looking exclusion predictions, correct labels, and retrain if many are actually relevant.

After each AI-labeled sample batch, inspect the label distribution before training. If a three-class batch becomes extremely imbalanced, such as almost all negative or almost no neutral, do not proceed as if it were high-quality training data. First audit whether the imbalance comes from true sampling, rule-based pseudo-labeling, unclear label definitions, missing neutral examples, or systematic misunderstanding. The correct response is targeted supplementation and review, not immediate training.

If a negative or positive class becomes unusually large, audit before reporting. In Chinese public comments, questions, rhetorical questions, policy demands, and off-topic demands are often misread as negative because they contain words such as `不`, `取消`, `降`, `不好`, or question marks. Sample and review:

- question/反问 rows predicted as negative;
- off-topic or adjacent-policy rows predicted as negative;
- rows that changed from neutral to negative or neutral to positive between rounds;
- short positive/negative rows that may have been filtered or under-sampled;
- high-duplicate short rows whose volume materially changes the final share.

Do not continue iterative training when a transition matrix shows one class absorbing many rows from another class without review. Build a small fixed audit set at the beginning and score it after every round. If stable audit rows drift in one direction, pause, review changed cases, add confirmed corrections, and retrain.

Low-confidence rows are allowed to remain. Do not force them into high-confidence positive/neutral/negative conclusions just to make the chart look complete. If many rows remain low-confidence or marked `needs_review`, sample and explain them: are they repeated expressions, low-information replies, off-topic rows, true boundary cases, or an overly strict threshold? When the main label distribution is stable, random audits show few clear errors, and low-confidence cases are either separately reported or concentrated in explainable buckets, the run may be usable with an uncertainty note. When low-confidence cases contain many obvious misclassifications or materially change the distribution after audit, continue schema refinement, targeted sampling, or review. Low-confidence share alone is not a valid stopping or failure criterion.

### 5a. Output Discipline

During active-learning iterations, keep outputs lean:

- Always save CSV artifacts for traceability: prepared data, AI labels, scored predictions, uncertain batch, and metrics.
- Do not write a full-row Excel workbook after every intermediate round.
- Write one summary Excel at the end of the current run with metrics, distributions, AI-labeled samples, low-confidence samples, random audit samples, and a small preview.
- For datasets above 50,000 rows, keep full predictions as CSV unless the user explicitly asks for full Excel.
- Do not present a one-round result as the main deliverable if a second-round review is still pending. First show the next review batch and quality status.

### 5c. Windows And File Handling Guardrails

On Windows or mixed Git Bash/PowerShell environments:

- Prefer saved `.py` scripts or bundled scripts over shell heredoc snippets such as `python <<EOF`, because some terminals lose stdout/stderr.
- Use absolute paths from `Path(...).expanduser().resolve()`; avoid passing `~` directly to Windows Python.
- Do not copy skill scripts to data folders unless path execution truly fails. Fix the path first.
- After CSV round-trips, explicitly normalize important grouping columns such as year/date/source to string before filtering or grouping.
- For full predictions above 50,000 rows, write CSV. Put only summaries and samples in Excel.

### 5b. Optional Reference-Label Evaluation

If the dataset already has a historical or manual label column, use `scripts/compare_labels.py` after generating predictions. Treat the reference column as a test aid, not automatic truth. Report agreement rate, confusion matrix, and disagreement samples. Skip this step when no reference label exists.

### 6. Audit

Always generate:

- label distribution;
- confidence distribution;
- duplicate/volume notes, including whether the reported distribution is volume-weighted or deduplicated;
- short-text attitude sample and handling note;
- per-class random audit sample;
- low-confidence sample;
- uncertain sample;
- sarcasm-like sample;
- question/反问-like sample when negative or positive shares are high;
- label transition matrix between rounds when iterative classification is used;
- month/event distribution only when a usable date/event column exists or the user asks for trend analysis.

For reports, disclose the denominator:

- full cleaned sample;
- meaningful/effective sample;
- four-class internal share;
- excluded/uncertain share.

### 7. Charts

Prefer clear denominators:

- 100% stacked bars for final classes;
- overall label distribution for every run;
- monthly/event trend charts only when the source data has a usable date/event column or the user asks for trend analysis;
- separate line/bar for risk voices if small classes are visually suppressed;
- avoid mixing volume and sentiment in one chart unless the scale and meaning are obvious.

If showing risk voices separately, note:

> Risk voices = selected negative/risk categories. The lower panel uses an independent y-axis to show small-category movement and does not change the true class shares above.

## Scripts

Bundled scripts are starting points. Patch column names and label lists for the concrete dataset.

- `scripts/prepare_text_data.py`: clean, hash, mark duplicates, create `row_id`.
- `scripts/make_llm_batches.py`: create hybrid stratified AI-labeling batch files and a prompt.
- `scripts/merge_labels.py`: merge labels and validate row_id coverage.
- `scripts/validate_label_coverage.py`: check whether each final label has enough AI-reviewed examples before training.
- `scripts/train_text_classifier.py`: train a lightweight classifier from AI-reviewed labels and score confidence/margins.
- `scripts/select_uncertain.py`: select low-confidence and boundary samples, deduplicating review text expressions by default while preserving volume fields.
- `scripts/make_targeted_samples.py`: create targeted review batches for underrepresented labels using weak labels or keyword candidates.
- `scripts/build_summary_charts.py`: create summary tables and monthly charts.
- `scripts/compare_labels.py`: compare predictions with an existing reference label column when available.

## Method Notes

Read `references/method_note.md` when writing the methodology section.

Read `references/llm_labeling_prompt.md` when preparing model prompts.

Read `references/evaluation.md` when comparing against existing labels or writing validation notes.

Read `references/privacy.md` when deciding what to hash, mask, or exclude before AI labeling.

Use `references/label_schema_template.md` when setting up canonical labels and aliases for a new task.
