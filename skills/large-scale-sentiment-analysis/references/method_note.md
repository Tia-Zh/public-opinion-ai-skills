# Method Note Template

Use this when writing a report methodology section.

## Recommended Method Wording

This study used a large-model-assisted, auditable classification workflow. First, raw comments were cleaned and de-identified while preserving the volume denominator; duplicate texts were marked with hash/count fields and, when needed, analyzed separately as a deduplicated expression view. A stable label taxonomy was then defined. A large model labeled hybrid stratified and uncertainty-selected samples to establish category boundaries. Based on those labeled samples, an automatic classifier was calibrated and applied to the full cleaned dataset. Low-confidence, boundary, sarcasm-like, and randomly sampled cases were reviewed. Label definitions, targeted samples, and classifier calibration were iterated until the quality signals were stable enough for the task.

## Chinese Report Wording

本研究采用“大模型辅助标注 + 自动分类迁移 + 疑难样本复核”的混合方法。首先对原始评论样本进行清洗与脱敏，同时保留声量口径；对重复文本增加哈希和重复次数标记，必要时另行生成去重表达口径。随后构建稳定的标签体系，并按平台、文本长度及必要的时间/事件维度抽取混合分层样本，由大模型进行语义标注，用于建立分类口径和边界案例。之后将标注口径迁移至自动分类器，对全量样本进行一致性分类。最后对低置信度、边界样本、疑似反讽样本及各类别随机样本进行复核，并根据复核结果继续修正标签体系或分类器，直到低置信度比例、复核一致性、类别分布和关键混淆情况达到稳定。

## Convergence Disclosure

When reporting a final result, state that convergence was judged from multiple quality signals:

- low-confidence and boundary share;
- agreement between AI-reviewed audit samples and classifier predictions;
- stability of label distribution across rounds;
- random audit error patterns;
- confusion among important categories;
- coverage of AI-reviewed examples for every final report label.

If the workflow stops before these checks pass, describe the output as an interim test or diagnostic run, not a final converged result.

## Chinese Convergence Wording

最终结果不是以固定轮数为准，而是以质量信号是否稳定为准：低置信度和边界样本比例是否下降到可接受范围，新一轮大模型复核结果是否与分类器预测基本一致，各类别占比是否不再大幅波动，随机抽查中明显错判是否减少，以及关键类别之间是否不再频繁混淆。若上述条件尚未满足，应将当前结果说明为阶段性测试结果，而不是最终收敛结果。

## What To Avoid

Do not claim:

- "The LLM labeled every row" unless every row was actually sent to an LLM.
- "Keyword sentiment analysis" when using rule-enhanced or active-learning classification.
- "All comments are meaningful opinion comments" when irrelevant/low-information rows are present.
- "The run converged" only because a distribution table, chart, or audit sample was generated.

## Denominator Disclosure

Always report:

- raw rows;
- cleaned rows;
- duplicate handling policy: volume denominator or deduplicated expression denominator;
- excluded irrelevant/low-information rows;
- uncertain or review-needed rows;
- effective opinion rows;
- final class shares within the effective denominator.
