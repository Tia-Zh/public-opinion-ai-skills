# Sentiment Handoff

Use this reference when a general data-processing task turns into sentiment, stance, or public-opinion classification.

## Route Selection

Use the main data-processing workflow when:

- the task is only cleaning, merging, filtering, charting, or exporting;
- the sentiment/stance dataset is small enough for direct full AI labeling or direct review;
- the user only needs a small-sample/basic labeling result and accepts that active-learning evidence is not being produced;
- the output is mainly a cleaned table plus a basic chart.

Use `large-scale-sentiment-analysis` when:

- the dataset has thousands or tens of thousands of Chinese comments;
- full AI labeling is too expensive, slow, or unstable;
- the task is large-scale sentiment/stance classification, even if the requested output labels are only positive/neutral/negative;
- labels include nuanced, rare, easily confused, or business-critical classes such as risk concern, ridicule, wait-and-see, irrelevant, or uncertain;
- sarcasm, reversal, mixed positive/negative expression, or low-context comments are common;
- the user needs confidence, audit samples, boundary cases, and denominator disclosure.

Do not use label simplicity as a reason to skip active learning on a large dataset. A 100,000-row positive/neutral/negative task still needs sampled AI labeling, classifier migration, review batches, and quality gates unless the user explicitly accepts a non-final smoke test.

## Handoff Packet

Before switching, collect or infer:

- input file path;
- text column name;
- source/platform column if available;
- date/time column if available;
- ID, URL, user, or link column to hash if available;
- proposed labels and exclusion labels;
- output folder;
- whether the user wants a seed sample only, one active-learning round, or a full workflow.

## Expected Specialist Outputs

The specialist workflow should produce:

- `prepared_texts.csv`;
- `data_summary.csv`;
- `llm_label_sample.csv` or `llm_batches.csv`;
- `merged_labels.csv`;
- `label_quality_summary.csv`;
- audit samples for low-confidence, uncertain, sarcasm-like, and random rows when available;
- charts and denominator tables.

## Convergence Requirement

The specialist output is not complete just because it produced a distribution table. Before returning a result as final, check whether:

- low-confidence and boundary rows have fallen to an acceptable level;
- a fresh AI-reviewed audit batch mostly agrees with the classifier;
- label distribution is stable across rounds;
- random samples show few obvious errors;
- important labels are no longer frequently confused;
- every final report label has enough AI-reviewed examples, or the label schema was adjusted with a documented reason.

If these checks are not met, return the current files as an interim or diagnostic result and state which review step is still needed. User confirmation may end the task, but it does not convert an unstable result into a converged one.

## Return To Main Workflow

After the specialist workflow finishes:

1. Read back the specialist output files.
2. Validate row counts and `row_id` coverage.
3. Merge labels into the final cleaned table if requested.
4. Generate report-ready charts and a short method note.
5. Export the final workbook without overwriting source data.

Use careful wording: say "large-model-assisted sampled labeling plus classifier/rule calibration" unless every row was actually sent to an AI model.
