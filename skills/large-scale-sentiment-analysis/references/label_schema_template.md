# Label Schema Template

Create a task-specific copy of this table before the first LLM labeling batch.

| canonical_label | aliases | definition | positive_examples | negative_examples |
| --- | --- | --- | --- | --- |
| 机会支持 | optimistic/expectant; 乐观期待; 自豪期待 | Supports or expects positive job/work effects from AI. | AI creates new roles; AI improves productivity. | Neutral news about AI investment. |
| 就业焦虑 | anxious/concerned; 焦虑担忧 | Worries about job loss, layoffs, replacement, wage pressure, or career insecurity. | AI will take my job. | General privacy or copyright concern. |
| 风险担忧 | risk concern; 风险担忧 | Worries about safety, governance, privacy, bias, copyright, exploitation, or social risk. | AI hiring tools discriminate. | Direct job-loss panic. |
| 质疑批评 | critical/questioning; 批评质疑 | Criticizes AI claims, hype, company decisions, or policy choices. | AI productivity claims are just layoff cover. | Plain factual reporting. |
| 理性中立 | neutral/analytical; 中性信息 | Factual, analytical, informational, or unclear attitude. | A report says AI affects hiring. | Emotional worry or support. |
| 调侃讽刺 | sarcasm; 调侃讽刺 | Sarcasm, jokes, memes, or ironic comments where literal keywords may mislead. | Sure, AI will totally save us. | Serious criticism without irony. |
| 无关/低信息 | irrelevant/low-information; 无关低信息 | Unrelated, too short, pure prompt, pure emoji, spam, or insufficient context. | Summarize in Spanish. | Short but clear job-loss worry. |
| 拿不准 | uncertain; 混合不确定 | Ambiguous, mixed, context-poor, or needs human/AI review. | Both opportunity and job-loss concern appear. | Dominant attitude is clear. |

Rules:

- Use only `canonical_label` values in all training files.
- Normalize aliases before classifier training.
- If the task needs fewer categories, merge labels deliberately and document the merge.
- If the task needs different categories, replace this table rather than mixing old and new labels.
