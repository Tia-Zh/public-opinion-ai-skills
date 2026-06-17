# Semantic Judgment Guidance

This skill is used by Codex, so ordinary judgment tasks inside this skill may be handled by the current AI agent directly when no external LLM/API is available.

Direct AI judgment means reading the sampled text as natural language and assigning labels according to the schema. It does not mean writing a keyword or heuristic script and treating the script output as AI labels. Scripts may prepare batches, enforce CSV schemas, merge labels, and check counts; they must not replace semantic labeling.

Use Codex's judgment for tasks that need semantic understanding:

- field mapping when column names vary across sheets
- exclusion-word suggestions
- sentiment labels such as `正面` / `中立` / `负面`
- topic labels and category names
- cluster naming
- concise summaries
- anomaly explanations

For sentiment sample labeling, label manageable batches with natural-language reasoning. If the requested sample is too large to label carefully in one pass, reduce the batch size, split batches, ask for an external API, or ask the user whether a quick weak baseline is acceptable. Do not silently convert the labeling step into rule-based pseudo-labeling.

Use deterministic code for tasks that should be exact:

- row counts
- filtering by exact keyword/date/category rules
- exact dedupe when the user explicitly asks for a deduplicated view; do not treat dedupe as the default for sentiment share analysis
- date parsing
- arithmetic summaries

## Output Discipline

Judgment-based labels should include enough evidence to audit. For batch labeling, prefer columns like:

- `标签`
- `置信度`
- `判断依据`

For external systems, follow the separate integration instructions for that system; do not mix those requirements into this general data-processing skill.
