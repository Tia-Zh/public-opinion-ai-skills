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

## Convergence Checks

Do not treat generated files or a fixed round count as convergence. A run is converged only when the quality evidence is stable enough for the task:

- the remaining low-confidence and boundary share is understood, sampled, and acceptable for the use case;
- a new AI-reviewed audit batch largely agrees with the classifier predictions;
- the full-data label distribution changes only slightly between rounds;
- per-class random audit samples show few obvious errors;
- important categories no longer frequently confuse with each other;
- every final report label has enough AI-reviewed examples, or has been deliberately merged/removed with a documented reason.

Low-confidence rows are not a backlog to clear. Do not infer the number of required rounds by dividing low-confidence row count by review batch size. A high low-confidence share is a diagnostic signal: inspect duplicate expressions, low-information rows, threshold settings, probability calibration, label coverage, and sampling strategy. Remaining low-confidence rows may be reported as uncertainty when audits show they do not materially change the main distribution.

Before training on a new AI-labeled batch, check batch health. If one label exceeds 80% of the batch, pause and audit sampling, duplicate concentration, label definitions, and missing-class coverage. If more than 90% of full-data rows are low-confidence after scoring, do not keep mechanically selecting the next low-confidence batch; diagnose the data and model setup first.

Denominator chains, distribution tables, and exported audit samples are required reporting evidence, but they are not convergence by themselves. User acceptance can stop a run, but if the quality checks above are not met, describe the output as an incomplete or diagnostic run instead of a final converged result.

## Report Wording

> Quality was checked through reference-label comparison where available and through targeted audit samples otherwise. Low-confidence, boundary, sarcasm-like, and random examples were reviewed to identify taxonomy or classifier issues.
