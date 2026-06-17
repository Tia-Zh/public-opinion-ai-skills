# Evaluation And Reference-Label Comparison

Use this reference for validation after predictions are generated.

## If Reference Labels Exist

Run `scripts/compare_labels.py` with the reference label and predicted label columns. Produce:

- `label_comparison_summary.csv`
- `confusion_matrix.csv`
- `disagreement_sample.csv`

Treat the reference label as a check, not absolute truth, unless the user confirms it is human-reviewed ground truth.

## If Reference Labels Do Not Exist

Use audit sampling:

- per-class random samples;
- low-confidence samples;
- top-2-close boundary samples;
- sarcasm-like or mixed-sentiment samples;
- off-topic/noise samples.

After each audit round, update label definitions or classifier calibration before running the next round.

## Report Wording

> Quality was checked through reference-label comparison where available and through targeted audit samples otherwise. Low-confidence, boundary, sarcasm-like, and random examples were reviewed to identify taxonomy or classifier issues.
