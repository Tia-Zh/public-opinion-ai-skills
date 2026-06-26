# Output Standards

## File naming

Use clear names:

- `原文件名_处理结果_YYYYMMDD_HHMMSS.xlsx`
- `原文件名_图表_YYYYMMDD_HHMMSS`

Avoid overwriting existing files.

## Excel sheets

For general office users, prefer:

- `处理结果`
- `删除记录`
- `处理日志`
- `字段说明`

For charts exported as images, place files in a sibling folder and list paths in `处理日志`.

## Column naming

Use user-facing names, not internal code names. Examples:

- `来源工作表`
- `来源行号`
- `处理后文本`
- `命中关键词`
- `情绪标签`
- `主题标签`
- `删除原因`

For any sentiment/stance output, include denominator fields before reporting shares:

- `是否纳入情感分母` or an equivalent inclusion flag
- `排除原因` for rows excluded from the denominator
- an effective-denominator summary, such as `有效分母`

If these fields are missing, the output is a diagnostic/intermediate file, not a final sentiment report.

## Charts

Every chart should have:

- a specific title, not just `图表`
- readable axis labels
- source column or grouping meaning made obvious
- saved PNG path reported to the user

Choose chart types based on data:

- category counts: bar chart
- time trend: line chart
- cross-tab: stacked bar or heatmap
- numeric relationship: scatter plot
- clustering: scatter plot or heatmap if embeddings/features are available
