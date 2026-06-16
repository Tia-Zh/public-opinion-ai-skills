# Sentiment Labeling

Use this reference when the user asks for emotion, sentiment, attitude, tone, or positive/neutral/negative labels.

## Default Labels

Use three labels unless the user provides another label set:

- `正面`: approval, praise, satisfaction, support, trust, gratitude, relief, constructive optimism.
- `中立`: factual description, unclear attitude, simple forwarding, objective question, mixed emotion without a clear dominant direction.
- `负面`: complaint, dissatisfaction, anger, worry, fear, accusation, sarcasm, distrust, grief, urgency, or criticism.

## Judgment Rules

Judge the attitude expressed in the text itself, not the topic alone. A text about a negative event can still be neutral if it only reports facts.

For public-opinion or service-response data, classify by the author's stance or emotional attitude:

- "救援很及时，辛苦了" -> `正面`
- "今天城区又积水了，什么时候能解决" -> `负面`
- "暴雨黄色预警发布，请注意出行安全" -> `中立`
- "这效率可真是太高了，等了三天还没人来" -> `负面`

Sarcasm and rhetorical praise should be treated by actual meaning, not surface praise words.

If the text is too short, ambiguous, or only contains a keyword with no attitude, choose `中立` and lower the confidence.

## Recommended Output Columns

For each labeled row, add:

- `情绪标签`: `正面` / `中立` / `负面`
- `情绪置信度`: high / medium / low, or 0-1 if the user requests numeric confidence
- `情绪判断依据`: short plain-language reason

For large datasets, label in batches and sample-check edge cases. If confidence is low or the consequences are important, export a `需人工复核` column.
