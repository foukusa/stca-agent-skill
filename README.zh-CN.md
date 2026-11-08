<p align="center"><img src="assets/stca-logo.png" alt="STCA logo" width="104"></p>
<h1 align="center">STCA Agent Skill</h1>
<p align="center">可读的聚合物筛选规则、带标签数据规则提取与规则引导候选核验。</p>
<p align="center"><strong>0.1.0</strong> · <a href="README.md">English</a> · 简体中文</p>

## 目录

- [能做什么](#能做什么)
- [快速开始](#快速开始)
- [安装与调用](#安装与调用)
- [已发表规则](#已发表规则)
- [从自己的带标签数据提取规则](#从自己的带标签数据提取规则)
- [数据集案例与目标选择](#数据集案例与目标选择)
- [规则引导候选设计](#规则引导候选设计)
- [数据与输出约定](#数据与输出约定)
- [证据与限制](#证据与限制)
- [论文与作者](#论文与作者)
- [许可](#许可)

## 能做什么

STCA Agent Skill 调用王维浩的固定版本**滑动阈值相关分析**实现。宿主智能体负责组织任务和提出候选；作者程序负责计算阈值—子结构相关性、排序前缀规则家族、冻结判断与评价指标。

| 工作流 | 输入 | 输出 |
|---|---|---|
| **应用已发表规则** | 新重复单元 SMILES 和明确的 profile/tier | 冻结规则判断和每条失败条件 |
| **从带标签数据学习** | 结构、标签目标、单位、方向、百分位与 source/evaluation 角色 | 源内准备、完整规则家族、冻结模型、物理阈值和留出指标 |
| **引导并核验设计** | 冻结约束、候选数量与化学范围 | 全部原始提案、H-cap 审计结构及核验后的原始重复单元 |

论文化学空间划分使用 **2048 位 Morgan radius 2（ECFP4-like）**。可读的 STCA 规则使用另一种表示 **RDKit MACCS167**。对新候选应用论文冻结规则，不重新划分或训练。自定义数据分析与论文复现分别标明。

## 快速开始

候选输入示例：

```csv
CandidateKey,SMILES
sample-A7,*CC*
42-blue,*CCO*
```

调用论文规则任务：

```text
使用 STCA 的冻结 paper 规则筛选 candidates.csv。
目标：Tg high、tier 0.20；EC low、tier 0.10。
CandidateKey 是可选行标识，SMILES 是原始重复单元。
H-cap 仅用于 MACCS 计算，返回原始带星号结构，
列出每条失败条件，结果保存到 out/screening。
```

每个目标分别给出**性质、方向和百分位 tier**。`high/low` 是方向，tier 定义该方向的尾部范围。不默认 5%，也不使用一个全局百分位。标识可选、可任意命名，不是描述符。

## 安装与调用

在兼容 Agent Skills 的宿主中从仓库安装：

```bash
npx skills add foukusa/stca-agent-skill --skill stca
```

也可将完整 `skills/stca` 目录复制到宿主的 skill 目录。保留其中的 `scripts/`、`references/` 和 `assets/`。

| 宿主 | 调用 |
|---|---|
| ChatGPT | 选择已安装 STCA 插件/skill，再用 `@STCA` 加输入与目标 |
| Codex | 选择已安装 skill，或写 `使用 $stca……` |
| DeepSeek Harness | `/stca……`；默认全局目录 `~/.dsh/skills/stca` |
| WorkBuddy | 启用已安装 STCA，在任务中写 `使用 STCA skill……` |

目录安装取决于是否已有公开条目。本地安装要求宿主能够执行脚本，并具备 Python/RDKit 环境。按包内说明准备环境；附上 skill 本身不会自动提供科学计算库。

在仓库根目录准备本地环境：

```bash
export SKILL_DIR="$PWD/skills/stca"
python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$HOME/.venvs/stca-0.1.0" > stca-setup.json
STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"
```

已有准备好的环境直接复用，不覆盖。源码固定提交为 `5951b0ef23d63edc8f7e803aaaffa5e4168288f6`。

## 已发表规则

| Profile | 方向 | 支持档位 |
|---|---|---|
| `tg-high` | 高 Tg | Top 30%、20%、10% |
| `ec-low` | 绝缘／低 EC | Bottom 20%、15%、10%、5% |
| `ec-high` | 导电／高 EC | Top 20%、15%、10%、5% |

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --profile tg-high --protocol paper --tier 0.20 \
  --input candidates.csv --id-column CandidateKey --smiles-column SMILES \
  --output-dir out/tg_top20
```

无行标识时省略 `--id-column`。`results.csv` 返回保留的原始结构；`rows.csv` 另含计算专用 H-cap 结构和错误。无效行保持明确的 error/unknown 状态。

论文迁移示例不是通用物性模型。将 Tg 规则用于 TC、将 EC 规则用于介电常数，需要**明确的迁移请求**；新实测性质通常应建立自己的自定义规则。程序不会把一种性质的 cutoff 当成另一性质的单位。

## 从自己的带标签数据提取规则

完整自有数据任务使用 **`auto_screen.py`**：检查并清理不可用记录，准备 H-cap，在源内决定目标变换和扫描分辨率，选择扫描支持量，冻结规则后评价留出角色。

```text
使用 STCA 自动 custom-data 模式分析 permeability.csv。
目标 Permeability，单位 Barrer，direction high，tiers 0.10、0.15、0.20、0.25、0.30。
自动清理不可用结构和目标，保留原始行及排除原因，使用 ECFP4 化学空间角色。
如果 Role 已有 source/holdout 划分，则保持这些角色。
只用 source 选择变换、value 扫描步长及支持量配置，冻结规则后再外评。
返回全部档位、物理阈值、失败条件和最严格的源内合格档位，不能根据 holdout 表现选设置。
```

```bash
"$STCA_PY" "$SKILL_DIR/scripts/auto_screen.py" \
  --input permeability.csv --smiles-column SMILES --target Permeability \
  --unit Barrer --direction high --tiers 0.10,0.15,0.20,0.25,0.30 \
  --data-kind experimental --output-dir out/permeability_auto
```

- 未提供 `--role-column` 时，自动建立 **2048 位 Morgan radius-2（ECFP4-like）t-SNE 角色**，目标外围 20% 保留为 evaluation，并在 source 内重复该过程建立 inner selection。原结构、H-cap 及可选分组保护可能增加留出比例。它是新数据上的自定义角色，不是重现论文的精确成员。
- 提供 `--role-column Role` 时，保持已有 source/holdout 角色；inner selection 仍在 source 内进行。
- 不可解析 SMILES、不支持的连接点、非有限目标及显式非空 ID 与完整原行均相同的重复导出，自动排除出拟合，并在 `excluded_rows.csv` 保留原因与原行映射。原输入文件不改写。
- 可用 `--quality-column` 配合 `--exclude-quality-value`（多个值可重复提供），或 `--target-min`／`--target-max`，执行事先声明的质量／允许范围过滤。这些是数据合同过滤，不是寻找能提高分数的删样本方案。有效但少见的数值、处理条件差异和重复测量，不按邻居标签静默删除或平均。
- 变换和有界 value 网格由源内决定。严格正、稳健跨度至少两 decade 的目标可取 log10；已是 log 的输入必须声明，避免再次取 log。
- 默认 nested 在 source 内比较预定的最小子集配置，再用全 source 重拟合所选配方。需要固定配方时可使用 `--scan-policy fixed`。
- 请求的所有档位均保留在报告中。合格判断使用选中配方的 source 内部 validation：有效评价、非零覆盖、MCC 为正且 Precision 高于 validation 目标率；推荐最小的合格 fraction。它不是 outer 验证；显式 fixed 配方没有 inner-validation 推荐。

模型保留真实目标、单位、变换，以及模型尺度和物理尺度的数值阈值。自动输出包括 `input_format_audit.json`、`cleaned_input.csv`、`excluded_rows.csv`、`cleaning_audit.json`、`workflow_input.csv`、`split_membership.csv`、`split_audit.json`、`fit/source_settings.json` 和 `tier_recommendations.json`。72 条流程检查排除了无效 SMILES 和缺失目标各一条，保留 70 条可用数据，原输入不变；这验证清理行为，不代表科学泛化。自动模型为 `out/permeability_auto/fit/model.json`，运行清单记录路径。增加 `--candidates candidates.csv` 可按 inner-validation 推荐档位筛选，或用 `--screen-tier` 指定已拟合档位。无合格档时保留诊断，不捏造推荐。冻结模型可用于后续筛选、约束导出和评价。

### 可控拟合与冻结评价

需要手动声明角色与设置时，仍可使用 `custom_fit.py`：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/custom_fit.py" \
  --input permeability.csv --smiles-column SMILES \
  --target Permeability --unit Barrer --direction high --tiers 0.30,0.20,0.15,0.10 \
  --role-column Role --source-value source --evaluation-value holdout \
  --transform auto --scan-policy fixed --min-subset-size 1 \
  --data-kind experimental --output-dir out/permeability_fit
```

这个可控接口默认变换 none、固定最小子集 1；auto 或 nested 设置必须显式指定。它不改变论文冻结规则。

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --model out/permeability_fit/model.json --tier 0.20 \
  --input candidates.csv --smiles-column SMILES --output-dir out/permeability_candidates
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" export-rules \
  --model out/permeability_fit/model.json --tier 0.20 --output-dir out/permeability_constraints
"$STCA_PY" "$SKILL_DIR/scripts/evaluate_custom.py" \
  --model out/permeability_fit/model.json --input independent.csv \
  --target Permeability --property Permeability --unit Barrer \
  --smiles-column SMILES --cutoff-mode fixed_train --output-dir out/independent_evaluation
```

冻结评价复用保存的变换和源数值阈值，不重拟合。性质与输入单位必须匹配合同，`--property` 是保存的真实目标名。`dataset_relative` 是另行声明的分位目标任务，不是相同物理阈值的目标。异常明确保留为错误，不能伪装成零分。

完整合同见[自定义数据指南](skills/stca/references/custom_data.md)和[命令](skills/stca/references/commands.md)。

## 数据集案例与目标选择

试用包含 **13 个性质任务**：实测 CO₂/O₂ 渗透率；RadonPy MD 的 TC、RI、密度、Cp、介电常数；ADEPT MD/DFT 的 TC、密度、孤立单体 HOMO–LUMO 能隙、介电常数、RI、Tg。[数据集指南](examples/open_data/README.zh-CN.md)及[索引](examples/open_data/dataset_registry.csv)提供公开来源、原列名、单位、数量和来源/许可说明。计算标签不是实验确认，公开可访问也不代表可无限制再分发数据。

### 代表性 ECFP4 结果

以下**从存档中挑选的案例用于展示 STCA 优于所列 WRAcc、RF 对照的情形**，不表示在每个数据集上都更优。主研究使用 2048 位 radius-2 Morgan／ECFP4-like 角色；[完整存档表](examples/open_data/archived_case_metrics.csv)与[完整跨来源表](examples/open_data/ecfp4_cross_source_all.csv)保留其他案例，包括弱结果。方法之间应只比较相同数据、角色定义和相同 tier 的任务。

| 存档任务 | 档位 | STCA MCC | WRAcc MCC | RF MCC |
|---|---|---:|---:|---:|
| ADEPT 孤立单体 HOMO–LUMO 能隙 | Top 10% | **0.702837** | 0.467958 | 0.566755 |
| RadonPy 密度 | Top 30% | **0.837995** | 0.807575 | 0.748950 |
| RI，ADEPT → RadonPy | Top 10% | **0.50** | 0.41 | 0.37 |
| RI，ADEPT → RadonPy | Top 20% | **0.60** | 0.54 | 0.44 |

ADEPT gap Top 10% 的存档 outer 共 554 条、正例 22、入选 39、TP 21，Precision 0.5385、富集约 13.56、最小子集 1、扫描步长 0.02 eV。目标是**氢封端孤立单体的 HOMO–LUMO 能隙**，不是体相聚合物带隙。RadonPy 密度 Top 30% 的阈值为 1.205 g/cm³，Precision 0.9468、最小子集 42、步长 0.001 g/cm³。RI 跨来源行在去除重叠后使用 **`dataset_relative`** 定义真实标签，不能写成同一物理数值阈值的迁移。这些是历史对照，不表示本轮重新运行了全部最终研究。

### 本轮自动流程的实算结果

RadonPy 密度原始全量新运行保留 1,077 条输入，生成 862 条 source／215 条 outer，自动选择变换 `none`、步长 0.001 g/cm³、最小子集 44。以下展示其中一个档位：

| 新自动任务 | 档位与阈值 | STCA MCC | WRAcc MCC | RF MCC |
|---|---|---:|---:|---:|
| RadonPy 密度 | Top 15%，1.27979818 g/cm³ | **0.542267** | 0.390058 | 0.430808 |

该档 24 条入选中 19 条为 TP，Precision 0.791667、Recall 19/41 = 0.463415、富集 4.1514。**Top 15% 是展示的实算结果；source 内部推荐仍是 Top 10%。** 不能看过 outer 分数后用展示行替换该推荐。[本轮完整五档表](examples/open_data/current_computed_cases.csv)保留所有请求结果，包括 ADEPT gap 正例不足的运行。新 ECFP4 成员和自动设置与历史研究不同，两组结果属于不同实验。

另一次自动运行直接读取官方原始 Dataset A：**778 行、33 个输入列**。空表头自动取别名并记录于 `input_format_audit.json`，列值保留；随后排除 296 条缺少实测 CO2 目标及 1 条不支持的结构，得到 **481 行（381 source／100 outer）**。源内自动选择 log10、模型尺度步长 0.0005、最小子集 20。Top 15% 阈值为 **2,800 Barrer**、MCC **0.486**；10/15/20/25/30% 的 MCC 分别为 0.450/0.486/0.503/0.526/0.526，见[原始气体自动流程汇总](examples/open_data/gas_auto_contract_summary.csv)。这展示完整输入与准备合同，混杂条件仍保留；它与 251 行历史对照是不同数据版本，未做基线比较。

### CO₂：多种可用目标选择

可取得的 **251 行 ECFP4 快照（201 source／50 outer）**，按存档步长 0.01、最小子集 1，重现 30%／20%／10% 规则；新增 25% 与 15% 是同一快照的扩展。

| Top 档位 | source 阈值（Barrer） | outer 正例 | 入选 | TP | MCC |
|---|---:|---:|---:|---:|---:|
| 30% | 840 | 15 | 18 | 11 | 0.5092 |
| 25% | 1,360 | 14 | 9 | 5 | 0.2875 |
| 20% | 2,901.93 | 9 | 9 | 3 | 0.1870 |
| 15% | 4,100 | 9 | 7 | 2 | 0.1110 |
| 10% | 6,100 | 9 | 7 | 2 | 0.1110 |

15% 规则可以选出候选；它与 10% 恰好在 outer 选中相同七条，目标阈值和 source 入选仍不同。外评正例少，结论置信度有限。新增 15%／25% 是在已见早期结果后的探索性扩展。[案例指南](examples/open_data/README.zh-CN.md)保留其身份和复现条件。

### 选择目标，而不是强制 10%

预先给出 `0.10,0.15,0.20,0.25,0.30` 等范围。自动源内合格检查返回每条规则状态并推荐最小合格 fraction；10% 无合格源规则时，继续检查 15%、20% 和其他请求档位，不中止整个任务，也不保证更宽档位一定成功。全部预定结果均保留。

主目标应按声明的 source／inner-validation 标准在看 holdout 前确定。因 holdout 结果而扩档属于探索，需要新的独立验证。Top 10% → Top 20% 是改变任务；固定绝对应用门槛除非用户明确修改，否则保持不变。

```text
使用 STCA 自动分析我的计算 RI 数据，使用 ECFP4 数据角色。
预先考虑 Top 10%、15%、20%、25%、30%。自动清理不可用记录并给出原因，
只在 source 内选择变换、步长和支持量，推荐最严格的源内合格档位。
外评之前拟合并冻结所有请求档位，报告全部结果、物理阈值和失败，
不根据 holdout 表现选 tier。
```

```bash
"$STCA_PY" "$SKILL_DIR/scripts/auto_screen.py" \
  --input computed_ri.csv --smiles-column SMILES --target RI --unit dimensionless \
  --direction high --tiers 0.10,0.15,0.20,0.25,0.30 --data-kind computed \
  --output-dir out/ri_multiple_tiers
```

可以选择**高 RI**、**高 TC**、**低密度**、**高孤立单体 HOMO–LUMO 能隙**或**高 CO₂ 渗透率**，分别使用对应标签与单位。低密度是新方向，不用存档高密度分数证明效果。训练后可冻结模型反复筛选、导出约束引导提案，或让独立训练的多个模型作用于同一候选表。

```text
从所给有标签数据自动训练高 TC 和低密度模型。
分别预定各性质的 tiers，使用 ECFP4 角色、自动有效性清理，
只在各自 source 内选择变换、扫描步长与支持量。冻结两个模型，
再对同一批候选 SMILES 执行。报告各项判断、每条失败条件和结构交集。
只有存在可比条件下的配对 TC／密度标签，才声明联合实测性能。
```

## 规则引导候选设计

```text
使用冻结的 permeability 模型、tier 0.20，提出 20 个带两个末端连接点的重复单元。
保留每条原始提案，只为 MACCS 建立临时 H-cap 副本，逐条核验 bit 条件，
最终返回原始带星号结构。报告所有失败候选，不把规则通过写成实测性能。
```

宿主 LLM 提出候选；STCA 提供约束与确定性核验。多个冻结规则可作用于同一候选表并取交集。冲突约束保持可见，程序不会删条件来制造非空交集。

## 数据与输出约定

- **标识：** 任意可选行标签；无标签生成回执。ID 不定义化学空间划分，也不进入模型特征。
- **结构：** 保留原连接点，H-cap 仅用于计算，返回精确保留的原始重复单元。相同 capped 图不证明相同聚合物。
- **带标签数据：** 明确目标、单位、方向、tiers、条件、source/evaluation 角色及防止相关记录跨角色所需的分组。
- **可审计的自动清理：** 不可用行与已声明质量/范围过滤自动执行，保存排除理由和原行映射。其他异常观测标记而不静默聚合或按标签排除。
- **评价：** 先冻结。报告实际物理阈值、目标数、混淆计数、指标状态和覆盖率。正例不足限制推断，不禁止提取规则或筛选。

| 输出 | 含义 |
|---|---|
| 冻结模型与完整规则家族 | 带目标和协议来源的可复用结构条件 |
| source 审计及扫描设置 | 源内变换、网格、支持量和未解决的数据标记 |
| 档位 cutoff 表 | 每个百分比及其模型尺度、物理单位阈值 |
| 评价报告 | 计数、指标、无定义/有限支持状态及固定训练阈值 |
| 候选结果和审计行 | 原始重复单元、判断、失败条件、H-cap 证据和碰撞标记 |
| 约束 JSON／prompt | 用于后续 agent 提案的精确 bit 逻辑 |

20 正例支持量是可调诊断启发式。零正例 holdout 无法给出有意义的 recall 估计；无定义状态与有效的 0 分区分。结构筛选继续执行。

## 证据与限制

主案例研究使用 13 个实验/MD/DFT 性质任务与 ECFP4 角色。上面的代表性对照从存档结果挑选，完整表保留弱、负结果及非对称迁移。自动工作流的新运行按各自输入哈希和设置记录，不替换存档分数。

- 原始 STCA 前缀家族与源内选择仍由作者实现计算。
- 源内预处理和嵌套配置属于适配层配方，其设置会记录。
- 跨性质迁移是需要明确意图和验证的假设；同性质跨来源也需条件与重叠审计。
- 没有可比条件下的配对标签，结构交集不能证明联合实测性质。
- 规则符合不证明合成、新颖性、因果或实验性能成功。
- 验证记录指出实际运行环境。具体宿主安装及 macOS/Windows 执行需分别验收。

精确证据边界见[验证说明](skills/stca/references/validation.md)与发行版 `validation/` 记录。

## 论文与作者

- [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x)
- [原始 polymer-stca 实现](https://github.com/foukusa/polymer-stca)
- [ORCID：0009-0005-4445-7074](https://orcid.org/0009-0005-4445-7074)
- [Google Scholar：Weihao Wang](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)
- [ResearchGate：Weihao Wang](https://www.researchgate.net/profile/Weihao-Wang-23)
- [软件引用](CITATION.cff)

## 许可

阅读 [LICENSE](LICENSE) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。封装与原作者实现分别保留各自条款。
