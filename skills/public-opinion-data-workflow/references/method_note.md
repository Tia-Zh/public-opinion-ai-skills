# Method Note Template

Use this when writing a report methodology section.

## Recommended Method Wording

This study used a large-model-assisted, auditable classification workflow. First, raw comments were cleaned and de-identified while preserving the volume denominator; duplicate texts were marked with hash/count fields and, when needed, analyzed separately as a deduplicated expression view. A stable label taxonomy was then defined. A large model labeled stratified and uncertainty-selected samples to establish category boundaries. Based on those labeled samples, an automatic classifier was calibrated and applied to the full cleaned dataset. Low-confidence, uncertain, sarcasm-like, and randomly sampled cases were reviewed to improve reliability.

## Chinese Report Wording

本研究采用“大模型辅助标注 + 自动分类迁移 + 疑难样本复核”的混合方法。首先对原始评论样本进行清洗与脱敏，同时保留声量口径；对重复文本增加哈希和重复次数标记，必要时另行生成去重表达口径。随后构建稳定的标签体系，并按平台、时间和事件窗口抽取分层样本，由大模型进行语义标注，用于建立分类口径和边界案例。之后将标注口径迁移至自动分类器，对全量样本进行一致性分类。最后对低置信度、拿不准、疑似反讽及各类别随机样本进行复核，以提高分类结果的可解释性和稳定性。

## What To Avoid

Do not claim:

- "The LLM labeled every row" unless every row was actually sent to an LLM.
- "Keyword sentiment analysis" when using rule-enhanced or active-learning classification.
- "All comments are meaningful opinion comments" when irrelevant/low-information rows are present.

## Denominator Disclosure

Always report:

- raw rows;
- cleaned rows;
- duplicate handling policy: volume denominator or deduplicated expression denominator;
- excluded irrelevant/low-information rows;
- uncertain rows;
- effective opinion rows;
- final class shares within the effective denominator.
