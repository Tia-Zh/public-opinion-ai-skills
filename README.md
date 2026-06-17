# Public Opinion AI Skills

面向中文舆情数据处理和大规模评论情感/态度分析的 agent skill toolkit。

这个项目的目标不是做一个固定话题分类器，而是让 agent 能在不同中文舆情议题下完成一条可复核的工作流：

```text
检查文件和字段
-> 隐私审计/脱敏
-> 清洗、去重、筛选
-> 确认或建立情感/态度标签口径
-> 抽样 AI 标注
-> 分类器迁移到全量
-> 低置信、边界、反讽、随机样本复核
-> 导出统计、图表和质量摘要
```

## 推荐安装

普通用户只需要安装一个 skill：

```text
dist/public-opinion-data-workflow-integrated-installable.zip
```

它是融合版入口，内部包含通用表格处理和大规模情感分析流程。

另外两个 zip 主要给开发者或高级用户拆分使用：

- `data-processing-assistant-installable.zip`：通用表格数据处理。
- `large-scale-sentiment-analysis-installable.zip`：大规模中文评论情感/立场/态度分析。

## 核心能力

- Excel/CSV/TSV、多工作表检查和字段识别。
- 平台、时间、正文、链接、用户、位置、指标等字段角色判断。
- 隐私审计、敏感列哈希、正文 URL/@/邮箱/手机号遮盖。
- 文本清洗、低信息过滤、去重、关键词筛选。
- 有标签体系时，按既定情感/态度标签处理。
- 无标签体系时，先抽样、聚类/关键词探索，再建立适合该议题的标签口径。
- 大规模数据下，用“AI 标注样本 + 分类器迁移 + 复核迭代”替代全量逐条 AI 标注。
- 可选参考标签对照：一致率、混淆矩阵、差异样本。
- 导出处理明细、删除记录、统计表、图表、质量摘要。

## 目录

```text
skills/
  public-opinion-data-workflow/        # 推荐安装入口
  data-processing-assistant/           # 内部通用处理模块
  large-scale-sentiment-analysis/      # 内部专项情感分析模块
dist/
  *.zip                                # 可导入 agent 的安装包
examples/
  sample_comments.csv                  # 小型示例数据
  demo_prompts.md                      # 示例提示词
tools/
  doctor.py                            # 项目结构和依赖自检
```

## 快速开始

详见：

- [INSTALL.md](INSTALL.md)
- [QUICKSTART.md](QUICKSTART.md)
- [METHOD.md](METHOD.md)
- [PRIVACY.md](PRIVACY.md)
- [EVALUATION.md](EVALUATION.md)
- [ROADMAP.md](ROADMAP.md)

## 自检

```powershell
python tools/doctor.py --skip-deps
python tools/doctor.py
```

`--skip-deps` 只检查 skill 文件和 zip 结构；不加参数会额外检查 `pandas`、`openpyxl` 等本地依赖。

## 当前边界

- Skill 不是独立软件，效果取决于安装它的 agent 是否支持读取文件、运行脚本和调用模型。
- 对大规模情感分析，不应声称每一条都由 AI 逐条标注，除非确实全量送入 AI。
- k-means/关键词聚类只用于发现表达簇和辅助建立标签口径，不等于最终情感分类器。
- 参考标签对照是验证手段，不自动代表真实准确率。
