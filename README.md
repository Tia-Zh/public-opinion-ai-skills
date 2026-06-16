# Public Opinion AI Skills

面向中文舆情、社交媒体评论和表格数据处理的 AI agent skills。

本仓库包含三个可安装 skill：

| Skill | 用途 |
| --- | --- |
| `data-processing-assistant` | 通用表格数据处理：检查文件、识别字段、合并多表、清洗、去重、关键词筛选、统计、图表和导出。 |
| `large-scale-sentiment-analysis` | 大规模中文评论情感/立场/风险分类：抽样 AI 标注、分类器迁移、低置信度和边界样本复核、质量摘要。 |
| `public-opinion-data-workflow` | 融合版入口：先走通用数据处理流程，遇到大样本、全量 AI 成本高或需要复核的情感分析任务时，转入专项流程。 |

## 能力概览

- 有预设分类时：按用户给定分类、关键词规则或标签体系处理。
- 没有预设分类时：可先运行主题发现，使用 TF-IDF + k-means 找候选主题，再由 agent 或人工命名、合并和修正。
- 情感分析小样本时：可以直接使用 AI 按指定标签判断。
- 情感分析大样本时：建议走抽样 AI 标注、分类器迁移、低置信度/边界/反讽/随机样本复核的迭代流程。

## 安装包

可直接使用 `dist/` 下的安装包：

- `dist/data-processing-assistant-installable.zip`
- `dist/large-scale-sentiment-analysis-installable.zip`
- `dist/public-opinion-data-workflow-integrated-installable.zip`

如果 agent 支持导入 skill zip，直接导入对应压缩包即可。

## 使用方式

安装后，把 Excel/CSV 文件发给支持 skills 的 agent，并说明目标，例如：

```text
请使用 $public-opinion-data-workflow 处理这个舆情数据集：
1. 检查工作表和字段；
2. 判断主文本列、时间列、来源列和保留信息列；
3. 清洗、去重、关键词筛选；
4. 如果需要情感分析，请判断是否适合全量 AI，还是转入专项情感分析流程；
5. 输出处理口径、每步数量、结果表、统计图和质量摘要。
```

## 自检

本仓库提供一个轻量自检脚本，用于检查 skill 目录和安装包结构是否完整：

```powershell
python tools/doctor.py --skip-deps
```

如果本机 Python 环境已安装 `pandas` 和 `openpyxl`，也可以运行：

```powershell
python tools/doctor.py
```

## 示例

- `examples/sample_comments.csv`：小型中文评论样例。
- `examples/demo_prompts.md`：通用处理、无预设主题发现、大规模情感分析的演示指令。

## 目录结构

```text
skills/
  data-processing-assistant/
  large-scale-sentiment-analysis/
  public-opinion-data-workflow/
dist/
  *.zip
examples/
tools/
```

每个 skill 目录包含：

- `SKILL.md`：skill 入口说明和执行流程。
- `agents/openai.yaml`：导入 agent 时显示的名称、简介和默认提示。
- `references/`：字段判断、输出标准、标注口径等参考说明。
- `scripts/`：可复用的数据处理、抽样、合并标签、训练分类器和图表脚本。

## 当前边界

- skill 本身不是独立软件，效果取决于安装它的 agent 是否支持读写文件、运行脚本和调用模型。
- 情感分析正式使用时，需要接入可用的 AI API，并通过多轮抽样复核稳定标签标准。
- 对于小样本且预算/时间允许的任务，可以直接用全量 AI 标注；专项情感分析主要用于大样本、成本高、耗时长或需要复核可追溯的场景。
