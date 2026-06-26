# Sentiment Labeling

Use this reference when the user asks for emotion, sentiment, attitude, tone, or positive/neutral/negative labels.

## Default Labels

Use three output labels unless the user provides another report label set:

- `正面`: approval, praise, satisfaction, support, trust, gratitude, relief, constructive optimism.
- `中立`: relevant factual description, objective question, balanced discussion, or relevant comment with no clear positive/negative direction.
- `负面`: complaint, dissatisfaction, anger, worry, fear, accusation, sarcasm, distrust, grief, urgency, or criticism.

These are final output labels, not the full internal processing schema. They do not mean every row must be forced into one of the three labels. Before assigning them, decide whether the row is relevant to the user's topic and meaningful enough to enter the denominator.

Use internal flags or labels when needed:

- `无关/偏题`: unrelated to the requested topic, cross-topic chatter, advertising, or platform noise.
- `低信息/不可判断`: empty, contextless, unusable, or pure signal where relevance cannot be established.
- `需复核`: conflicting cues, unclear target, low confidence, or model/human disagreement.

Report these separately. Do not force them into `中立` unless the user explicitly asks for every row to receive one of the output labels. If the user says "输出正面/中性/负面", treat that as the final sentiment distribution for effective rows; still create separate relevance/effectiveness or exclusion fields for off-topic, spam, and low-information rows.

Hard denominator gate: before reporting any sentiment percentage, the row-level result must include `是否纳入情感分母` and `排除原因` or equivalent columns, and the summary must state the final `有效分母`. If these are missing, do not output final positive/neutral/negative shares. First add the denominator decision, audit excluded/low-information rows, and rerun the summary.

Short text is not deleted for being short; separate it into explicit plain-text attitude signals and low-information candidates. Explicit plain-text attitude signals enter the sentiment denominator. Low-information candidates are counted separately, sampled for review, and not forced into `中立` by default. Common low-information examples include pure acknowledgements or greetings such as `了解`, `好的`, `收到`, `知道了`, `早安`. Rows made only of emoji or bracketed platform emoji such as `[赞]`, `[强]`, `[捂脸]`, `[玫瑰]`, or `[微笑]` should be removed from the prepared sentiment sample by default and counted separately, not counted as `中立`. Short plain-text attitude signals such as `支持`, `赞成`, `反对`, and `不支持` are meaningful and should be labeled by attitude.

Do not strip emoji inside longer text during the first cleaning step because they may help interpret tone. Remove rows made solely of emoji or bracketed platform emoji from the prepared sentiment sample by default, and write them to a removed/audit file with row counts.

## Judgment Rules

Judge the attitude expressed in the text itself, not the topic alone. A text about a negative event can still be neutral if it only reports facts.

For public-opinion or service-response data, classify by the author's stance or emotional attitude:

- "救援很及时，辛苦了" -> `正面`
- "今天城区又积水了，什么时候能解决" -> `负面`
- "暴雨黄色预警发布，请注意出行安全" -> `中立`
- "这效率可真是太高了，等了三天还没人来" -> `负面`

Sarcasm and rhetorical praise should be treated by actual meaning, not surface praise words.

If the text is relevant but has no clear positive or negative attitude, choose `中立`. If it is unrelated, off-topic, spam, contextless, or impossible to connect to the user's topic, mark it as an exclusion/review category instead of `中立`.

Use `中立` for meaningful relevant content, such as factual statements, genuine questions, procedural explanations, or balanced discussion. Do not use `中立` as the default bucket for texts that contain too little information to judge.

## Recommended Output Columns

For each labeled row, add:

- `情绪标签`: `正面` / `中立` / `负面`
- `情绪置信度`: high / medium / low, or 0-1 if the user requests numeric confidence
- `情绪判断依据`: short plain-language reason
- `相关性/有效性`: relevant/effective vs irrelevant/low-information when needed
- `是否纳入情感分母`: yes/no when exclusions exist
- `排除原因`: required when `是否纳入情感分母` is no
- `有效分母`: report-level summary count used as the denominator for percentages

For large datasets, label in batches and sample-check edge cases. If confidence is low or the consequences are important, export a `需人工复核` column.
