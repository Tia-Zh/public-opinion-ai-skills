---
name: "large-scale-sentiment-analysis"
description: "当需要处理大规模中文文本、评论、舆情、情感或立场分类，且全量人工或全量 AI 逐条标注成本过高、耗时过长或需要复核时使用。提供可复用的主动学习流程：清洗脱敏，分层抽样，让 AI 标注高价值样本，训练或校准自动分类器，抽取低置信度、边界、反讽和随机样本继续复核，合并标签，审计质量，并生成可汇报的统计表和图表。"
---

# Large-Scale Sentiment Analysis

Use this skill for large comment, review, survey, post, or public-opinion datasets where labels require semantic judgment but full LLM labeling is too expensive or unstable.

This skill can be called directly, or as the specialist workflow from `data-processing-assistant` when general data processing reaches high-volume or nuanced Chinese sentiment/stance classification.

Core method:

1. Clean, de-identify, and deduplicate text.
2. If labels are missing, explore samples and expression clusters to draft a task-specific sentiment/stance taxonomy.
3. Define a small, stable label taxonomy with edge cases.
4. Ask an LLM to label a stratified seed sample.
5. Train, calibrate, or rule-calibrate an automatic classifier.
6. Run the classifier on all data only after at least one AI-labeled seed batch exists.
7. Select uncertain/boundary/sarcasm-like samples for another LLM labeling round.
8. Repeat active-learning rounds until the quality checks converge or the user accepts a quick baseline.
9. Run final full-data classification only after convergence criteria are met or clearly disclose why the run stopped early.
10. Audit low-confidence, uncertain, and random class samples.
11. Generate report-ready tables and charts.

Recommended wording:

> This analysis uses a large-model-assisted, auditable classification workflow. A large model labels stratified and uncertainty-selected samples to establish category boundaries. A calibrated automatic classifier then applies the learned coding rules to the full dataset. Low-confidence, uncertain, sarcasm-like, and random samples are reviewed to improve reliability.

Avoid saying "the LLM manually labeled every row" unless every row was actually sent to an LLM.

## Label Taxonomy

For every task, define:

- final labels;
- canonical label names and allowed aliases;
- exclusion labels such as `irrelevant/low-information`;
- `uncertain` for ambiguous or context-poor cases;
- concise criteria for each label;
- examples and counterexamples.

Do not begin with keyword matching. Begin with label definitions and edge cases.

Before the first LLM batch, create or update a `label_schema.md` or equivalent table in the output directory. Use one language for canonical labels throughout the run. If a later LLM batch returns aliases or another language, normalize labels before training the classifier.

If the user does not provide labels, do not default blindly to positive/neutral/negative. First inspect stratified samples and, if useful, rough clusters from a topic-discovery script. Treat clusters as evidence about common expressions, not as final sentiment labels. Draft labels that match the business question, such as `employment anxiety`, `technical optimism`, `policy demand`, `sarcasm`, `irrelevant/low-information`, or a simpler three-class taxonomy when that is enough.

Do not start interpreting full classifier results until every target label has enough AI-labeled examples to be learnable. As a practical default, aim for at least 20-30 AI-labeled examples per label, and more for subtle or rare labels such as `critical/questioning`, `neutral/analytical`, or `sarcasm`. If a label has fewer examples, run targeted sampling for that label before treating a zero or near-zero prediction share as meaningful.

## Workflow

When invoked by `data-processing-assistant`, expect the main skill to provide the input file path, text column, optional source/date/hash columns, proposed labels, and output folder. Return cleaned data, label quality checks, audit samples, charts, and denominator notes so the main skill can package the final workbook/report.

### 1. Prepare Data

Use `scripts/prepare_text_data.py` to normalize text, hash sensitive source fields, remove obvious low-information rows, deduplicate, and assign stable `row_id`.

Input can be CSV/XLSX. Required text column must be specified. Optional columns:

- platform/source
- timestamp/date
- link/url/id to hash
- event/window grouping

Output:

- `prepared_texts.csv`
- `data_summary.csv`

### 2. Create LLM Batches

Use `scripts/make_llm_batches.py` to create stratified or full batches. Prefer stratified seed batches first:

- platform/source;
- month/date;
- event window;
- text length bucket;
- random sample.

For active learning rounds, batch only uncertain/boundary cases.

### 3. LLM Labeling

Give the LLM:

- label taxonomy;
- output schema;
- input batch file;
- instruction to preserve `row_id`;
- instruction to return CSV/JSON only.

Use the prompt template in `references/llm_labeling_prompt.md`.

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

### 5. Classifier Or Rule Calibration

Train or calibrate a classifier from LLM-labeled samples and use probabilities as uncertainty. Do not replace this step with pure keyword classification unless the classifier cannot run and the output is clearly marked as a weak baseline.

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

1. Train/calibrate classifier on current labeled sample.
2. Score unlabeled/full data.
3. Select uncertain rows:
   - low maximum probability;
   - close top-2 class probabilities;
   - sarcasm marker;
   - category-specific risk words;
   - weak-rule candidates for underrepresented labels;
   - examples where weak-rule label and model prediction disagree;
   - random audit sample.
4. Send selected rows to LLM.
5. Merge labels and repeat.

Avoid class starvation. If a target label is absent or nearly absent in the AI-labeled sample, uncertainty sampling alone will not recover it because the classifier has not learned that class. Use weak rules, anchor phrases, keyword candidates, or clustering to find possible examples for that label, then ask the LLM to judge them. Treat weak rules as candidate generators, not final labels.

Do not stop because a fixed number of rounds has been reached. Stop only when one of these is true:

- the remaining low-confidence/boundary share is small enough for the task;
- a new AI review batch largely agrees with the classifier's predictions;
- the full-data label distribution changes only slightly between rounds;
- random audit samples show few obvious errors;
- key categories such as employment anxiety, risk concern, sarcasm, and neutral information no longer frequently confuse with each other;
- every target label has enough labeled examples or has been deliberately merged/removed with a documented reason;
- the user explicitly asks for a quick baseline.

If stopping after only one round, do not call the result final. Label it as an initial baseline.

Treat raw Naive Bayes probabilities with caution. If `fast-nb` produces very high confidence values, do not interpret them as calibrated accuracy. Prefer `top2_margin`, disagreement samples, and random audits for uncertainty selection.

If a predicted distribution drops plausible labels to zero, do not accept it silently. Check labeled-sample coverage first. A zero or near-zero category often means the active-learning sample missed that class, not that the class is absent in the data.

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
- per-class random audit sample;
- low-confidence sample;
- uncertain sample;
- sarcasm-like sample;
- month/event distribution.

For reports, disclose the denominator:

- full cleaned sample;
- meaningful/effective sample;
- four-class internal share;
- excluded/uncertain share.

### 7. Charts

Prefer clear denominators:

- 100% stacked bars for final classes;
- separate line/bar for risk voices if small classes are visually suppressed;
- avoid mixing volume and sentiment in one chart unless the scale and meaning are obvious.

If showing risk voices separately, note:

> Risk voices = selected negative/risk categories. The lower panel uses an independent y-axis to show small-category movement and does not change the true class shares above.

## Scripts

Bundled scripts are starting points. Patch column names and label lists for the concrete dataset.

- `scripts/prepare_text_data.py`: clean, hash, dedupe, create `row_id`.
- `scripts/make_llm_batches.py`: create LLM-ready batch files and a prompt.
- `scripts/merge_labels.py`: merge labels and validate row_id coverage.
- `scripts/train_text_classifier.py`: train a dependency-light baseline classifier and score confidence/margins.
- `scripts/select_uncertain.py`: select low-confidence and boundary samples.
- `scripts/build_summary_charts.py`: create summary tables and monthly charts.
- `scripts/compare_labels.py`: compare predictions with an existing reference label column when available.

## Method Notes

Read `references/method_note.md` when writing the methodology section.

Read `references/llm_labeling_prompt.md` when preparing model prompts.

Read `references/evaluation.md` when comparing against existing labels or writing validation notes.

Read `references/privacy.md` when deciding what to hash, mask, or exclude before AI labeling.

Use `references/label_schema_template.md` when setting up canonical labels and aliases for a new task.
