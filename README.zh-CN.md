<p align="center">
  <img src="assets/stca-logo.png" alt="STCA logo" width="104">
</p>

<h1 align="center">STCA Agent Skill</h1>

<p align="center">
  用滑动阈值相关分析实现可解释的聚合物筛选、规则提取与规则引导候选设计。
</p>

<p align="center">
  <a href="README.md">English</a> · <strong>简体中文</strong>
</p>

> **GitHub 源码与平台安装包是两类不同文件。** GitHub 仓库保存可编辑源码，核心 skill 位于 [`skills/stca/`](skills/stca/)；平台 ZIP 由维护者构建后作为 GitHub Release 附件发布，不应出现在仓库源码目录中。

<a id="table-of-contents"></a>
## 目录

- [这个 skill 能做什么](#what-this-skill-does)
- [快速开始](#quick-start)
- [安装 STCA](#install-the-skill)
  - [通过 GitHub 与 skills.sh 安装](#from-github-with-skillssh)
  - [ChatGPT 与 Codex](#chatgpt-and-codex)
  - [DeepSeek Harness](#deepseek-harness)
  - [WorkBuddy](#workbuddy)
- [如何调用 STCA](#how-to-invoke-stca)
- [功能一：使用冻结规则筛选候选](#workflow-1)
- [功能二：从实测数据提取规则](#workflow-2)
- [功能三：规则引导候选设计](#workflow-3)
- [输入与输出规范](#input-output)
- [命令行使用](#command-line)
- [科学边界](#scientific-scope)
- [论文、源码与引用](#citation-source)
- [许可](#license)

<a id="what-this-skill-does"></a>
## 这个 skill 能做什么

STCA Agent Skill 将原始 Sliding Threshold Correlation Analysis 工作流封装为可调用的聚合物重复单元分析工具。宿主智能体负责理解任务、组织文件、调用脚本和汇总结果；固定版本的 `polymer-stca` 实现负责阈值扫描、子结构排序、规则家族构建、冻结筛选与评价。

它明确支持三种功能：

1. **应用已发表的 STCA 规则。** 对候选重复单元进行筛选，输出逐候选通过／未通过状态，以及缺失的必需 MACCS 条件和出现的排除条件。
2. **从实测数据提取可读规则。** 执行滑动阈值分析，保留正／负前缀规则家族，冻结代表规则，并评价独立留出集。
3. **用规则指导候选设计。** 导出精确结构约束，由宿主智能体提出候选，再执行 H-cap、指纹计算和逐条冻结规则核验。

对于多性能目标，每种性质保留自己的方向和档位。STCA 不会把 Tg、EC、TC 等性质强行转换为同一个数值尺度，而是分别应用对应规则，再报告同一候选的交集。

<a id="quick-start"></a>
## 快速开始

### A. 筛选候选 CSV

提供 UTF-8 CSV，至少包含：

```csv
ID,SMILES
P001,*c1ccc(cc1)C(=O)N*
P002,*Oc1ccc(cc1)O*
```

然后这样调用：

```text
使用 STCA skill 筛选 candidates.csv，目标是高 Tg 和 Bottom 5% 低电导率。
保留原始 SMILES，在计算 MACCS 前对末端连接点做 H-cap，使用冻结的 paper 规则，
输出逐行通过／未通过结果和失败条件，并将文件保存到 out/screening。
```

### B. 从实测数据提取规则

```text
使用 STCA skill 分析 measured_tg.csv。
列名是 PID、SMILES 和 Tg_degC。先审计重复结构与划分重叠，
在源数据上提取完整 STCA 规则家族并冻结代表规则，
再在独立留出集报告 Precision、Recall、F1、MCC、coverage 和 enrichment factor。
```

### C. 生成并核验候选

```text
使用 STCA skill 导出高热稳定性和低 EC 的结构约束。
提出 20 个带两个连接点的重复单元候选，保留全部原始提案，
对每个候选执行 H-cap 和 MACCS 计算，并逐条核验冻结规则。
不得把结构规则通过表述为实测性能已经达标。
```

<a id="install-the-skill"></a>
## 安装 STCA

<a id="from-github-with-skillssh"></a>
### 通过 GitHub 与 skills.sh 安装

直接从公开源码仓库安装：

```bash
npx skills add foukusa/stca-agent-skill --skill stca
```

这一方式直接读取 `skills/stca/`，**不需要 ZIP 文件**。

也可以克隆仓库，并把 skill 目录复制到任意兼容 Agent Skills 的宿主：

```bash
git clone https://github.com/foukusa/stca-agent-skill.git
cp -R stca-agent-skill/skills/stca /你的/skills/目录/stca
```

<a id="chatgpt-and-codex"></a>
### ChatGPT 与 Codex

**普通使用者：** STCA 插件公开后，在 Plugins 目录安装；新建对话，输入 `@STCA`，附上输入文件，并说明性质、方向和档位。

**维护者：** 在本地构建 OpenAI 平台包：

```bash
python3 tools/build_packages.py --output-dir "$HOME/Desktop/STCA-release-0.1.2"
```

上传到 OpenAI 发布门户的文件是：

```text
STCA-release-0.1.2/stca-openai-plugin-0.1.2.zip
```

该 ZIP 是**发布产物**，不会提交到 GitHub 源码目录。

<a id="deepseek-harness"></a>
### DeepSeek Harness

在 macOS 上直接从源码安装：

```bash
git clone https://github.com/foukusa/stca-agent-skill.git
mkdir -p "$HOME/.dsh/skills"
rm -rf "$HOME/.dsh/skills/stca"
cp -R stca-agent-skill/skills/stca "$HOME/.dsh/skills/stca"
```

启动 Harness 后调用：

```text
/stca 使用 paper 的低 EC 5% 规则筛选 candidates.csv。先 H-cap，再输出每个候选的失败条件。
```

维护者也可以把 `stca-deepseek-harness-0.1.2.zip` 作为 GitHub Release 附件，供使用者直接下载。

<a id="workbuddy"></a>
### WorkBuddy

**普通使用者：** STCA 上架后从 WorkBuddy 技能市场安装；本地测试时，也可以使用维护者提供的平台 ZIP，在“添加技能 → 上传技能”中导入。

**维护者：** 使用同一个构建命令生成：

```text
STCA-release-0.1.2/stca-workbuddy-0.1.2.zip
```

启用技能后，在任务对话中明确调用：

```text
使用 STCA skill 筛选这份聚合物数据，目标是高 Tg 和低 EC。
两个目标分别选择档位，并把逐候选结果和交集保存到工作区。
```

<a id="how-to-invoke-stca"></a>
## 如何调用 STCA

| 宿主 | 显式调用方式 | 示例 |
| --- | --- | --- |
| ChatGPT / ChatGPT Work | 输入 `@STCA` 并选择插件或 skill | `@STCA 筛选附件中的候选，目标为 Bottom 5% EC。` |
| Codex | 选择或提及已安装的 STCA skill | `使用 $stca 审计并筛选 candidates.csv。` |
| DeepSeek Harness | 输入 `/stca` | `/stca 从 measured_td.csv 提取并冻结规则。` |
| WorkBuddy | 启用 STCA 后，在任务中点名调用 | `使用 STCA skill 核验这些生成候选。` |
| 其他 Agent Skills 宿主 | 在自然语言请求中明确写 STCA | `使用 STCA，并遵循 H-cap 和冻结规则流程。` |

一个可执行的请求应尽量说明：

- 输入文件及相关列；
- 性质和方向，例如高 Tg 或低 EC；
- 档位或严格程度，例如 `0.05`、`strict` 或 `extreme`；
- 使用已发表规则，还是从新数据提取规则；
- 输出目录或报告格式。

<a id="workflow-1"></a>
## 功能一：使用冻结规则筛选候选

**输入：** 重复单元 SMILES，或已有的 167 位 MACCS 矩阵。

**处理步骤：**

1. 保留原始结构列。
2. 对末端单键 `*` 连接点进行 H-cap，生成独立计算结构。
3. 计算 167 位 RDKit MACCS，并保留 K0 占位。
4. 加载指定的 STCA 冻结 profile 与 tier。
5. 执行全部“必须出现”和“必须缺失”条件。
6. 无效结构保留为错误行，不将其当作真实负例。

**输出：** 逐候选规则签名、通过／未通过状态和精确失败条件。

可用的论文 profile 包括：

- `tg-high`：`0.30`、`0.20`、`0.10`；
- `ec-low`：`0.20`、`0.15`、`0.10`、`0.05`；
- `ec-high`：`0.20`、`0.15`、`0.10`、`0.05`。

<a id="workflow-2"></a>
## 功能二：从实测数据提取规则

**输入：** 结构、实测性能、单位、ID／分组列和 source／holdout 定义。

**处理步骤：**

1. 审计无效结构、重复测量、表示碰撞和跨集重叠。
2. 在源数据上扫描性能阈值。
3. 计算阈值与子结构出现频率之间的相关性。
4. 分别排序正向和负向 MACCS keys。
5. 构建原始的纯正、纯负和混合前缀规则家族。
6. 按声明的协议选择并冻结代表规则。
7. 评价未参与选择的留出集。

**输出：** 阈值轨迹、排序、完整规则家族、冻结 `model.json`、选择诊断和留出指标。

`paper` 仅用于声明清楚的数据角色和论文流程重建；真正的源内选规则与外部评价使用 `source_locked`。

<a id="workflow-3"></a>
## 功能三：规则引导候选设计

**输入：** 冻结规则、候选数量、连接点格式、允许的化学范围和设计目标。

**处理步骤：**

1. 导出精确结构约束。
2. 由宿主智能体提出指定数量的重复单元候选。
3. 保留每一条原始提案及原始 SMILES。
4. 对候选执行 H-cap 与结构有效性检查。
5. 计算 MACCS 并执行每条冻结规则。
6. 输出通过、未通过及失败原因。
7. 多目标时，先分别评价，再计算同一候选的交集。

**输出：** 原始提案、H-cap 结构、逐规则结果、失败条件和最终交集。

结构规则通过仅表示候选符合冻结结构条件，不等于材料已经通过实验验证，也不保证可合成性、Tg、电导率或击穿性能。

<a id="input-output"></a>
## 输入与输出规范

### 候选筛选 CSV

必需列：

```text
ID,SMILES
```

skill 会新增 `SMILES_hcap` 等计算列，不覆盖原始 SMILES。

### 实测数据 CSV

常见形式：

```text
PID,SMILES,Tg_degC,split
```

或：

```text
PID,SMILES,EC_S_per_m,split
```

测量条件应保留为独立列。温度、频率或测试方法不可比时，不应直接合并而不作说明。

### 主要输出

| 任务 | 主要输出 |
| --- | --- |
| 冻结规则筛选 | 逐行 CSV、失败原因、规则签名、运行清单 |
| 规则提取 | 扫描表、正负排名、规则家族、`model.json`、选择诊断 |
| 留出评价 | TP/FP/TN/FN、Precision、Recall、F1、MCC、coverage、enrichment、cutoff 与单位 |
| 多目标筛选 | objective plan、各目标结果、同候选交集 |
| 候选设计 | 原始提案、H-cap 结构、逐规则核验、通过／拒绝表 |

<a id="command-line"></a>
## 命令行使用

推荐通过智能体调用。需要直接运行时，先创建固定环境：

```bash
export SKILL_DIR="$PWD/skills/stca"
export STCA_ENV_DIR="$HOME/.venvs/stca-0.1.2"

python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR" > stca-setup.json

STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"
```

生成 H-cap 结构：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/prepare_hcap.py" \
  --input candidates.csv \
  --output candidates_hcap.csv \
  --smiles-column SMILES \
  --output-column SMILES_hcap
```

执行论文低 EC 5% 规则：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  screen \
  --profile ec-low \
  --protocol paper \
  --tier 0.05 \
  --input candidates_hcap.csv \
  --smiles-column SMILES_hcap \
  --errors report \
  --output ec_low_05_screened.csv
```

更多命令见 [`skills/stca/references/commands.md`](skills/stca/references/commands.md)。

<a id="scientific-scope"></a>
## 科学边界

- STCA 是透明的筛选和规则提取方法，不是数值物性预测器。
- 候选通过冻结规则表示**结构规则符合**，不等于实验确认。
- 多性能筛选是分别定义的结构规则的交集；真实联合性能评价需要同一材料、可比条件下的配对标签。
- 保留原始 STCA 的前缀规则家族构建，不替换成任意组合搜索或 beam search。
- `paper` 流程与 `source_locked` 外部评价结果分别报告。

<a id="citation-source"></a>
## 论文、源码与引用

- **论文：** [Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design](https://doi.org/10.1038/s41524-026-02345-x)
- **原始实现：** [foukusa/polymer-stca](https://github.com/foukusa/polymer-stca)
- **软件引用信息：** [`CITATION.cff`](CITATION.cff)

<a id="license"></a>
## 许可

再分发前请阅读 [`LICENSE`](LICENSE)、[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 和 [`PUBLISHER_LICENSE_NOTES.md`](PUBLISHER_LICENSE_NOTES.md)。Agent skill 封装、原始 STCA 实现、logo 与示例数据可能适用不同条款。
