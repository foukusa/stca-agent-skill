# STCA 数据集检测案例

[English](README.md) · [仓库说明](../../README.zh-CN.md) · 版本 **0.1.0**

## 目录

- [选择数据和目标](#选择数据和目标)
- [代表性 ECFP4 对照](#代表性-ecfp4-对照)
- [证据文件](#证据文件)
- [CO2 与15%选项](#co2-与15选项)
- [执行自动自有数据案例](#执行自动自有数据案例)
- [多档位选择与多目标组合](#多档位选择与多目标组合)

## 选择数据和目标

所提供试用包含三类来源、**13 项性质任务**。[索引](dataset_registry.csv)分别记录原始观测行、有限目标值及历史处理后的结构数；这些数量对应所提供快照，而非重新下载后的数据。

| 数据与公开来源 | 性质 | 存储单位 | 可选任务 |
|---|---|---|---|
| [RadonPy PI1070](https://github.com/RadonPy/RadonPy/blob/develop/data/PI1070.csv) | 热导率、折射率、密度、比热、介电常数 | W/(m·K)、无量纲、g/cm³、J/(kg·K)、无量纲 | 高热导、高折射率、高/低密度、高比热、高/低介电常数 |
| [ADEPT / PolyGraphMT 数据](https://github.com/sobinalosious/PolyGraphMT/tree/main/data/raw)与[性质定义](https://github.com/sobinalosious/PolyGraphMT/blob/main/data/README.md) | 热导率、密度、单体 HOMO–LUMO gap、介电常数、折射率、Tg | W/(m·K)、g/cm³、eV、无量纲、无量纲、K | 同性质自训练；多个独立模型在同候选上的交集 |
| [PolymerGasMembraneML Dataset A](https://github.com/jsunn-y/PolymerGasMembraneML/blob/main/datasets/datasetA_imputed_all.csv) | 实测 CO2、O2 渗透率 | Barrer 或明确声明的 log10(Barrer) | 高渗透率；用户定义的低渗透率；不同尾部百分位 |

索引中列出了 13 项任务的固定版本下载链接、源提交和区分大小写的原始目标/结构列名。气体结构列为 `Smiles`，RadonPy 为 `smiles`，ADEPT 为 `SMILES`；显式映射字段。已有角色时，用 `--role-column` 及其声明的角色值保留。

RadonPy/ADEPT 是计算观测，不是新增实验验证。ADEPT 的 `BANDGAP_DFT.csv` 实际为氢封端孤立单体的 HOMO–LUMO gap，不是实测聚合物体相带隙。目标应保留作者定义的方法与条件。

公开可访问不等于任意再分发：RadonPy 声明 BSD-3-Clause；ADEPT/PolyGraphMT 和气体数据的再利用条款需按来源核实。本仓库提供汇总证据与来源链接。气体输入应使用原实测 `CO2`/`O2` 或其原始 log 列；Bayesian/Etree 插补列属于另一类数据。

## 代表性 ECFP4 对照

以下案例**从最终历史研究中选择，用于展示 STCA 超过所列 WRAcc、RF 基线的设置**，不表示每个任务均占优。主流程使用 radius-2、2048 位 Morgan（ECFP4-like）角色；可读 STCA 规则使用仅供计算的 H-cap 结构的 MACCS。比较方法时应保持数据、角色、目标定义与档位相同。

| 历史任务 | 档位 | STCA MCC | WRAcc MCC | RF MCC |
|---|---|---:|---:|---:|
| ADEPT 孤立单体 HOMO–LUMO gap | Top 10% | **0.702837** | 0.467958 | 0.566755 |
| RadonPy 密度 | Top 30% | **0.837995** | 0.807575 | 0.748950 |
| RI，ADEPT → RadonPy | Top 10% | **0.50** | 0.41 | 0.37 |
| RI，ADEPT → RadonPy | Top 20% | **0.60** | 0.54 | 0.44 |

ADEPT gap Top 10% 的 outer 共 554 条、正例 22、入选 39、TP 21，Precision 0.5385、富集约 13.56，最小子集 1、步长 0.02 eV；这仍是孤立单体目标。RadonPy 密度 Top 30% 的阈值为 1.205 g/cm³、Precision 0.9468，最小子集 42、步长 0.001 g/cm³。RI 跨来源案例在去除重叠后使用 **`dataset_relative`** 标签，不是冻结物理数值阈值的迁移证明。这些是历史结果，本次更新不宣称重新运行了全部最终研究。

### 本轮自动流程的实算结果

RadonPy 密度原始全量新运行保留 1,077 条输入，生成 862 条 source／215 条 outer，自动选择变换 `none`、步长 0.001 g/cm³、最小子集 44。以下展示其中一个档位：

| 新自动任务 | 档位与阈值 | STCA MCC | WRAcc MCC | RF MCC |
|---|---|---:|---:|---:|
| RadonPy 密度 | Top 15%，1.27979818 g/cm³ | **0.542267** | 0.390058 | 0.430808 |

该档 24 条入选中 19 条为 TP，Precision 0.791667、Recall 19/41 = 0.463415、富集 4.1514。**Top 15% 是展示的实算结果；source 内部推荐仍是 Top 10%。** 不能看过 outer 分数后用展示行替换该推荐。[本轮完整五档表](current_computed_cases.csv)保留所有请求结果，包括 ADEPT gap 正例不足的运行。新 ECFP4 成员和自动设置与历史研究不同，两组结果属于不同实验。

另一次自动运行直接读取官方原始 Dataset A：**778 行、33 个输入列**。空表头自动取别名并记录于 `input_format_audit.json`，列值保留；随后排除 296 条缺少实测 CO2 目标及 1 条不支持的结构，得到 **481 行（381 source／100 outer）**。源内自动选择 log10、模型尺度步长 0.0005、最小子集 20。Top 15% 阈值为 **2,800 Barrer**、MCC **0.486**；10/15/20/25/30% 的 MCC 分别为 0.450/0.486/0.503/0.526/0.526，见[原始气体自动流程汇总](gas_auto_contract_summary.csv)。这展示完整输入与准备合同，混杂条件仍保留；它与 251 行历史对照是不同数据版本，未做基线比较。

## 证据文件

| 文件 | 范围 |
|---|---|
| [dataset_registry.csv](dataset_registry.csv) | 13 个目标、来源链接、单位及历史数据数量 |
| [ecfp4_selected_comparisons.csv](ecfp4_selected_comparisons.csv) | 展示的代表性胜例及精确 MCC 差值 |
| [archived_case_metrics.csv](archived_case_metrics.csv) | 最终 `three_mode_study` 全部 30/20/10% 结果、物理阈值和支持量；保留弱及负面案例 |
| [ecfp4_cross_source_all.csv](ecfp4_cross_source_all.csv) | 完整历史 ECFP4 跨来源对照，包括方向不同的结果 |
| [current_computed_cases.csv](current_computed_cases.csv) | 新 ECFP4 自动运行的全部请求档位 |
| [current_case_provenance.json](current_case_provenance.json) | 新输入哈希、自动配置、角色及原字段核验 |
| [co2_tier_comparison.csv](co2_tier_comparison.csv) | CO2 五档实算及明确的快照来源；下方主案例使用 251 行 ECFP4 快照 |
| [gas_auto_contract_summary.csv](gas_auto_contract_summary.csv) | 官方原始气体自动准备与五档结果 |
| [co2_integrity_checks.json](co2_integrity_checks.json) | 独立 MACCS 核验、混淆计数、原字段保留与历史对照 |

历史文件的空白指标表示未报告；某些 0 来自常量预测或被捕获的错误，详细表保留原值及解释状态。Tg 在档案中有论文规则迁移记录，但没有最终自训练指标；缺失实验不填造分数。

## CO2 与15%选项

对于可获得的 **251 行 ECFP4 快照（201 source／50 outer）**，原固定步长 0.01、最小子集 1 重现了原 30/20/10% 规则和外评指标。新增 25%、15% 是查看过此前结果后增加的探索性分析。

| Top档位 | source物理阈值(Barrer) | outer正例 | 入选 | TP | MCC |
|---|---:|---:|---:|---:|---:|
| 30% | 840 | 15 | 18 | 11 | 0.5092 |
| 25% | 1,360 | 14 | 9 | 5 | 0.2875 |
| 20% | 2,901.93 | 9 | 9 | 3 | 0.1870 |
| 15% | 4,100 | 9 | 7 | 2 | 0.1110 |
| 10% | 6,100 | 9 | 7 | 2 | 0.1110 |

15% 有非空覆盖。它与 10% 恰好在 outer 选中同 7 条，但目标阈值及 source 入选集合不同。outer 正例较少，泛化证据有限。不能由单个档位不成功推断 CO2 无法筛选。

## 执行自动自有数据案例

从上述公开来源或自己的带标签表开始。例如，将 RadonPy 文件下载为 `PI1070.csv`，保留原始 `smiles`、`refractive_index` 列，明确目标来自计算且无量纲。在仓库根目录按主 README 设置 `STCA_PY`、`SKILL_DIR` 和 `STCA_SOURCE` 后：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/auto_screen.py" \
  --input PI1070.csv --smiles-column smiles --target refractive_index \
  --unit dimensionless --data-kind computed --direction high \
  --tiers 0.10,0.15,0.20,0.25,0.30 --output-dir out/ri_auto
```

自动流程：

1. 排除不可用结构、不支持的 H-cap 连接和非有限目标，在 `excluded_rows.csv`／`cleaning_audit.json` 保留原始字段、行映射及原因。仅显式稳定 ID 相同且**完整原始行相同**的重复导出会去重；重复测量不自动平均或删除。
2. 建立 ECFP4/t-SNE 质心外围角色，目标 outer 比例为 20%。canonical 原结构、H-cap 身份及声明的组不跨角色，因此保护后的 outer 可超过 20%。在 source 内重复该方法建立 inner 角色。这是新数据上的自定义成员，不是论文的精确划分。
3. 只在 source 内选择目标变换与有界扫描分辨率。默认 nested 在 inner train/validation 比较最小子集设置，再冻结选中的配方，之后评价 outer。跨度较大的正目标可取 log10；已取 log 的输入用 `--already-log` 及真实输入单位声明。
4. 报告全部请求档位、物理阈值、规则失败及 inner-validation 合格情况，推荐最严格的请求合格档；无合格档时不捏造推荐。

已有 `source`／`holdout` 角色时使用 `--role-column Role`，其他角色值用 `--source-value`／`--evaluation-value` 声明；`--inner-role-column` 可保留事先定义的源内 `train`／`validation` 角色。可用 `--quality-column Quality --exclude-quality-value unusable`，或声明的 `--target-min`／`--target-max`，执行有依据的数据合同过滤。不能通过搜索更高外评分数来设置过滤条件。有效但少见的数值和条件差异会保留可见，不按邻居标签删除。

准备阶段输出 `input_format_audit.json`、`cleaned_input.csv`、`excluded_rows.csv`、`cleaning_audit.json`、`workflow_input.csv`、`split_membership.csv` 和 `split_audit.json`；选中的源内配置在 `fit/source_settings.json`，档位决定在 `tier_recommendations.json`。另一份 72 条流程检查排除了无效 SMILES 和缺失目标各一条，保留 70 条可用数据，原输入不变。这验证程序行为，不是泛化估计。

冻结模型为 `out/ri_auto/fit/model.json`；`run_manifest.json` 和 `automation_plan.json` 记录路径与设置。将某个已拟合档位用于独立候选：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --model out/ri_auto/fit/model.json --tier 0.15 \
  --input candidates.csv --smiles-column SMILES --output-dir out/ri_candidates15
```

也可在自动命令后增加 `--candidates candidates.csv`，按 inner-validation 推荐档位筛选，或用 `--screen-tier` 显式指定已拟合档位。无合格档时保留诊断，不捏造候选筛选结果。

需要完全可控的配方时，可用 `custom_fit.py` 显式提供角色及数值设置，见[主说明](../../README.zh-CN.md#可控拟合与冻结评价)。`--scan-policy fixed` 是显式替代；fixed／仅 source 重代入不产生独立 inner-validation 推荐。nested 划分不可用时程序报告失败，不静默更换策略。

`candidates.csv` 是用户输入；上方证据 CSV 是汇总结果，不是训练观测。精确复现历史指标需要对应清理后输入哈希、角色、目标尺度及数值设置。重新下载原文件再执行自动流程属于新运行，应保留自己的哈希和结果。自动设置不保证得到同一分数或超过基线。

### 可选：相同准备行上的基线对照

在仓库根目录，用冻结 STCA 模型对应的同一准备行和角色，对照 WRAcc、RF：

```bash
"$STCA_PY" tools/benchmark_cases.py \
  --input out/permeability_auto/fit/prepared_rows.csv \
  --model out/permeability_auto/fit/model.json --dataset my_case \
  --target-column stca_model_target --target-transform none \
  --role-column auto_role --source-role source --outer-role holdout \
  --output-dir out/same_rows_comparison
```

将路径和 `auto_role` 替换为实际准备输入及角色列。`stca_model_target` 已是拟合模型尺度，`--target-transform none` 避免重复变换。对照使用相同请求档位及源内阈值。

## 多档位选择与多目标组合

当应用允许范围时，预先声明 **10%、15%、20%、25%、30%** 等候选。自动合格判断使用选中配方的 **source 内部 validation**：有效评价、非零覆盖、MCC 为正且 Precision 高于 validation 目标率。完整报告各档，并推荐最小合格 fraction；10% 不满足时继续检查 15% 和其他请求档位，不中止整个任务。20 正例支持量是可调诊断，不禁止拟合或筛选。

应在使用 outer 结果前选主目标。因 holdout 结果而扩档属于探索，需要新的独立验证。Top 10% → Top 20% 是改变任务；固定绝对应用要求除非明确修改，否则保持不变。

```text
对我的计算 RI 数据表使用 STCA 自动自有数据模式。
预先考虑 Top 10%、15%、20%、25%、30%，使用 ECFP4 角色，清理不可用数据并保留原因，
只在 source 内选择目标尺度、扫描步长和支持量。
每条规则冻结后再评价 outer，返回全部结果，推荐最严格的 inner-validation 合格档位，
不能根据 outer 表现选择。
```

其他可选任务包括高热导、低密度、高孤立单体 HOMO–LUMO gap、高 CO2 渗透率，各自使用对应标签、方向与单位。**低密度是新任务**，历史高密度分数不能证明它。组合目标时，独立训练并冻结高热导、低密度两个模型，再筛选同一候选表，返回结构交集与每项失败条件。联合实测效果需要可比条件下的配对标签，仅满足两组规则不能证明。
