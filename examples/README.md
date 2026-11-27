# 两篇论文示例

由 `scripts/build_mini_example.py` 从 `evaluation/full_v3_delivery` 截取，用于在没有全量数据时
跑通导出与校验：

```powershell
python article/export_materials_graph.py --input-dir examples/mini_v3 --papers-dir examples/mini_papers --output-dir examples/mini_package --force
python article/export_materials_graph.py --verify-only --output-dir examples/mini_package
```
