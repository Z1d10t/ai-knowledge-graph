# 材料专业术语知识图谱：最终目标、首批抽取结果与执行方案

更新日期：2026-11-25。本文是当前项目目标与后续实施的主文档；文件名保留以延续原评估文档链接。

> 执行状态（2026-11-25 补充）：第 6 节阶段 A–D 已执行完毕，第 7 节建议工程门槛全部通过，
> 规范化的概念/提及/关系层已写入 `evaluation/full_v3_normalized/`。逐项判定、指标口径、门槛
> 证据与剩余问题见 `evaluation/terminology_review_20261125/COMPLETION_REPORT.md`；本文件第 8 节
> 已按实际完成情况更新。

## 1. 最终目标与范围

**最终目标：从材料领域论文中，优先识别专业名词，建立规范概念、别名、分类及有原文证据的专业关系，形成支持专业检索、概念浏览和论文定位的知识图谱。**

核心链路是“专业术语 → 相关材料/结构/工艺/方法/机理/性能/器件 → 关系 → 证据与论文”。图谱应能让用户从一个专业词出发理解相关知识，不需要先获得一个完整的定量实验数据库。

本轮纠正此前目标偏移：跨论文性能排名、实验条件完整覆盖、全部数值抽取不再是核心验收目标。v2 已有数值、样品、条件、数值类型、转引来源保留为附加信息，不推倒重来，也不继续以提高 PCE 数字命中数驱动全量重抽。

### 1.1 核心任务与附加任务

| 层次 | 需要完成 | 当前优先级 |
|---|---|---|
| 专业术语 | 识别关键材料、材料类别、组分、结构、缺陷、工艺、表征/计算方法、机理、性能、器件与功能层 | 最高 |
| 概念组织 | 规范名、原文名、别名、缩写、类别与上下位关系；避免误合并 | 最高 |
| 专业关系 | 组成、结构、制备、表征、作用、应用，以及有证据的性质影响关系 | 最高 |
| 检索与证据 | 术语搜索、别名搜索、关系浏览、原文定位 | 最高 |
| 实验样品 | 在论文范围内区分具体样品，与概念节点关联 | 辅助，防止误连 |
| 数值观测 | 保留 v2 成果，按需展示数值和条件 | 附加 |
| 跨论文排名 | 需要另行定义可比较子集 | 本轮不实施、不验收 |

### 1.2 项目完成的可检查表现

用户搜索“甲酸根 / formate / HCOO−”应能定位同一概念，并看到相关缺陷、处理作用和出处；搜索“原子层沉积 / ALD”应能找到对应工艺及关联材料；搜索“AgBiS2”应能浏览阳离子无序、吸收系数、相关器件及证据。不同晶相、组分、掺杂和具体样品不能因为名称相近被合成同一个节点。

中文名是检索入口和人工可读标签，英文原词与化学式必须保留。没有核实的中英文对译先记为建议标签，不能当作已经验证的同义词。

## 2. 本轮实际执行范围

已从本地原文独立整理参考术语与关系，再读取相应 v2 enriched 文件进行名称定位。共选择 12 篇：7 篇原始研究、5 篇综述，覆盖钙钛矿、氧化物功率器件、发光、紫外探测、气敏、铁电栅介质、MXene、二维器件和硫化物纳米晶。

**这是跨主题定向试查，不是随机样本。**本轮没有执行前一条建议中的 9+3 或半随机抽样，也没有逐篇通读所有正文、图注和补充材料。每篇限定在下列摘要及正文行段，每篇整理 8 个核心术语和 3 条参考关系，共 **96 项论文内术语记录、36 条参考关系**。术语记录跨论文可能重复，不是 96 个全局唯一概念。

参考术语与关系由 Codex 依据本地论文文本复核，属于 AI 证据参考集，未经过独立人工审定。部分关系采用概念归纳表达，不要求 v2 谓词逐字一致。关系的适用范围仍是对应论文论述，不能自动提升为无条件的领域定律。

### 2.1 对照方法与实际数字

先在同篇 v2 的非 obs 节点端点上检查规范名及已登记别名；名称比较会去除 HTML、统一大小写并移除部分符号，随后用包含关系提出候选。

| 定位结果 | 数量 | 可解释的含义 |
|---|---:|---|
| 名称/别名规范化后匹配 | 49 | 找到标签对应项，不保证概念、类型和关系均正确 |
| 仅找到包含或被包含的候选 | 31 | 需要语义复核，包含父类、复合短语和偶然匹配 |
| 按当前标签规则未定位 | 16 | 漏抽候选；仍可能存在未登记别名或仅出现在证据/字段中 |
| 合计 | 96 | 仅限本轮参考术语 |

**49/96 不是实体准确率；(49+31)/96 不是召回率；16/96 也不是已确认漏抽率。**当前定位只是诊断工具。符号和大小写的简化只用于提出候选，禁止直接用于化学实体合并。方法名可能只出现在 measured by 字段或证据，最终应检查其是否成为可检索概念，而不是只看抽取文本中是否出现。

36 条参考关系已整理证据位置；本轮仅对若干 v2 对应关系做实例检查，没有给出 36 条关系的整体命中率或全库准确率。

## 3. 首批抽取结果与逐篇定位

表中“直接”指名称定位，“候选”指需要复核的变体，“未定位”不等同于确认漏抽。下列类型是本轮目标分类建议，不是对原有类型字段的盲目继承。括号内缩写只在对应论文语境下成立。

### 3.1 001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit.md:53)；检查行段 53–87；文献类型：原始研究。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| 4-chlorobenzenesulfonate | 材料 | 4Cl-BZS；4- chlorobenzenesulfonate | 直接 |
| benzenesulfonate | 材料 | BZS | 直接 |
| undercoordinated Pb2+ | 缺陷 | undercoordinated Pb；Pb2+ defect sites | 候选 |
| density functional theory | 表征/计算方法 | DFT | 未定位 |
| electron transport layer | 功能层/部件 | ETL | 未定位 |
| nonradiative recombination | 机理/过程现象 | non-radiative recombination | 候选 |
| fill factor | 性能/物理量 | FF | 直接 |
| inverted perovskite solar cells | 器件 | pin PSCs | 候选 |

**原文参考关系：**

- `4-chlorobenzenesulfonate → enables → dual-site Pb2+ passivation`。[证据 L87](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit.md:87)
- `undercoordinated Pb2+ ions → results in → nonradiative recombination`。[证据 L77](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit.md:77)
- `nonradiative recombination → limits → fill factor`。[证据 L77](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/001_Chen_2024_Improved-charge-extraction-in-inverted-perovskit.md:77)

**实际候选实例：**

- undercoordinated Pb2+：two neighboring Pb2+ defect sites（defect）；undercoordinated Pb2+ ions（defect）。
- nonradiative recombination：nonradiative recombination at the perovskite/CTL interface（mechanism）；interface nonradiative recombination（mechanism）。

### 3.2 011_Zhang_2022_Ultra-wide-bandgap-semiconductor-Ga2O3-power-dio

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/011_Zhang_2022_Ultra-wide-bandgap-semiconductor-Ga2O3-power-dio.md:25)；检查行段 25–39；文献类型：原始研究。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| Ga2O3 | 材料 | gallium oxide | 直接 |
| NiOx | 材料 | p-NiOx | 直接 |
| GaN | 材料 | gallium nitride | 未定位 |
| SiC | 材料 | silicon carbide | 未定位 |
| heterojunction PN diodes | 器件 | HJ PN diodes；PN hetero-junction | 未定位 |
| conductivity modulation | 机理/过程现象 | — | 候选 |
| specific on-resistance | 性能/物理量 | Ron,sp | 直接 |
| breakdown voltage | 性能/物理量 | BV | 未定位 |

**原文参考关系：**

- `holes injection → induces → conductivity modulation`。[证据 L25](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/011_Zhang_2022_Ultra-wide-bandgap-semiconductor-Ga2O3-power-dio.md:25)
- `Ga2O3 → used in → power electronics`。[证据 L25](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/011_Zhang_2022_Ultra-wide-bandgap-semiconductor-Ga2O3-power-dio.md:25)
- `p-NiOx → combined with → n-Ga2O3`。[证据 L39](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/011_Zhang_2022_Ultra-wide-bandgap-semiconductor-Ga2O3-power-dio.md:39)

**实际候选实例：**

- conductivity modulation：hole injection and conductivity modulation（mechanism）；conductivity modulation effect（mechanism）。

### 3.3 021_Zhang_2021_High-performance-quasi-2D-perovskite-light-emitt

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/021_Zhang_2021_High-performance-quasi-2D-perovskite-light-emitt.md:27)；检查行段 27–55；文献类型：综述。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| quasi-2D perovskites | 材料类别 | quasi-two-dimensional perovskites；quasi2D perovskites | 候选 |
| quantum-well structure | 结构/有序状态 | quantum-well structures | 直接 |
| dielectric confinement | 机理/过程现象 | dielectric-confinement | 直接 |
| quantum confinement | 机理/过程现象 | quantum-confinement | 未定位 |
| exciton binding energy | 性能/物理量 | — | 直接 |
| energy transfer | 机理/过程现象 | — | 直接 |
| photoluminescence quantum yield | 性能/物理量 | PLQY；PLQYs | 直接 |
| perovskite LEDs | 器件 | PeLEDs | 候选 |

**原文参考关系：**

- `quasi-2D perovskites → has structure → quantum-well structures`。[证据 L55](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/021_Zhang_2021_High-performance-quasi-2D-perovskite-light-emitt.md:55)
- `quantum-well structures → induces → quantum-confinement effects`。[证据 L55](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/021_Zhang_2021_High-performance-quasi-2D-perovskite-light-emitt.md:55)
- `quasi-2D perovskites → used in → LEDs`。[证据 L27](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/021_Zhang_2021_High-performance-quasi-2D-perovskite-light-emitt.md:27)

**实际候选实例：**

- quasi-2D perovskites：quasi-2D perovskite（None/material/material_class）；perovskites（None/material_class）。
- perovskite LEDs：3D PeLEDs（device）；PeLEDs based on perovskite nanocrystals（device）。

### 3.4 023_Cai_2021_Progress-on-AlGaN-based-solar-blind-ultraviolet

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/023_Cai_2021_Progress-on-AlGaN-based-solar-blind-ultraviolet.md:27)；检查行段 27–39；文献类型：综述。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| AlGaN | 材料 | AlGaN alloys | 直接 |
| III-nitride | 材料类别 | III-nitride material | 直接 |
| solar-blind ultraviolet photodetectors | 器件 | solar-blind UV PDs | 候选 |
| focal plane arrays | 器件 | FPAs | 直接 |
| metal-semiconductor-metal photodetectors | 器件 | MSM | 未定位 |
| avalanche photodiodes | 器件 | APDs | 候选 |
| epitaxy | 工艺/处理 | — | 候选 |
| p-type doping | 工艺/处理 | — | 候选 |

**原文参考关系：**

- `AlGaN → used in → solar-blind UV photodetectors`。[证据 L27](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/023_Cai_2021_Progress-on-AlGaN-based-solar-blind-ultraviolet.md:27)
- `AlGaN-based focal plane arrays → enables → solar-blind imaging`。[证据 L27](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/023_Cai_2021_Progress-on-AlGaN-based-solar-blind-ultraviolet.md:27)
- `avalanche photodiodes → is a → photodetectors`。[证据 L27](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/023_Cai_2021_Progress-on-AlGaN-based-solar-blind-ultraviolet.md:27)

**实际候选实例：**

- solar-blind ultraviolet photodetectors：development of AlGaN-based solar-blind UV PDs（process）。
- avalanche photodiodes：avalanche photodiodes (APDs)（device）；photodiodes（device）。

### 3.5 038_Ou_2022_Recent-Progress-on-Flexible-Room-Temperature-Gas

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/038_Ou_2022_Recent-Progress-on-Flexible-Room-Temperature-Gas.md:35)；检查行段 35–39；文献类型：综述。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| metal oxide semiconductors | 材料类别 | MOS | 直接 |
| flexible room-temperature gas sensors | 器件 | FRT gas sensors | 直接 |
| noble metal nanoparticles | 材料类别 | — | 直接 |
| organic polymers | 材料类别 | — | 候选 |
| carbon nanotubes | 材料类别 | — | 未定位 |
| graphene derivatives | 材料类别 | — | 直接 |
| transition metal dichalcogenides | 材料类别 | — | 候选 |
| operating temperature | 性能/物理量 | — | 直接 |

**原文参考关系：**

- `metal oxide semiconductors → used in → gas sensors`。[证据 L39](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/038_Ou_2022_Recent-Progress-on-Flexible-Room-Temperature-Gas.md:39)
- `noble metal nanoparticles → modifies → metal oxide semiconductors`。[证据 L39](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/038_Ou_2022_Recent-Progress-on-Flexible-Room-Temperature-Gas.md:39)
- `organic polymers → modifies → metal oxide semiconductors`。[证据 L39](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/038_Ou_2022_Recent-Progress-on-Flexible-Room-Temperature-Gas.md:39)

**实际候选实例：**

- organic polymers：organic polymers modified MOS（material_class）。
- transition metal dichalcogenides：two-dimensional transition metal dichalcogenides materials modified MOS（material_class）。

### 3.6 043_Cheema_2022_Ultrathin-ferroic-HfO2ZrO2-superlattice-gate-sta

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/043_Cheema_2022_Ultrathin-ferroic-HfO2ZrO2-superlattice-gate-sta.md:190)；检查行段 190–194；文献类型：原始研究。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| HfO2 | 材料 | — | 直接 |
| ZrO2 | 材料 | — | 直接 |
| SiO2 | 材料 | — | 直接 |
| HfO2-ZrO2 superlattice | 结构/有序状态 | — | 候选 |
| atomic layer deposition | 工艺/处理 | ALD | 直接 |
| ferroelectric order | 结构/有序状态 | FE；ferroelectric | 候选 |
| antiferroelectric order | 结构/有序状态 | AFE；antiferroelectric | 候选 |
| effective oxide thickness | 性能/物理量 | EOT | 直接 |

**原文参考关系：**

- `HfO2 → used as → high-k dielectric layer`。[证据 L192](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/043_Cheema_2022_Ultrathin-ferroic-HfO2ZrO2-superlattice-gate-sta.md:192)
- `doped-HfO2 → grown by → atomic layer deposition`。[证据 L190](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/043_Cheema_2022_Ultrathin-ferroic-HfO2ZrO2-superlattice-gate-sta.md:190)
- `HfO2-ZrO2 superlattice gate stack → exploits → mixed ferroelectric-antiferroelectric order`。[证据 L194](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/043_Cheema_2022_Ultrathin-ferroic-HfO2ZrO2-superlattice-gate-sta.md:194)

**实际候选实例：**

- HfO2-ZrO2 superlattice：HfO2-ZrO2 superlattices（material/sample）；HfO2-ZrO2（material）。
- ferroelectric order：mixed ferroelectric-antiferroelectric order（property）；ferroelectric orthorhombic phase（structure）。

### 3.7 052_Bhat_2021_Prospects-challenges-and-stability-of-2D-MXenes

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/052_Bhat_2021_Prospects-challenges-and-stability-of-2D-MXenes.md:23)；检查行段 23–31；文献类型：综述。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| MXenes | 材料类别 | MXene | 直接 |
| transition metal carbides | 材料类别 | carbides | 候选 |
| transition metal nitrides | 材料类别 | nitrides | 候选 |
| graphene | 材料 | — | 直接 |
| transition metal dichalcogenides | 材料类别 | TMDCs | 候选 |
| exfoliation | 工艺/处理 | exfoliating | 候选 |
| solid solutions | 结构/有序状态 | solid solution | 直接 |
| Mo2TiC2Tx | 材料 | — | 直接 |

**原文参考关系：**

- `MXenes → is a → 2D materials`。[证据 L23](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/052_Bhat_2021_Prospects-challenges-and-stability-of-2D-MXenes.md:23)
- `transition metal dichalcogenides → prepared by → exfoliation`。[证据 L29](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/052_Bhat_2021_Prospects-challenges-and-stability-of-2D-MXenes.md:29)
- `Mo2TiC2Tx → has structure → ordered transition metal atomic sandwiches`。[证据 L31](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/052_Bhat_2021_Prospects-challenges-and-stability-of-2D-MXenes.md:31)

**实际候选实例：**

- transition metal carbides：carbides and/or nitrides of a transition metal（material_class）；carbides, carbonitrides, and nitrides（material_class）。
- transition metal nitrides：carbides and/or nitrides of a transition metal（material_class）；carbides, carbonitrides, and nitrides（material_class）。

### 3.8 065_Zheng_2023_Co-deposition-of-hole-selective-contact-and-abso

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/065_Zheng_2023_Co-deposition-of-hole-selective-contact-and-abso.md:31)；检查行段 31–31；文献类型：原始研究。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| phosphonic acids | 材料类别 | phosphonic | 候选 |
| carboxylic acids | 材料类别 | carboxylic | 候选 |
| indium tin oxide | 材料 | ITO | 直接 |
| self-assembled monolayer | 结构/有序状态 | SAM | 直接 |
| hole-selective contact | 功能层/部件 | — | 直接 |
| perovskite light absorber | 功能层/部件 | — | 候选 |
| one-step solution-coating | 工艺/处理 | one-step solution-coating procedure | 直接 |
| wettability | 性能/物理量 | — | 未定位 |

**原文参考关系：**

- `phosphonic or carboxylic acids → self-assemble on → indium tin oxide substrate`。[证据 L31](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/065_Zheng_2023_Co-deposition-of-hole-selective-contact-and-abso.md:31)
- `self-assembled monolayer → used as → hole-selective contact`。[证据 L31](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/065_Zheng_2023_Co-deposition-of-hole-selective-contact-and-abso.md:31)
- `one-step solution-coating → forms → perovskite light absorber`。[证据 L31](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/065_Zheng_2023_Co-deposition-of-hole-selective-contact-and-abso.md:31)

**实际候选实例：**

- phosphonic acids：phosphonic or carboxylic acids（material）；carbazole-containing phosphonic acid（material_class）。
- carboxylic acids：phosphonic or carboxylic acids（material）；carboxylic acid（material_class）。

### 3.9 095_Liu_2021_A-wafer-scale-van-der-Waals-dielectric-made-from

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/095_Liu_2021_A-wafer-scale-van-der-Waals-dielectric-made-from.md:62)；检查行段 62–72；文献类型：原始研究。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| Sb2O3 | 材料 | — | 直接 |
| Sb4O6 | 材料 | — | 候选 |
| MoS2 | 材料 | — | 直接 |
| inorganic molecular crystal | 材料类别 | IMC；IMCs | 直接 |
| van der Waals dielectrics | 材料类别 | vdW dielectrics；vdW dielectric | 直接 |
| standard thermal evaporation deposition | 工艺/处理 | STED；standard thermal evaporation | 候选 |
| electron mobility | 性能/物理量 | — | 直接 |
| transfer-curve hysteresis | 性能/物理量 | hysteresis | 候选 |

**原文参考关系：**

- `Sb2O3 dielectric film → fabricated via → standard thermal evaporation deposition`。[证据 L66](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/095_Liu_2021_A-wafer-scale-van-der-Waals-dielectric-made-from.md:66)
- `Sb2O3 powder → consists of → Sb4O6 molecules`。[证据 L72](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/095_Liu_2021_A-wafer-scale-van-der-Waals-dielectric-made-from.md:72)
- `Sb4O6 molecules → bonded via → van der Waals interaction`。[证据 L72](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/095_Liu_2021_A-wafer-scale-van-der-Waals-dielectric-made-from.md:72)

**实际候选实例：**

- Sb4O6：Sb4O6 molecules（material）。
- standard thermal evaporation deposition：standard thermal evaporation deposition (STED)（process）；thermal evaporation deposition（process）。

### 3.10 153_Nie_2023_Recent-Advances-in-Wide-Bandgap-OrganicInorganic

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/153_Nie_2023_Recent-Advances-in-Wide-Bandgap-OrganicInorganic.md:40)；检查行段 40–64；文献类型：综述。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| wide-bandgap perovskites | 材料类别 | WBG perovskites | 直接 |
| tandem solar cells | 器件 | TSCs | 直接 |
| front absorber | 功能层/部件 | — | 未定位 |
| photo-induced phase separation | 机理/过程现象 | — | 候选 |
| open-circuit voltage deficit | 性能/物理量 | VOC deficit；V OC deficit | 直接 |
| thermalization losses | 机理/过程现象 | thermalization loss | 直接 |
| charge transport layers | 功能层/部件 | — | 候选 |
| bandgap complementarity | 机理/过程现象 | — | 候选 |

**原文参考关系：**

- `wide-bandgap perovskites → acts as → front absorber`。[证据 L40](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/153_Nie_2023_Recent-Advances-in-Wide-Bandgap-OrganicInorganic.md:40)
- `front cell with WBG absorber → reduces → thermalization loss`。[证据 L62](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/153_Nie_2023_Recent-Advances-in-Wide-Bandgap-OrganicInorganic.md:62)
- `wide-bandgap perovskite solar cells → has issue → photo-induced phase separation`。[证据 L40](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/153_Nie_2023_Recent-Advances-in-Wide-Bandgap-OrganicInorganic.md:40)

**实际候选实例：**

- photo-induced phase separation：severe photo-induced phase separation（property）。
- charge transport layers：instability of charge transport layers (CTLs)（mechanism）；charge transport（property）。

### 3.11 201_Jeong_2021_Pseudo-halide-anion-engineering-for-α-FAPbI3-per

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/201_Jeong_2021_Pseudo-halide-anion-engineering-for-α-FAPbI3-per.md:21)；检查行段 21–31；文献类型：原始研究。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| alpha-FAPbI3 | 材料 | α-FAPbI3；α-phase of formamidinium lead triiodide | 直接 |
| delta-FAPbI3 | 材料 | δ-phase | 直接 |
| formamidinium lead triiodide | 材料 | FAPbI3 | 直接 |
| formate | 材料 | HCOO−；HCOO- | 直接 |
| anion-vacancy defects | 缺陷 | anion vacancy | 直接 |
| grain boundaries | 结构/有序状态 | grain boundary | 候选 |
| anion engineering | 工艺/处理 | — | 未定位 |
| crystallinity | 性能/物理量 | — | 直接 |

**原文参考关系：**

- `formate → suppresses → anion-vacancy defects`。[证据 L21](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/201_Jeong_2021_Pseudo-halide-anion-engineering-for-α-FAPbI3-per.md:21)
- `formate → improves → crystallinity`。[证据 L21](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/201_Jeong_2021_Pseudo-halide-anion-engineering-for-α-FAPbI3-per.md:21)
- `FAPbI3 films → undergo phase transition → black alpha-phase to yellow delta-phase below 150 C`。[证据 L29](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/201_Jeong_2021_Pseudo-halide-anion-engineering-for-α-FAPbI3-per.md:29)

**实际候选实例：**

- grain boundaries：defects near the grain boundaries（defect）。

### 3.12 250_Wang_2022_Cation-disorder-engineering-yields-AgBiS2-nanocr

原文：[选定段落](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/250_Wang_2022_Cation-disorder-engineering-yields-AgBiS2-nanocr.md:26)；检查行段 26–42；文献类型：原始研究。

| 核心术语 | 建议类型 | 别名/缩写 | v2 定位 |
|---|---|---|---|
| AgBiS2 | 材料 | — | 直接 |
| colloidal nanocrystals | 材料类别 | NCs | 未定位 |
| cation disorder | 结构/有序状态 | — | 候选 |
| cation segregation | 结构/有序状态 | — | 直接 |
| optical transition matrix elements | 性能/物理量 | — | 未定位 |
| absorption coefficient | 性能/物理量 | — | 候选 |
| valence band maximum | 性能/物理量 | VBM | 未定位 |
| conduction band minimum | 性能/物理量 | CBM | 未定位 |

**原文参考关系：**

- `cation disorder engineering → enhances → optical transition matrix elements`。[证据 L26](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/250_Wang_2022_Cation-disorder-engineering-yields-AgBiS2-nanocr.md:26)
- `cation-disorder-engineered AgBiS2 colloidal nanocrystals → enables → extremely thin absorber photovoltaic devices`。[证据 L26](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/250_Wang_2022_Cation-disorder-engineering-yields-AgBiS2-nanocr.md:26)
- `AgBiS2 valence band maximum → derives from → Ag d and S p states`。[证据 L42](C:/Users/admin/Desktop/工作区/06-横向项目/知识库项目/材料论文/全部_285篇/md/250_Wang_2022_Cation-disorder-engineering-yields-AgBiS2-nanocr.md:42)

**实际候选实例：**

- cation disorder：homogeneous cation disorder（property）；cation disorder homogenization under mild annealing conditions（process）。
- absorption coefficient：absorption coefficient enhanced by up to a factor of two after annealing（property）；absorption coefficient 5–10 times greater than any other material currently used in photovoltaic technology（property）。

## 4. 实际发现与修订意见

### 4.1 关系方向存在需要优先修复的错误

250 篇原文第 26、36 行表达：调控阳离子无序可以增强光学跃迁矩阵元，进而改善吸收。v2 实际有：

`absorption coefficients of ternary AgBiS2 NCs → improves → cation disorder homogenization under mild annealing conditions`

这将性质改善与调控过程的方向写反。应回到该边的具体证据确认后，改为过程影响吸收性质的方向，保留原文的限定；不能仅交换端点后批量处理其他 improves 边。

011 篇候选中有 `conductivity modulation effect → originates from → hole injection across the PN HJ-interface`，说明不同谓词也可能正确表达同一事实。关系评估不能只要求与参考三元组逐字相同。

### 4.2 专业名词经常被包在长短语中

实际节点包括：

- `absorption coefficient enhanced by up to a factor of two after annealing`：规范概念应为 absorption coefficient；增强倍数与退火信息放到事实或上下文中。
- `exfoliating the 3D bulk to 2D planer structures`：可整理为 exfoliation 工艺，并保留原文动作和对象。
- `organic polymers modified MOS`：是复合材料描述，不能直接当作 organic polymers 的同义词；应保留复合对象并补充有机聚合物概念及修饰关系。
- `development of AlGaN-based solar-blind UV PDs`：当前标为 process，不等同于 solar-blind ultraviolet photodetectors 器件概念。

治理方式是提取“原文提及 + 规范概念 + 修饰信息”，不能简单截断所有长实体。复合材料、异质结构、器件堆叠本身可能是合法专业对象。

### 4.3 分类与粒度没有稳定分开

同篇 `perovskite solar cells` 出现 device/material_class；`quasi-2D perovskite` 出现 material/material_class/缺类型；`HfO2-ZrO2 superlattices` 出现 material/sample。应先确定概念、结构和实验实例的层次，再统一分类，不采用出现次数最多的类型直接覆盖。

本轮 ferroelectric order、cation disorder 等类型也属于待定边界：应在本体规范中明确归入结构/有序状态，或按统一方案归入物理状态；避免为单篇随意切换。性能与机制不应混用，例如“photo-induced phase separation”更接近过程现象，而不是一个纯数值性能。

### 4.4 别名缺失与复合提及影响检索

`transition metal dichalcogenides (TMDCs)`、`standard thermal evaporation deposition (STED)`、`avalanche photodiodes (APDs)` 已有节点，可拆出括号内别名并统一展示。`Sb4O6 molecules` 可关联到材料 Sb4O6；`quasi-2D perovskite/perovskites` 是单复数候选。

禁止把 FE 直接在全库归并为 ferroelectric order，或把 δ-phase 全局归并为 δ-FAPbI3。本轮别名首先限于对应论文上下文，跨论文晋升为全局别名需要验证。Sb2O3 与 Sb4O6 有组成/分子结构关系，不是同义词；α-FAPbI3 与 δ-FAPbI3 必须分开，并关联到共同的材料概念 FAPbI3。

### 4.5 术语定位缺口值得检查，但不是直接启动重抽的依据

001 篇 DFT、ETL；011 篇 GaN、SiC、breakdown voltage；250 篇 optical transition matrix elements、VBM、CBM 等在当前端点标签规则下未定位。下一步需依次查原始输出、字段、别名和证据，确认是已抽取未建节点、名称变体、预处理丢失，还是模型漏抽。只对最后一类考虑定向补抽。

### 4.6 专业关系已有可复用成果

本轮实际找到以下对应关系，说明不需要推倒重来：

- 001：`4Cl-BZS → enables → dual-site Pb2+ passivation`。
- 021：`quasi-2D perovskite → exhibits → quantum-well structures`。
- 038：`Metal oxide semiconductors → used in → commercial gas sensors`。
- 052：`MXenes → is a → 2D material`。
- 065：`phosphonic or carboxylic acids → self-assemble on → indium tin oxide substrate`。
- 095：`Sb2O3 → deposited by → standard thermal evaporation deposition (STED)`。

这些是实例核查，不是全库关系正确性保证。001 和 052 的候选结果中也出现同名重复三元组，需查看 chunk 和证据后决定是否合并；本轮不据此重新估计重复率。

## 5. 建议采用的图谱结构

### 5.1 专业概念层

核心类型：材料、材料类别、组分/化学物种、结构/晶相、缺陷、工艺/处理、表征/计算方法、机制/过程现象、性能/物理量、器件、功能层/界面。先写清定义、正反例和边界，再与现有 profile 做映射；不是立即增加所有新标签。

每个概念保留 concept_id、规范名、原文名、别名、类型、化学式（适用时）、语言标签、来源。化学式对大小写、计量、价态和相标记敏感。下标格式可规范化，化学意义不得抹除。

### 5.2 论文提及与实验实例层

专业概念允许跨论文聚合；提及保留 paper_id、原文片段和位置；样品/器件实例保留论文范围及原文身份。`control device` 不再是全局概念枢纽，而是论文内实例，并连接到相应器件概念。

### 5.3 关系与证据层

关系应保留两端、谓词、原文证据、论文、位置、否定/推测/适用范围和复核状态。最小证据单位可以是句子，跨句时保存完整支持段落。综述概念关系可以保留，但来源标签标明综述；不能仅因出现引用标记就强行猜测原始研究身份。

建议优先稳定如下关系族，具体规范名与现有受控表对齐：

| 关系族 | 例子 | 主要风险 |
|---|---|---|
| 分类 | MXenes is a 2D material | 类别与实例混淆 |
| 组成 | 材料 composed of 组分 | 分子式与材料名误当同义词 |
| 结构 | 准二维钙钛矿 has structure 量子阱结构 | 结构不等于样品 |
| 制备/处理 | 薄膜 deposited by 热蒸发 | 工艺与材料方向反转 |
| 表征/计算 | 材料 characterized by 方法；性质 calculated by 方法 | 计算不应全部映射为测量 |
| 作用/影响 | formate suppresses 缺陷；工艺 improves 性能 | 因果方向、限定与证据强度 |
| 应用/功能 | 材料 used in 器件；层 used as 接触层 | 不能把应用需要写成依赖 |
| 相变/演化 | 材料 undergoes transition 晶相变化 | 温度等限定不可丢失 |

`depends on` 不是禁用词，但只有原文明示依赖时使用；不要拿它替代更具体关系。`calculated by` 不能一律并入 `measured by`。

## 6. 接下来具体怎么做

### 阶段 A：完成这批参考集的语义对照

1. 对 49 项直接标签匹配逐条检查概念与类型是否一致；对 31 项候选区分同义、上下位、复合提及和误匹配；对 16 项未定位查询 raw 与字段。
2. 为每项添加最终判定：正确概念、正确但未规范、概念粒度不同、分类错误、确认漏抽、待定。保留证据和修订理由。
3. 对 36 条参考关系逐条检索 v2 候选，再判定支持、部分支持、不支持、未找到、无法判断；支持原义相同的不同谓词，不用字符串相等代替语义评估。
4. 特别复核 250 的方向错误、各篇类型冲突和方法名未建节点问题。此阶段结束才计算限定参考集上的概念覆盖与关系覆盖，不外推全量。

### 阶段 B：先修后处理与检索组织

1. 从括号定义识别缩写，生成带论文范围的别名；识别全称与化学式关系，但禁止按小写键直接全局合并。
2. 把 mention 与 concept 分开，保留复合实体及其内部概念；从长属性短语中分离数值、变化、条件。
3. 引入概念类型约束和冲突清单，修正高频错误，不让材料类别和样品实例共享全局身份。
4. 合并确认重复关系的证据列表，保留所有原始记录及 chunk；不以删边数量作为优化成绩。
5. 原始 raw/enriched 冻结保存，规范化结果写到新目录，提供原 ID 到新 ID 的映射。

阶段 B 优先于模型重抽。别名、类型和展示层能解决的问题，不消耗一次新的全量抽取。

### 阶段 C：只补抽被确认缺失的专业知识

提示词主任务改为先列核心专业术语，再建立有证据的专业关系；数值作为可选附加事实。明确区分概念名、实验实例、性能名和性能数值；明确列出工艺及表征/计算方法。

使用阶段 A 的确认漏抽记录定位具体段落，定向补抽并与原输出融合。只有固定评估集显示总体漏抽具有系统性、且后处理无法解决时，才考虑全量重抽。

### 阶段 D：用真实检索任务验收

| 检索任务 | 参考路径 | 应有的证据入口 |
|---|---|---|
| 哪些配体与 Pb 缺陷钝化有关？ | 4Cl-BZS → 双位点 Pb 钝化 | 001 L87 |
| 甲酸根作用于什么缺陷？ | formate → 抑制 → anion-vacancy defects | 201 L21 |
| 哪种材料可用于热蒸发 vdW 介质？ | Sb2O3 → 制备工艺 → 热蒸发 | 095 L66、72 |
| 准二维钙钛矿有什么特征结构？ | quasi-2D perovskites → 量子阱 | 021 L55 |
| 哪些修饰材料用于 MOS 气敏体系？ | 贵金属纳米粒子/有机聚合物 → MOS | 038 L39 |
| HfO2-ZrO2 栅堆叠利用什么有序状态？ | 超晶格栅堆叠 → 混合 FE-AFE order | 043 L194 |
| 一步涂覆如何形成空穴选择接触？ | 酸类自组装 → SAM → hole-selective contact | 065 L31 |
| AgBiS2 吸收增强与什么调控有关？ | 阳离子无序调控 → 跃迁矩阵元/吸收 | 250 L26、36 |
| 宽带隙钙钛矿用于叠层的什么位置？ | WBG perovskites → front absorber | 153 L40 |
| AlGaN 关联哪些探测器类型？ | AlGaN → UV PDs / APDs 等 | 023 L27 |

这些是有来源的测试用例，还不是已经通过的检索测试。验收同时检查别名查询、结果类型、关系方向和原文跳转。用户界面只展示图谱及证据实际支持的答案；无支持时明确无结果，不能凭模型常识补出关系。

## 7. 评估指标与完成门槛

保留 v2 结构指标作为运行健康检查；主要指标切换到概念和关系。不要用一个总分掩盖误合并或关系方向错误。

| 指标 | 怎么计算 | 适用范围 |
|---|---|---|
| 核心概念覆盖 | 语义确认找到的参考概念 / 参考概念数 | 固定选定段落；当前尚未完成语义对照 |
| 抽取实体有效性 | 从预测侧另行抽样，检查是否为边界清楚的专业实体 | 与参考概念覆盖分别报告 |
| 分类正确性 | 可判定的预测概念中类型正确的比例，同时报冲突/待定 | 按类型分层 |
| 别名聚合正确性 | 已提出别名组中语义正确组数 / 可判定组数 | 化学式与缩写单列 |
| 误合并 | 发现的跨相、跨组分、跨样品错误合并及影响记录 | 优先清零本轮已确认问题 |
| 关系支持 | 预测侧抽样中有证据、方向和语义正确的关系比例 | 原文支持与字面匹配分开 |
| 参考关系覆盖 | 正确表达的参考关系 / 参考关系总数 | 不要求谓词逐字相同 |
| 检索任务通过 | 返回正确关系路径且可定位原文的任务数 / 测试任务数 | 固定用例，报告失败原因 |

建议工程门槛：阶段 A 所有参考项都完成判定，待定保留理由；本轮已确认方向错误和误合并全部修复并回查；10 个固定检索用例均给出受证据支持的结果或明确的未通过原因；更改前后使用同一参考集对照，不以新增边数作为成功证据。这是建议验收规则，尚未宣称 v2 已满足。

后续增加一个固定随机样本用于估计普遍质量，定向风险集继续用于找问题；两者分开报告。AI 复核意见保留证据与修订轨迹，同一模型多轮一致不冒充独立专家一致性。

## 8. 本轮交付、复现与剩余工作

### 8.1 第一轮（本文件第 1–3 节，已完成）

- 已完成：目标重置、12 篇限定段落的 96 项术语与 36 条关系参考抽取、96 项标签定位、若干关系实例复核及详细执行方案。
- 参考与逐项标签结果：`evaluation/terminology_review_20261125/reference_and_comparison.json`，保留完整证据行、文件路径、原文 SHA256 和候选标签。
- 复现脚本：`evaluation/build_terminology_review.py`。术语与参考关系是第一轮 AI 阅读后写入的清单；重跑脚本仅重新生成参考文件和机械定位，不代表重新完成 AI 专家审阅。
- 原文行号依赖当前 Markdown 快照；若原文变动，应核对 SHA256 后重新定位。

### 8.2 第二轮（阶段 A–D，2026-11-25 完成）

- 阶段 A：96 项术语与 36 条关系全部完成语义判定（正确概念 36、正确但未规范 43、概念粒度不同 5、
  确认漏抽 12；关系支持 16、部分支持 8、未找到 12），并逐项记录缺失原因（已抽取未建节点 8、
  模型漏抽 2、预处理丢失 2）。文件：`evaluation/terminology_review_20261125/stage_a/`。
- 阶段 B：按第 5 节结构生成规范化 v3 层（51,408 个概念、39,400 条关系、145,260 条提及、920 个论文内实例、
  16,829 条观测、12,649 条数值事实），并落盘别名索引、v2→v3 ID 映射、类型冲突清单与修复记录。
  文件：`evaluation/full_v3_normalized/`（v2 只读，哈希见 manifest）。
- 阶段 C：材料提示词改为“先术语、后关系”，对 12 篇参考论文的 34 个段落做定向补抽（402 条关系，
  340 条证据可核验后融合），未做全量重抽。
- 阶段 D：10 个固定检索用例 10/10 通过，8 个别名检索检查 8/8 通过；每条答案给出关系、论文与原文行号。
- 门槛与遗留：第 7 节门槛全部通过；仍未解决的是 7 项参考概念在 v3 中无同篇干净概念、12 条参考关系
  未被检索判定支持、类型冲突 7,132 条待复核、前处理裁掉部分摘要的缺陷、全库误合并审计与界面接入。
  详见 `evaluation/terminology_review_20261125/COMPLETION_REPORT.md` 第 8 节。

### 8.3 复现命令

```bash
python evaluation/build_terminology_review.py          # 参考术语与机械定位
python evaluation/stage_a_cases.py                     # 阶段 A 证据卷宗
python evaluation/stage_a_adjudication.py              # 阶段 A 判定与参考集指标
python evaluation/targeted_reextract.py                # 阶段 C 定向补抽（需 API key，已有结果复用）
python evaluation/normalize_v3.py                      # 阶段 B 规范化（读取 v2 冻结输入并融合阶段 C 结果）
python evaluation/stage_d_retrieval.py                 # 阶段 D 检索验收
python evaluation/stage_metrics.py                     # 阶段 A/B/D 汇总指标与门槛
python -m pytest -q                                    # 167 passed, 1 skipped
```

后续修改候选匹配或类型规则时必须保留当前结果快照，以免指标口径无记录地变化。

## 9. 与旧 v1/v2 数值评估的关系

旧报告保留为历史质量记录，放在同目录归档文件 `full_v1_review_before_goal_reset.md`，其中数值条件和定量比较方案不再作为当前主线。此前关于证据分母、宽松命中、疑似重复和失败块口径的纠错仍然有效。

v2 的条件覆盖、sample_id、value_type、source_study 说明字段建设进展，不能替代专业术语与关系质量。当前不再以“28 条数值严格命中从 7 到 8”决定下一阶段研发投入。

**当前执行依据：先把材料领域的专业概念识别清楚、组织正确、关系做实、证据可查，再根据真实检索需求补充数值功能。**
