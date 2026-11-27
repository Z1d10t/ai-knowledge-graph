# 金标准标注规范（材料事实）

本目录用于 **30 篇冻结评估集**的人工标注与自动评分。开发集（10 篇）和探索性盲测（5 篇）不参与最终指标。

## 1. 文件怎么用

| 路径 | 用途 |
|---|---|
| `eval_set_30.csv / .json` | 冻结的 30 篇清单（方向、类型、DOI） |
| `annotate/<id>.md` | **标注范围**：摘要→结论、含表格，带行号 `[0001]` |
| `gold/<id>.csv` | 金标准表（每人一份，空表 + 一行示例，标注前删掉示例行） |
| `candidates/<id>.csv` | 模型输出，**只作参考**，不得作为标注依据 |
| `eval_index.xlsx` | 进度表（谁标了哪篇、多少条、是否复核） |
| `evaluate.py` | 自动评分脚本 |

标注流程：先读 `annotate/` 的正文，**穷尽**标出范围内的事实 → 填 `gold/` CSV → 全部标完后再打开 `candidates/` 对比漏抽 → 在 `eval_index.xlsx` 登记进度 → 第二人复核 20% 并裁决分歧。

## 2. 标注范围（穷尽，不是抽查）

- 摘要、结果与讨论、结论、**所有结果表格**；
- 不标：引言里的背景常识、参考文献、作者与单位、方法与表征细节中的仪器型号（除非与性能直接相关）。

范围外的内容 `in_scope=0` 保留在表里但不计入召回率分母。

## 3. 一条事实记什么

| 列 | 说明 |
|---|---|
| `subject` / `object` | 原文写法；材料保留大小写与化学式（CsPbI3、Spiro-OMeTAD） |
| `subject_type` / `object_type` | 13 类之一：material / material_class / sample / structure / device / process / condition / property / measurement / characterization / mechanism / defect / interface |
| `predicate_canonical` | 受控谓词（见 §4） |
| `predicate_raw` | 原文动词（若与规范谓词不同） |
| `property` / `value_raw` / `value` / `unit` | 数值事实必填；`value_raw` 保留 `>7.0 eV`、`25.6 ± 0.2%`、`20.1–21.3%` 原样 |
| `comparator` / `uncertainty` | `>`、`±`、范围上下界 |
| `sample_or_device` | 数值属于哪个样品/器件（不能只写材料名） |
| `conditions` | 测试条件（光强、光谱、温度、扫描速率），与工艺条件分开 |
| `characterization` | 表征手段（J-V、XRD、PL…） |
| `evidence_quote` | **逐字**抄写支持该事实的原文片段（≤300 字符），不得改写 |
| `evidence_location` | 章节 / 页码 / 表格行列（例：`Results p.3`、`Table 1 row 2`） |
| `origin` | `stated`（原文直述）/ `ontology`（本体关系）/ `inferred`（推断） |
| `merge_error` | 若模型把两个不同材料/样品误并，填 1 |
| `unmapped_verdict` | 对模型未映射谓词的判断：`useful`（值得进受控表）/ `junk`（语法碎片/低价值）/ `duplicate`（已有同义谓词） |
| `annotator` / `notes` | 标注人、分歧与裁决记录 |

## 4. 受控谓词（标注时优先使用）

```
is a, part of, has formula, doped with, alloyed with, crystallizes in, has phase,
exhibits, achieves, has bandgap, has efficiency, has mobility, has measurement,
degrades after, retains, synthesized by, deposited by, annealed at, annealed for,
treated with, passivated by, measured by, characterized by, used in, composed of,
has layer, stacked with, improves, limits, enables, originates from, attributed to
```

不在表内但确实重要的关系：`predicate_canonical` 留空、`predicate_raw` 填原文，并在 `notes` 写"建议新增"。

## 5. 判定口径（容易分歧的四条）

1. **数值事实**：必须能回答"谁的、哪个性能、多少、什么条件"。缺样品归属 → 记为 `subject` 缺失，`notes` 注明"文本未给出样品"。
2. **证据支持**：证据句必须**直接**表达该关系。主语与宾语同句出现但句子没有表达关系（如列表句）→ 不算证据。
3. **材料 vs 样品**：材料是物质（CsPbI3），样品是被测对象（CsPbI3 film annealed at 150 °C）。同一材料不同工艺的样品必须分开。
4. **不可合并**：不同样品、不同条件下的相同数值是两条事实；不同化学计量比的材料不得合并。

## 6. 自动评分

```bash
python evaluation/evaluate.py --gold evaluation/gold --pred evaluation/kg_output_eval/enriched
```

计算：关系 P/R/F1（主谓宾严格匹配，数值事实按 主语+性能+值+单位 匹配）、实体 P/R/F1、数值严格准确率、证据文本匹配率（自动，不等于人工确认）、未映射谓词裁决统计、误合并计数。

> `evidence_text_match=true` 只表示模型给的证据句能在原文中逐字找到；是否**支持**该事实，仍以人工 `evidence_quote`/复核为准。

## 7. 复核与冻结

- 第二人复核 ≥20%（按方向和类型各抽 1/5），分歧记入 `notes` 并裁决；
- 评估期间**冻结** prompt、谓词表、规则；任何修改都必须换一套未参与调整的论文重新复核。
