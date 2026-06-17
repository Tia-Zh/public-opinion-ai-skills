# General Data Processing Workflow

## 1. Understand the source

Inspect files before processing. For each sheet or table, capture:

- row count and column count
- column names
- likely column roles
- missing-value rates
- representative examples
- obvious problems such as duplicated headers, blank rows, merged title rows, or inconsistent column names

For multi-sheet workbooks, do not flatten everything immediately. Inspect each sheet first, then decide whether sheets share a compatible structure.

## 2. Define the processing target

Clarify or infer:

- main content columns: the columns being cleaned, filtered, optionally deduplicated, labeled, or analyzed
- keep columns: metadata columns to retain in the final output
- key columns: columns that uniquely identify a record or may be used for optional dedupe
- time columns: columns used for date filtering or trend charts
- grouping columns: category, platform, department, region, author, source, product, status, or similar fields

If the user only needs one column exported, allow all other columns to be omitted.

## 3. Plan transformations as named steps

Typical order:

1. Load and align sheets.
2. Standardize selected fields.
3. Clean text or normalize values.
4. Remove empty or invalid rows.
5. Apply date/category/keyword filters.
6. Mark duplicates with hash/count fields.
7. Deduplicate only when the user asks for a unique-expression view, spam cleanup, or a task where duplicates would corrupt the result.
8. Add labels or derived columns.
9. Summarize and chart.
10. Export data, removed rows, charts, and a step log.

The order can change. For sentiment, stance, policy feedback, or public-opinion share analysis, do not default to dedupe: repeated short comments are part of the observed volume. If dedupe is needed, produce a separate deduplicated view and keep `duplicate_count` so the volume can be restored.

## 4. Preview and audit

After each significant step, provide:

- rows before
- rows after
- rows removed
- a short sample of kept rows
- a short sample of removed rows when deletion is substantial

Preserve source sheet and source row whenever records come from Excel sheets. This helps users trace results back to the original workbook.

## 5. Export

Prefer Excel output for office users:

- `处理结果`: final data
- `删除记录`: rows removed by filters or optional dedupe, when applicable
- `处理日志`: step names, before/after counts, parameters
- `字段说明`: original column names, inferred roles, renamed output columns

Use Chinese column names when the user is Chinese-speaking or the source data is Chinese. Use plain names such as `来源工作表`, `来源行号`, `处理后文本`, `命中关键词`, `情绪标签`, `主题标签`.
