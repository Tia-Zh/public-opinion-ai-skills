# Evaluation And Reference-Label Comparison

Use this reference when the user wants to validate labels, compare against a historical label column, or prepare a quality summary.

## Two Validation Modes

Use reference-label comparison only when the dataset already contains a historical, manual, or trusted label column. Otherwise use audit sampling.

Reference-label comparison answers:

- how often the new output agrees with the existing label column;
- which labels are most often confused;
- which disagreement samples need review.

Audit sampling answers:

- whether random examples from each predicted class look reasonable;
- whether low-confidence, boundary, sarcasm-like, or mixed-sentiment rows need a new labeling round;
- whether the label taxonomy itself needs adjustment.

## Do Not Overclaim

A historical label column is a reference, not automatic ground truth. If labels were produced by a previous classifier or weak rules, say so. Report agreement as a validation signal, not final accuracy.

## Minimum Evaluation Outputs

When reference labels exist, generate:

- `label_comparison_summary.csv`
- `confusion_matrix.csv`
- `disagreement_sample.csv`

When reference labels do not exist, generate:

- per-class random audit sample;
- low-confidence sample;
- boundary/top-2-close sample;
- sarcasm-like or mixed-sentiment sample when relevant;
- short quality notes with known limitations.

## Recommended Wording

> Existing labels were used as a reference check rather than as absolute ground truth. The comparison reports agreement rate, confusion patterns, and disagreement samples for review.
