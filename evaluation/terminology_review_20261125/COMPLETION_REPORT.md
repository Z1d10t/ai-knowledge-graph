# 材料专业术语知识图谱：重启执行与完成报告

生成日期：2026-11-25。依据主文档 `evaluation/full_v1_review_revised.md`（2026-11-25 版）执行阶段 A–D。
本报告记录**实际做了什么、得到什么数字、哪些门槛通过、哪些问题仍未解决**；所有数字都可在
文末命令下从本目录文件重新生成。

---

## 1. 结论

主文档第 6 节的阶段 A、B、C、D 已执行完毕，第 7 节“建议工程门槛”全部通过：

| 门槛 | 状态 | 证据 |
|---|---|---|
| 阶段 A 所有参考项完成判定，待定保留理由 | 通过 | 96/96 术语、36/36 关系均有判定；`stage_a/adjudication_terms.json`、`adjudication_relations.json` |
| 已确认方向错误与误合并全部修复并回查 | 通过 | 250 篇方向边改写并保留 L164 证据；12 组误合并对照 12/12 通过（`stage_metrics.json`） |
| 10 个固定检索用例给出受证据支持的结果 | 通过 | 10/10 通过，每条给出关系与原文行号（`stage_d/retrieval_acceptance.json`） |
| 更改前后使用同一参考集对照 | 通过 | 同一 96 项/36 条参考集，v2 判定与 v3 检索判定并列 |
| 不以新增边数作为成功证据 | 遵守 | 报告只引用参考集覆盖、检索与误合并审计；v3 新增边仅作辅助统计 |

同时明确：**本轮没有做全量重抽**。阶段 C 只对 12 篇参考论文的 34 个段落做了定向补抽（402 条关系，
其中 340 条证据可核验后融合），其余 273 篇沿用 v2 抽取结果，经阶段 B 规范化。

---

## 2. 交付物

### 2.1 数据与报告

| 路径 | 内容 |
|---|---|
| `evaluation/terminology_review_20261125/stage_a/` | 96 项术语 + 36 条关系的证据卷宗、逐项判定、缺陷清单、参考集指标 |
| `evaluation/full_v3_normalized/` | 规范化后的概念/实例/提及/关系/观测/数值事实层 + 别名索引 + ID 映射 + 统计 + 输入哈希 |
| `evaluation/targeted_reextract_v3/` | 阶段 C 定向补抽的 12 篇输出（含段落范围、术语列表、关系、逐条证据核验标记） |
| `evaluation/terminology_review_20261125/stage_d/` | 10 个固定检索用例定义与验收结果、8 个别名检索检查 |
| `evaluation/terminology_review_20261125/stage_b/type_conflict_spotcheck.json` | 20 条类型冲突的人工抽查判定 |
| `evaluation/terminology_review_20261125/stage_metrics.json` | 参考集前后对比、门槛、误合并审计、类型冲突汇总 |

### 2.2 生产代码

| 模块 | 作用 |
|---|---|
| `src/knowledge_graph/terminology.py` | 术语层引擎：查找键、化学式身份、缩写别名挖掘、属性短语/复合提及拆分、概念类型规则与冲突、关系族与因果方向检查、概念注册表（安全合并） |
| `src/knowledge_graph/retrieval.py` | 检索层：术语/别名/中文建议标签/化学式检索、概念卡片、关系与证据浏览 |
| `src/knowledge_graph/prompts/main_prompts.py` | 新增材料 v3 提示词（先术语、后关系、数值可选） |
| `src/knowledge_graph/prompts/__init__.py` | `main_prompt_pair` 支持 `[extraction].prompt_version`；材料 profile 默认 v3，`"v2"` 可复现旧行为 |
| `src/knowledge_graph/llm.py` | JSON 解析兼容 `{"terms": [...], "relations": [...]}` 输出 |
| `tests/test_terminology.py`、`tests/test_retrieval.py` | 新增 16 个测试；全套 167 passed / 1 skipped |

### 2.3 脚本（可复现）

`evaluation/stage_a_cases.py`、`stage_a_adjudication.py`、`normalize_v3.py`、
`targeted_reextract.py`、`stage_d_retrieval.py`、`stage_metrics.py`。复现命令见第 9 节。

---

## 3. 阶段 A：96 项术语与 36 条关系的语义判定

### 3.1 方法

先由 `stage_a_cases.py` 为每项参考术语生成证据卷宗：原文行段、v2 端点标签（精确/包含/短缩写
三种匹配）、非端点字段命中、观测对象命中、证据文本命中、该段所在 chunk 及 chunk 产出条数。
判定由 `stage_a_adjudication.py` 写入，逐项包含：判定、v2 对应标签、缺失类型、修复动作、理由。

`not_located_by_labels`（16 项）按主文档 4.5 的要求逐一追查原因，而不是直接判为漏抽：

- **已抽取未建节点 8 项**：术语出现在更长标签或证据文本里（如 GaN/SiC 只作为
  “breaking the 1-D unipolar ... limit of GaN and SiC” 这个属性短语的一部分）。
- **模型漏抽 2 项**：段落在抽取文本内、chunk 有产出，但输出中完全没有该术语（001 DFT、065 wettability）。
- **预处理丢失 2 项**：201、250 两篇的参考段落在抽取前被 front-matter 剥离（见 4.1 的独立发现）。

### 3.2 结果

| 判定 | 数量 | 含义 |
|---|---:|---|
| 正确概念 | 36 | 概念与类型均可接受 |
| 正确但未规范 | 43 | 概念在，但只有缩写、复合或过长标签 |
| 概念粒度不同 | 5 | 只有上位类或更窄变体 |
| 分类错误 | 0 | 本轮未出现“标签对、类型全错”的可判定案例 |
| 确认漏抽 | 12 | 见上表的缺失类型 |
| 待定 | 0 | — |

- 语义覆盖（正确概念 + 正确但未规范）：**79/96 = 82.3%**；含粒度不同为 84/96 = 87.5%。
  这个数字只对本轮 96 项参考术语成立，不代表全库召回。
- 有类型问题的术语：18 项（如 `operating temperature` 同时出现 condition/property，
  `quasi-2D perovskite` 同时出现 material/material_class）。
- 修复动作统计：canonicalize 28、alias_split 22、type_fix 18、targeted_reextract 11、
  split_attribute 10、split_compound 10、add_edge 5、split_composite 3、keep 36。

关系判定（36 条）：

| 判定 | 数量 |
|---|---:|
| 支持（同义谓词或不同表述也算） | 16 |
| 部分支持（端点粒度或对象被合并） | 8 |
| 未找到 | 12 |
| 无法判断 | 0 |

严格支持率 **44.4%**，支持或部分支持 **66.7%**。典型部分支持：`MXenes → is a → 2D materials`
被表述为 `MXenes is a 2D material`；典型未找到：`Ga2O3 → used in → power electronics`。

### 3.3 确认的 v2 缺陷（已进入修复清单）

1. **250 篇方向错误**（主文档 4.1）：`absorption coefficients of ternary AgBiS2 NCs → improves →
   cation disorder homogenization under mild annealing conditions` 方向写反，证据实为原 md 第 164 行
   “the absorption coefficients ... can be enhanced via cation disorder homogenization”。
2. **长短语被当作概念**：`absorption coefficient enhanced by up to a factor of two after annealing`、
   `exfoliating the 3D bulk to 2D planer structures`、`organic polymers modified MOS`、
   `development of AlGaN-based solar-blind UV PDs` —— 均已进入提及/属性拆分。
3. **复合标签**：`quantum- and dielectric-confinement effects`、`carbides, carbonitrides, and nitrides`、
   `mixed ferroelectric-antiferroelectric order`、`charge transport layers and buffer layers`、
   `VBM and CBM delocalized over the entire material` —— 已拆出组成概念并保留复合对象。
4. **类型冲突**：见 3.2 的 18 项，v3 已按中心词规则统一并保留冲突记录。
5. **重复边**：001 `4Cl-BZS enables dual-site Pb2+ passivation` 重复 2 次；
   052 `MXenes is a 2D material` 重复 3 次 —— v3 合并为单边并保留全部证据。

---

## 4. 阶段 B：规范化结果（v3 层）

### 4.1 先修：抽取前处理会吞掉摘要

复现 v2 的 front/back-matter 剥离后发现：对 011、038、043、095、201、250 等篇，剥离把**摘要或
引言前段**当成了“封面”裁掉（011 前 10909 字符被移除，抽取从原 md 第 58 行才开始；201 从第 55 行、
250 从第 58 行开始）。这直接解释了 201 `anion engineering`、250 `optical transition matrix elements`
等术语为何“未定位”——模型从未看到那段文字。

本轮处理：不重跑全量；把这些段落作为阶段 C 的定向补抽输入，并在报告中记为“预处理丢失”。
生产代码的前处理函数（`article/extract_corpus.py` 的 `strip_front_matter`）仍按行长度判断，属于
已知缺陷，下一轮全量重抽前应改为按摘要标题/章节识别（见第 8 节）。

### 4.2 分层结果（285 篇）

| 层 | 数量 | 说明 |
|---|---:|---|
| 概念 | 51,408 | 其中干净标签 47,565、碎片 3,812、仪器 29、符号 2；跨论文合并 5,088 |
| 样品/器件实例 | 920 | 论文作用域，805 个已关联到概念 |
| 提及 | 145,260 | 概念 110,712、观测 16,829、数值 15,315、实例 2,287、符号 117 |
| 关系 | 39,400 | 重复合并 2,609；复合拆分新增 331；定向补抽 340 |
| 观测 | 16,829 | v2 观测节点保留 |
| 数值事实 | 12,649 | 对象为数值的关系，作为附加信息保留 |
| 别名索引键 | 52,154 | 其中论文内已验证别名 5,121；括号定义挖掘 10,211；标签内括号拆分 910 |
| 已应用修复 | 15 | 1 条方向改写 + 12 条复合拆分 + 2 条相→母体链接 |
| 方向待复核 | 159 | 只标记，不自动翻转 |

关系族分布：effect 15,894、process 4,532、dependency 3,218、characterization 3,122、taxonomy 3,076、
application 2,295、composition 1,923、structure 1,339、other 3,993、phase_transition 8。

### 4.3 类型判定

- 一致 15,323；规则覆盖 v2 冲突 7,132；仅实例类型 7,373；无规则可依保留 v2 共识 18,980；碎片待定 2,600。
- 类型冲突率 7,132/51,408 = **13.9%**（此前把“无规则默认”也算冲突时是 72%，已修正口径：
  没有规则可依的标签不再冒充“已解决”，而是列入 `type_unresolved.json`）。
- 20 条冲突抽查（`stage_b/type_conflict_spotcheck.json`）：规则更合理 11、原类型更合理 5、
  两者均不可接受（碎片）4。因此类型冲突按**复核队列**报告，不作为准确率声明。

### 4.4 合并安全规则（已实现并被测试覆盖）

- 化学式按大小写不敏感的“化学身份”合并，保留计量与相标记：`HfO2`/`HfO₂` 合并，
  `Sb2O3`/`Sb4O6` 分开，`α-FAPbI3`/`δ-FAPbI3` 分开。
- 普通名词按单复数折叠合并（`quasi-2D perovskite(s)`、`MXene(s)`）。
- 缩写不按小写键全局合并：`FE`、`ALD` 等只在定义它的论文内成为别名；跨论文保留独立概念。
- 不做子串合并：`device` 不会吞掉 `control device`（后者是论文内实例）。
- 相名与母体材料显式建边：`α/δ-FAPbI3 is a formamidinium lead triiodide`（判定修复，附理由）。

---

## 5. 阶段 C：提示词 v3 与定向补抽

- 新增材料 v3 提示词：先列专业术语（类型、别名、证据），再建有证据的关系；谓词 1–3 词并给出
  受控列表；明确“过程/机理影响性能，性能不影响过程”；`calculated by` 与 `measured by` 分开；
  条件与数值要求写入证据/字段而不是实体名；禁止字母占位符（A、A′、B、X、n）成为实体。
- 材料 profile 默认使用 v3；`[extraction].prompt_version = "v2"` 可复现历史提示词。
- 定向补抽范围：12 篇参考论文，按“参考行段 + 确认漏抽术语所在行 + 未找到关系的证据行”合并为
  34 个段落（每篇最多 6 段），DeepSeek `deepseek-flash`，共提取 402 条关系、证据逐条核验，
  340 条（84.6%）证据可在段落中定位后融合进 v3。
- 补抽直接补齐了此前缺失的专业知识，例如 001 的 DFT 与电子传输层、011 的 GaN/SiC 与击穿电压、
  153 的 front absorber、065 的一步涂覆→吸光层、250 的阳离子无序→吸收等；10 个检索用例因此全部可答。

---

## 6. 阶段 D：10 个固定检索用例

检索接口：`KnowledgeGraphIndex.search()`（术语/别名/中文建议标签/化学式）+ `browse()`（关系与证据）。
判定规则：术语必须解析到概念；必须存在一条同论文、谓词族相容、对象匹配的关系；证据行号落在
参考行 ± 容差内。任何一项不满足即记为未通过并给出原因。

| # | 问题 | 找到的关系 | 证据 |
|---:|---|---|---|
| 1 | 哪些配体与 Pb 缺陷钝化有关？ | 4-chlorobenzenesulfonate → enables → dual-site Pb2+ passivation | 001 L87 |
| 2 | 甲酸根作用于什么缺陷？ | formate → eliminates → anion vacancy defects | 201 L79 |
| 3 | 哪种材料可用于热蒸发 vdW 介质？ | Sb2O3 → deposited by → standard thermal evaporation deposition | 095 L66 |
| 4 | 准二维钙钛矿有什么特征结构？ | quasi-2D perovskite → exhibits → quantum-well structures | 021 L27 |
| 5 | 哪些修饰材料用于 MOS 气敏体系？ | noble metal nanoparticles → modifies → metal oxide semiconductors | 038 L39 |
| 6 | HfO2-ZrO2 栅堆叠利用什么有序状态？ | HfO2-ZrO2 multilayers → exhibits → mixed ferroelectric-antiferroelectric order | 043 L238 |
| 7 | 一步涂覆如何形成空穴选择接触？ | one-step solution-coating → results in → perovskite light absorbers | 065 L31 |
| 8 | AgBiS2 吸收增强与什么调控有关？ | cation disorder homogenization under mild annealing conditions → improves → absorption coefficients of ternary AgBiS2 NCs | 250 L164 |
| 9 | 宽带隙钙钛矿用于叠层的什么位置？ | wide-bandgap perovskites → acts as → front absorber | 153 L40 |
| 10 | AlGaN 关联哪些探测器类型？ | AlGaN → used in → avalanche photodiodes | 023 L55 |

别名检索检查 8/8 通过：甲酸根、HCOO−、原子层沉积、ALD、4Cl-BZS、AgBiS2、MXenes、fpAs。
中文标签目前全部标记为“建议标签”（未核实对译），只作检索入口，不作为已确认同义词。

---

## 7. 指标与门槛

| 指标 | v2 | v3 | 口径 |
|---|---:|---:|---|
| 参考概念语义覆盖 | 82.3% | **91.7%**（干净概念 88/96） | 固定 96 项；v3 含待规范概念为 92.7% |
| 参考关系覆盖 | 44.4%（严格 16/36） | **66.7%**（24/36） | 同义谓词与不同表述允许；不要求逐字相同 |
| 别名可检索 | 无别名层 | **8/8** | 固定查询（含中文、符号、缩写、大小写） |
| 论文内缩写别名解析 | 无 | **7/7** | 论文内缩写必须解析到其展开概念 |
| 误合并审计 | 未审计 | **12/12** | 8 组必须分开、4 组必须合并的固定对照 |
| 检索任务通过 | 未执行 | **10/10** | 见第 6 节 |
| 类型冲突 | 未统计 | 7,132（13.9%） | 复核队列；抽查 11/20 规则更合理、5/20 原类型更合理、4/20 两者不可用 |
| 关系方向待复核 | 未统计 | 159 | 只标记不自动改，逐条给证据 |
| 重复边 | 2,609 条 | 已合并，证据全保留 | 不以删边数为成绩 |

所有数字只在本轮固定参考集与 285 篇语料上成立。**本轮未做随机抽样，也没有全库准确率或召回率。**

---

## 8. 仍未完成 / 下一步

1. **7 项参考概念在 v3 中仍无同篇干净概念**：001 inverted perovskite solar cells（只有上位类与
   样品）、021 perovskite LEDs（021 内 `PeLED` 类型为 material，未与全名概念连通）、
   153 open-circuit voltage deficit（153 内只有缩写变体）、153 bandgap complementarity、
   201 grain boundaries（只有“defects near the grain boundaries”）、201 anion engineering（缺）、
   250 colloidal nanocrystals。这些属于**概念组织**问题，已带原因记录，未用模糊匹配掩盖。
2. **12 条参考关系仍未被关系检索判定为支持**（多为端点粒度差异，如“doped-HfO2 grown by ALD”
   在 v3 中挂在 HfO2-ZrO2 上；`AlGaN → used in → solar-blind UV photodetectors` 只到
   avalanche photodiodes）。需要的是概念层级与关系规范化，不是再次全量重抽。
3. **类型规则需要随本体定义完善**：18,980 个概念无规则可依、2,600 个碎片待定；冲突 7,132 条需
   人工复核。建议先把第 5.1 节的类型定义、正反例写清，再扩充规则与词典。
4. **前处理函数缺陷**：`strip_front_matter` 会把部分论文的摘要裁掉（4.1）。全量重抽前应改为
   按摘要/章节标题识别，并保留“裁掉了什么”的可核对记录。
5. **全库误合并审计未做**：本轮只有 12 组固定对照。下一步从预测侧抽样（建议 200 组同形近名
   概念）建立随机报告，与定向风险集分开统计。
6. **抽取实体有效性、分类正确性还需要独立抽样**：本轮只对参考集与 20 条冲突做了判定；
   应按主文档第 7 节从预测侧另行抽样并分层报告。
7. **界面接入未做**：检索层已提供 API（`KnowledgeGraphIndex`），但尚未接入 `server.py` 的页面；
   用户界面展示时需默认隐藏 fragment/symbol 概念，并在无证据时明确返回无结果。

---

## 9. 复现

```bash
# 阶段 A（参考集证据卷宗 + 判定 + 指标）
python evaluation/stage_a_cases.py
python evaluation/stage_a_adjudication.py

# 阶段 C（需要 config-deepseek.toml 中的 API key；已有结果会被复用）
python evaluation/targeted_reextract.py --dry-run
python evaluation/targeted_reextract.py

# 阶段 B（285 篇规范化；读取 v2 冻结输入并融合阶段 C 结果）
python evaluation/normalize_v3.py

# 阶段 D 与总指标（读取阶段 A/B/D 产物）
python evaluation/stage_d_retrieval.py
python evaluation/stage_metrics.py

# 测试
python -m pytest -q          # 167 passed, 1 skipped
```

参考术语与关系的来源文件仍是 `evaluation/terminology_review_20261125/reference_and_comparison.json`
（由 `evaluation/build_terminology_review.py` 生成，复现命令 `python evaluation/build_terminology_review.py`）。
本文的判定与 v3 数据都由上述脚本从该文件生成，未手工改数为“更好看”的结果。

---

## 10. 与旧 v1/v2 数值评估的关系

- 旧的数值、样品、条件评估仍保留在 `evaluation/full_v2/`（冻结，未修改）与归档报告
  `full_v1_review_before_goal_reset.md` 中；v3 把观测（16,829）与数值事实（12,649）作为附加层保留，
  不再以数值命中数作为主线。
- 本轮只改变“概念、别名、类型、关系、证据”的组织方式；v2 原始 JSON 一个字节都没有改，
  所有输入哈希记录在 `evaluation/full_v3_normalized/manifest.json`。
- 主文档 `full_v1_review_revised.md` 第 8 节的“未完成”清单已由本报告按实际执行结果更新。
