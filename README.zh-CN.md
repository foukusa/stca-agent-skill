<p align="center">
  <img src="assets/stca-logo.png" alt="STCA logo" width="104">
</p>

<h1 align="center">STCA Agent Skill</h1>

<p align="center">
  使用滑动阈值相关分析实现可解释的聚合物筛选、规则提取与规则引导候选核验。
</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong>
</p>

## 目录

- [STCA 能做什么](#stca-能做什么)
- [两种运行模式](#两种运行模式)
- [已发表 profile 与百分位档位](#已发表-profile-与百分位档位)
- [快速开始](#快速开始)
- [输入约定](#输入约定)
- [安装与调用](#安装与调用)
- [功能一：应用已发表规则](#功能一应用已发表规则)
- [功能二：在自己的数据上重新归纳规则](#功能二在自己的数据上重新归纳规则)
- [功能三：规则引导候选设计](#功能三规则引导候选设计)
- [命令行示例](#命令行示例)
- [输出文件](#输出文件)
- [科学边界](#科学边界)
- [论文、源码与作者主页](#论文源码与作者主页)
- [许可](#许可)

## STCA 能做什么

STCA Agent Skill 将原始 Sliding Threshold Correlation Analysis 工作流封装为可调用的聚合物重复单元分析工具。宿主智能体负责理解任务、组织文件、调用脚本和解释结果；固定版本的 `polymer-stca` 实现负责阈值扫描、MACCS 子结构排序、前缀规则家族构建、冻结筛选与评价。

它支持三种功能：

1. **把已发表的 STCA 规则直接应用到新的候选表**，逐条输出通过／未通过状态和失败条件。
2. **在用户自己的实测数据上重新归纳可读规则**，百分位阈值由用户明确指定。
3. **使用冻结规则指导候选设计**，并对每个提案进行显式结构核验。

## 两种运行模式

### 1. 已发表规则模式

直接使用 STCA 论文中已经冻结的结论。这些规则保留了论文中 **基于 ECFP2 的 interpolation／extrapolation 划分**来源。把已发表规则应用到新的候选库时，不需要重新划分候选库，也不会重新训练规则。

适合以下任务：

- 把论文已有的 Tg 或 EC 结构规则应用到新的候选；
- 复用论文某个明确的 profile 和百分位档位；
- 把已发表规则导出为可执行设计约束。

### 2. 自定义数据模式

在新的实测数据集上重新提取 STCA 规则。用户需要明确提供：

- 实测性质和单位；
- 目标方向或 EC regime；
- 一个或多个百分位阈值；
- 需要独立评价时的 source／evaluation 数据角色。

由此得到的是**针对该数据集的新规则**，不是论文中冻结规则的复现。随机行 ID 不会被当作科学划分变量。

## 已发表 profile 与百分位档位

百分位档位是每个已发表筛选任务的明确组成部分，不能用“standard”或“extreme”一类模糊标签替代。

| 已发表 profile | 含义 | 可用档位 |
| --- | --- | --- |
| `tg-high` | 高 Tg 分支 | Top 30%、Top 20%、Top 10% |
| `ec-low` | 低 EC／绝缘 regime | Bottom 20%、Bottom 15%、Bottom 10%、Bottom 5% |
| `ec-high` | 高 EC／导电 regime | Top 20%、Top 15%、Top 10%、Top 5% |

在已发表 profile 中，Tg 只有高性能分支。**high／low 的双向区分主要用于 EC**：`ec-low` 表示绝缘，`ec-high` 表示导电；百分位档位再单独指定。

因此，5% 只是 EC 的一个可选档位，不是默认值。只有用户明确选择 5% 时才使用它。

## 快速开始

### A. 使用已发表规则筛选候选

输入示例：

```csv
CandidateKey,SMILES
sample-A7,*c1ccc(cc1)C(=O)N*
42-blue,*Oc1ccc(cc1)O*
```

百分位分别指定的调用示例：

```text
使用 STCA 的已发表规则模式筛选 candidates.csv。
Tg 使用 Top 20% 规则，EC 使用低电导／绝缘 regime 的 Bottom 10% 规则。
CandidateKey 只是可选行标识，SMILES 是原始重复单元结构。
最终结果保留原始带星号 SMILES，H-cap 只用于 MACCS 计算，
列出每条失败条件，并将结果保存到 out/screening。
```

### B. 在实测数据上重新归纳规则

```text
使用 STCA 的自定义数据模式分析 measured_ec.csv。
SMILES 是重复单元结构，EC_S_cm 是实测电导率。
由用户定义 Bottom 20%、Bottom 15% 和 Bottom 10% 三个低 EC 百分位阈值。
使用 Role 列中已经提供的 source／evaluation 角色，分别冻结规则并报告评价指标。
不要把行标识当作划分变量。
```

### C. 提出并核验候选

```text
使用 STCA 导出已发表的 Tg Top 20% 与低 EC Bottom 10% 结构约束。
提出 20 个带两个连接点的重复单元，保留全部原始提案，
建立 H-cap 计算副本用于 MACCS，最终返回原始带星号结构、通过／失败状态和每条失败条件。
```

## 输入约定

### 标识列

- 不要求使用 `PID`。
- 标识列可以省略，也可以使用 `CandidateKey`、`Name`、`RecordID` 等任意列名。
- 标识只用于记录追踪，不会进入 MACCS 或 STCA。
- 未提供标识列时，适配器会生成 `row-000001` 形式的行回执，不会修改源文件。
- 自定义数据模式中的 source／evaluation 角色必须明确提供；任意标识不会自动定义划分。

### H-cap 与最终结构

原始重复单元 SMILES 从一开始就被保留；H-cap 只是计算副本：

```text
原始带 * 的重复单元 SMILES
        ├── 原样保留用于最终展示
        └── 临时 H-cap 计算副本
                    ↓
                 MACCS
                    ↓
               STCA 规则
                    ↓
最终结果仍显示原始带 * 的 SMILES
```

skill 不会从 H-cap 分子反推连接点。`results.csv` 展示原始重复单元；审计输出可以另外记录临时 H-cap 结构。

## 安装与调用

### GitHub 与 skills.sh

直接从仓库安装：

```bash
npx skills add foukusa/stca-agent-skill --skill stca
```

安装后，在兼容 Agent Skills 的宿主中明确调用：

```text
使用 STCA 的已发表规则模式。对 candidates.csv 应用 Tg Top 20% 和 EC-low Bottom 10% 规则。
```

### ChatGPT 与 Codex

STCA 插件公开后，从插件目录安装。

- **ChatGPT：** 新建对话，输入 `@STCA`，附上输入文件，并说明模式、profile 和百分位档位。
- **Codex：** 选择已经安装的 STCA skill，或明确提及 `$stca`。

示例：

```text
@STCA 对附件候选应用已发表的 Tg Top 20% 规则，并列出每条失败条件。
```

### DeepSeek Harness

克隆仓库并复制 skill 目录：

```bash
git clone https://github.com/foukusa/stca-agent-skill.git
mkdir -p "$HOME/.dsh/skills"
rm -rf "$HOME/.dsh/skills/stca"
cp -R stca-agent-skill/skills/stca "$HOME/.dsh/skills/stca"
```

使用 `/stca` 调用：

```text
/stca 对 candidates.csv 应用已发表的 EC-low Bottom 10% 规则。保留原始重复单元 SMILES，并列出失败条件。
```

### WorkBuddy

从 WorkBuddy 技能市场安装 STCA，在任务中启用并明确点名：

```text
使用 STCA skill 的自定义数据模式，从 measured_tg.csv 的 Top 30%、Top 20% 和 Top 10% 阈值重新提取 Tg 规则。
```

## 功能一：应用已发表规则

**输入：** 原始重复单元 SMILES，或已经验证的 167 位 MACCS 矩阵。

**必须明确选择：**

- 已发表 profile：`tg-high`、`ec-low` 或 `ec-high`；
- 该 profile 支持的明确百分位档位。

**处理步骤：**

1. 保留原始行和原始重复单元 SMILES。
2. 对支持的末端单键 `*` 连接点建立 H-cap 计算副本。
3. 计算 167 位 RDKit MACCS，并保留 K0 占位。
4. 加载所选 profile 与档位的冻结 paper 规则。
5. 检查全部“必须出现”和“必须缺失”条件。
6. 无效结构保留为未知／错误行，不当作真实负例。

这个工作流不会生成新的训练划分。它直接把论文冻结结论应用到用户候选集。

## 功能二：在自己的数据上重新归纳规则

**输入：** 重复单元结构、实测性质、单位、明确百分位阈值，以及需要评价时的 source／evaluation 角色。

**处理步骤：**

1. 审计无效结构、重复测量、表示碰撞和数据角色重叠。
2. 在 source 数据上扫描用户定义的性能阈值。
3. 计算子结构频率轨迹与移动阈值的相关性。
4. 分别排序正向与负向 MACCS keys。
5. 构建原始的纯正、纯负和混合前缀规则家族。
6. 仅使用声明的 source 角色选择并冻结代表规则。
7. 在声明的 evaluation 角色上评价冻结规则。

用户可以根据自己的数据定义有科学意义的百分位阈值。这些规则属于新数据集。除非实际使用论文原始数据角色，否则不能把结果写成论文 ECFP2 划分的复现。

## 功能三：规则引导候选设计

**输入：** 一个或多个冻结规则、明确百分位档位、候选数量、连接点格式和允许化学范围。

**处理步骤：**

1. 导出精确的“必须出现／必须缺失”结构约束。
2. 由宿主智能体提出指定数量的重复单元。
3. 保留全部原始提案和原始带星号 SMILES。
4. 建立临时 H-cap 计算结构。
5. 计算 MACCS 并逐条核验冻结规则。
6. 输出通过／失败状态和精确失败条件。
7. 多目标时先分别评价，再计算同一候选的交集。

结构规则符合不等于实测性能，也不保证可合成性。

## 命令行示例

### 应用一个已发表规则

```bash
export SKILL_DIR="$PWD/skills/stca"
export STCA_ENV_DIR="$HOME/.venvs/stca-0.1.0"

python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR" > stca-setup.json

STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"

"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --profile tg-high \
  --protocol paper \
  --tier 0.20 \
  --input candidates.csv \
  --id-column CandidateKey \
  --smiles-column SMILES \
  --output-dir out/tg-top20
```

输入没有标识列时，删除 `--id-column CandidateKey`。

### 使用明确百分位规划多规则筛选

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "CandidateKey",
  "smiles_column": "SMILES",
  "hcap_before_maccs": true,
  "objectives": [
    {"property": "Tg", "direction": "high", "tier": 0.20},
    {"property": "EC", "direction": "low", "tier": 0.10}
  ]
}
```

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" plan-objectives \
  --objectives objectives.json \
  --output-dir out/objective-plan

"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" joint-screen \
  --input candidates.csv \
  --config out/objective-plan/joint_config.json \
  --output-dir out/joint-screen
```

更多命令见 [`skills/stca/references/commands.md`](skills/stca/references/commands.md)。

## 输出文件

| 文件 | 用途 |
| --- | --- |
| `results.csv` | 面向用户的主结果，显示原始重复单元 SMILES |
| `rows.csv` | 审计表，另含计算专用 H-cap 表示 |
| `summary.json` | profile、百分位档位、规则签名、表示合同和运行元数据 |
| `objective_plan.json` | 多规则任务的性质／profile／档位连接方案 |
| `joint_config.json` | 可执行的同候选多规则配置 |
| 冻结 `model.json` | 已发表或自定义结构规则工件 |

## 科学边界

- STCA 是透明的筛选与规则提取方法，不是数值物性预测器。
- 通过冻结规则只表示**结构规则符合**，不等于实验确认。
- 已发表规则模式保留论文 ECFP2 划分来源，并把冻结结论直接应用到新候选。
- 自定义数据模式允许用户自定义百分位阈值和数据角色；输出是针对新数据集的规则。
- 多性能筛选是分别指定的结构规则在同一候选上的交集。
- 保留原始 STCA 的前缀规则家族构建，不替换成任意组合搜索或 beam search。
- H-cap 是计算表示；原始重复单元始终是最终输出中的权威结构。

## 论文、源码与作者主页

- **论文：** [Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design](https://doi.org/10.1038/s41524-026-02345-x)
- **原始实现：** [foukusa/polymer-stca](https://github.com/foukusa/polymer-stca)
- **ORCID：** [0009-0005-4445-7074](https://orcid.org/0009-0005-4445-7074)
- **Google Scholar：** [Weihao Wang](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)
- **ResearchGate：** [Weihao Wang](https://www.researchgate.net/profile/Weihao-Wang-23)
- **软件引用信息：** [`CITATION.cff`](CITATION.cff)

## 许可

再分发前请阅读 [`LICENSE`](LICENSE)、[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 和 [`PUBLISHER_LICENSE_NOTES.md`](PUBLISHER_LICENSE_NOTES.md)。Agent skill 封装、原始 STCA 实现、logo 和示例数据可能适用不同条款。
