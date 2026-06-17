# Label Schema Template

Create a task-specific copy of this table before the first AI labeling batch. The rows below are examples; replace them with the task's actual labels.

## Label Roles

| canonical_label | role | aliases | definition | positive_examples | negative_examples | supplementation_strategy |
| --- | --- | --- | --- | --- | --- | --- |
| final_label_a | final_report_label | alias_a1; alias_a2 | A reportable sentiment/stance/topic category. | Clear examples of this category. | Similar examples that should not be this category. | Use anchor phrases, weak rules, clusters, or random samples relevant to this label. |
| final_label_b | final_report_label | alias_b1; alias_b2 | Another reportable category. | Clear examples. | Counterexamples. | Use a different strategy if this label has different signals. |
| exclusion_label | exclusion_or_denominator_label | spam; irrelevant; low-information | Texts to exclude or report separately according to denominator policy. | Unrelated spam, pure prompt, too little content. | Short but clearly relevant text. | Combine text length, topic relevance, spam patterns, and audit samples. |
| review_status_name | review_status_not_training_label | uncertain; needs_review; ambiguous | Use only as a review state unless explicitly defined as a final report bucket. | Context-poor or conflicting cases that need review. | Clear cases with a dominant label. | Use low confidence, low margin, weak-rule/model disagreement, short context, or conflicting cues. |

## Rules

- Use only `canonical_label` values in training files.
- Normalize aliases before classifier training.
- Distinguish final report labels from review statuses before the first batch.
- If an ambiguity/insufficient-context category is a final report bucket, include enough confirmed examples.
- If ambiguity only means "needs review", do not train it as an ordinary label.
- If the task needs fewer categories, merge labels deliberately and document the merge.
- If the task needs different categories, replace this table rather than mixing old and new labels.
