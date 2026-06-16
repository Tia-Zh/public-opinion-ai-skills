# Semantic Judgment Guidance

This skill is used by Codex, so ordinary judgment tasks inside this skill are handled by Codex directly.

Use Codex's judgment for tasks that need semantic understanding:

- field mapping when column names vary across sheets
- exclusion-word suggestions
- sentiment labels such as `正面` / `中立` / `负面`
- topic labels and category names
- cluster naming
- concise summaries
- anomaly explanations

Use deterministic code for tasks that should be exact:

- row counts
- filtering by exact keyword/date/category rules
- exact dedupe
- date parsing
- arithmetic summaries

## Output Discipline

Judgment-based labels should include enough evidence to audit. For batch labeling, prefer columns like:

- `标签`
- `置信度`
- `判断依据`

For external systems, follow the separate integration instructions for that system; do not mix those requirements into this general data-processing skill.
