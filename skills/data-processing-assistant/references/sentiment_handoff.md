# Sentiment Handoff

Use this reference when a general data-processing task turns into sentiment, stance, or public-opinion classification.

## Route Selection

Use the main `data-processing-assistant` workflow when:

- the dataset is small enough for direct review or full AI labeling;
- the requested labels are simple, such as positive/neutral/negative;
- the user does not need iterative audit, uncertainty sampling, or sarcasm review;
- the output is mainly a cleaned table plus a basic chart.

Use `large-scale-sentiment-analysis` when:

- the dataset has thousands or tens of thousands of Chinese comments;
- full AI labeling is too expensive, slow, or unstable;
- labels include nuanced classes such as risk concern, ridicule, wait-and-see, irrelevant, or uncertain;
- sarcasm, reversal, mixed positive/negative expression, or low-context comments are common;
- the user needs confidence, audit samples, boundary cases, and denominator disclosure.

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

## Return To Main Workflow

After the specialist workflow finishes:

1. Read back the specialist output files.
2. Validate row counts and `row_id` coverage.
3. Merge labels into the final cleaned table if requested.
4. Generate report-ready charts and a short method note.
5. Export the final workbook without overwriting source data.

Use careful wording: say "large-model-assisted sampled labeling plus classifier/rule calibration" unless every row was actually sent to an AI model.
