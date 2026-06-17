# Install

## 推荐方式

优先导入融合版：

```text
dist/public-opinion-data-workflow-integrated-installable.zip
```

导入后，对 agent 说：

```text
请使用 $public-opinion-data-workflow 处理这个中文舆情数据集。
```

## 拆分安装

只有在你明确需要拆分能力时，再单独安装：

```text
dist/data-processing-assistant-installable.zip
dist/large-scale-sentiment-analysis-installable.zip
```

通用数据处理模块会在大规模中文情感/态度分析场景中转入专项流程。

## 安装后验证

把 `examples/sample_comments.csv` 发给 agent，然后使用 [QUICKSTART.md](QUICKSTART.md) 里的提示词测试。

本地工程自检：

```powershell
python tools/doctor.py --skip-deps
```
