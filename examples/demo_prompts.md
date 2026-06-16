# Demo Prompts

## 通用数据处理

```text
请使用 $data-processing-assistant 处理 examples/sample_comments.csv：
检查字段，识别主文本列，清洗文本，按来源和日期做基础统计，并导出可复核结果。
```

## 无预设主题时的主题发现

```text
请使用 $public-opinion-data-workflow 分析 examples/sample_comments.csv。
我还没有预设主题分类，请先用主题发现方法找候选主题，输出每类代表词和代表评论，再给出建议主题名。
```

## 大规模情感分析流程演示

```text
请使用 $large-scale-sentiment-analysis 处理 examples/sample_comments.csv。
这是小样本演示：请说明正式大样本场景下应如何清洗、抽样、AI 标注、分类器迁移、低置信度复核和输出质量摘要。
```
