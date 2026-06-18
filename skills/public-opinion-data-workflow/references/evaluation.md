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

## Convergence Checks

Minimum output files are not the same as convergence. For sentiment, stance, or public-opinion classification, treat the result as converged only when:

- the remaining low-confidence and boundary share is understood, sampled, and acceptable for the task;
- a new AI-reviewed audit batch largely agrees with classifier predictions;
- full-data label shares no longer move sharply between rounds;
- random per-class audits show few obvious mistakes;
- key labels no longer repeatedly confuse with each other;
- each final report label has enough AI-reviewed examples, or has been merged/removed with a documented reason.

Low-confidence rows are not a backlog to clear. Do not infer the number of required rounds by dividing low-confidence row count by review batch size. A high low-confidence share is a diagnostic signal: inspect duplicate expressions, low-information rows, threshold settings, probability calibration, label coverage, and sampling strategy. Remaining low-confidence rows may be reported as uncertainty when audits show they do not materially change the main distribution.

The denominator chain, label distribution, and audit samples are required evidence. They prove the process is traceable, but they do not prove convergence until the audit results are reviewed. If the user asks to stop before these checks pass, mark the run as stopped early or diagnostic rather than final.

## Recommended Wording

> Existing labels were used as a reference check rather than as absolute ground truth. The comparison reports agreement rate, confusion patterns, and disagreement samples for review.
