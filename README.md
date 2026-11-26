# 材料专业术语知识图谱 · 完整项目

从 285 篇材料论文中抽取、规范化并交付一个可交互、可追溯的术语知识图谱。

## 现在是什么

- **285 篇论文** → 70,802 条原始三元组（关系候选 41,324、观测 16,829、数值事实 12,649）
- 去重与补全后 **39,400 条规范关系**，覆盖 **51,464 个专业概念**、920 个论文内实例
- 每条关系尽量带 `paper_id`、原文引文和 Markdown 行号（96.3% 可定位）
- 一个离线交互页面：全库大图、全部关系、类型汇总、术语邻域；支持搜索、筛选、证据回查、中英文切换
- 一套可直接移交的数据：`triples_full.csv`（18 列）、`triples_full.jsonl`、页面 `data/`、GEXF、285 篇原文

## 30 秒跑起来（不需要 LLM）

```powershell
cd 材料知识图谱_完整项目_20261126
python scripts/check_env.py
python scripts/run_tests.ps1                 # 167 passed, 1 skipped
powershell -ExecutionPolicy Bypass -File scripts/demo_export.ps1   # 两篇论文示例，11/11 校验
```

打开示例页面：

```powershell
python -m http.server 8770 --bind 127.0.0.1 --directory examples/mini_package
# http://127.0.0.1:8770/
```

打开完整交付页面：

```powershell
python -m http.server 8766 --bind 127.0.0.1 --directory delivery/materials_kg_final
# http://127.0.0.1:8766/
```

如果 `delivery/materials_kg_final/` 不存在，先解压 `delivery/materials_kg_v3.1-delivery.zip`。

## 文档

| 文档 | 内容 |
|---|---|
| [`docs/01_项目总览.md`](docs/01_项目总览.md) | 项目定位、规模、三层数据、目录、边界 |
| [`docs/02_快速开始.md`](docs/02_快速开始.md) | 安装、测试、示例、页面、配置 |
| [`docs/03_代码架构.md`](docs/03_代码架构.md) | 分层、调用链、文件职责、数据契约 |
| [`docs/04_核心模块.md`](docs/04_核心模块.md) | config / llm / prompts / text_utils / profiles / main |
| [`docs/05_术语与图谱模块.md`](docs/05_术语与图谱模块.md) | terminology / 标准化 / 观测 / 检索 / 问答 / 服务 / 可视化 / 导出 |
| [`docs/06_数据模型.md`](docs/06_数据模型.md) | v2、v3、交付包每层字段与计数口径 |
| [`docs/07_图谱页面.md`](docs/07_图谱页面.md) | 前端结构、渲染、交互、双语、导出 |
| [`docs/08_评估与交付脚本.md`](docs/08_评估与交付脚本.md) | normalize_v3、补抽、指标、导出、汇报包 |
| [`docs/09_运行手册.md`](docs/09_运行手册.md) | 从 285 篇论文复现到交付包的完整命令 |
| [`docs/10_测试与质量.md`](docs/10_测试与质量.md) | 测试结构、质量检查、已知缺口 |
| [`docs/11_常见问题.md`](docs/11_常见问题.md) | 页面、数据、抽取、交付问题 |

## 目录

```
src/knowledge_graph/       Python 包（抽取、术语、检索、页面、导出）
tests/                     26 个 pytest 文件
evaluation/                规范化、补抽、评估脚本 + 小体积参考数据
article/                   语料处理、交付导出、汇报包
scripts/                   环境检查、示例、测试、打包
examples/                  两篇论文的可运行示例
data/samples/              上游通用图谱样例
delivery/                  交付包、汇报包、报告、截图
docs/                      本套文档
```

## 数据说明

- 完整的 285 篇原文、v2/v3 全量数据体积较大（约 1.3 GB），未放进源码包；
  交付 ZIP（`delivery/materials_kg_v3.1-delivery.zip`，约 28 MB）已包含 285 篇原文和全量交付数据。
- 源码包内的 `examples/` 是两篇论文的截取，用于无数据、无 LLM 的冒烟运行。
- 重新抽取全量需要 LLM 端点；步骤见 `docs/09_运行手册.md`。

## 质量与边界

- 质量口径：计数守恒、端点完整、证据可定位、包可校验（15/15）。
- 未做独立语义准确率/召回率评估。
- 已知待清：65 个重复规范名、159 条方向待复核、44 条自环、342 条 `not reported`、4,799 条引文未逐字命中。
- 页面与数据都是**论文级声明图**，不是跨论文共识库。

## 来源与许可

- 基于 [robert-mcdermott/ai-knowledge-graph](https://github.com/robert-mcdermott/ai-knowledge-graph)（Apache-2.0）扩展。
- 材料 profile、v3 术语层、`materials_overview.*` 页面和交付脚本为项目内新增。
- 许可证见 [`LICENSE`](LICENSE)。

## 验证清单

```powershell
python scripts/check_env.py
python -m pytest tests -q
python article/export_materials_graph.py --verify-only --output-dir examples/mini_package
python article/export_materials_graph.py --verify-only --output-dir delivery/materials_kg_final   # 若已解压
```
