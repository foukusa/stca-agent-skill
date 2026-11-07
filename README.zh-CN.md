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

> **GitHub 源码仓库和平台 ZIP 是两类不同文件。** GitHub 的 `main` 分支保存可编辑源码，核心 skill 位于 [`skills/stca/`](skills/stca/)；平台 ZIP 由维护者在本地构建，可作为 GitHub Release 附件或上传到相应平台，但不要求出现在源码树中。

## 目录

- [这个 skill 能做什么](#这个-skill-能做什么)
- [快速开始](#快速开始)
- [标识列与结构列](#标识列与结构列)
- [安装 STCA](#安装-stca)
  - [GitHub 与 skills.sh](#github-与-skillssh)
  - [ChatGPT 与 Codex](#chatgpt-与-codex)
  - [DeepSeek Harness](#deepseek-harness)
  - [WorkBuddy](#workbuddy)
- [如何调用 STCA](#如何调用-stca)
- [功能一：使用冻结规则筛选候选](#功能一使用冻结规则筛选候选)
- [功能二：从实测数据提取规则](#功能二从实测数据提取规则)
- [功能三：规则引导候选设计](#功能三规则引导候选设计)
- [命令行使用](#命令行使用)
- [科学边界](#科学边界)
- [论文、源码与引用](#论文源码与引用)
- [许可](#许可)

## 这个 skill 能做什么

STCA Agent Skill 将原始 Sliding Threshold Correlation Analysis 工作流封装为可调用的聚合物重复单元分析工具。宿主智能体负责理解任务、组织文件、调用脚本和解释结果；固定版本的 `polymer-stca` 实现负责阈值扫描、子结构排序、前缀规则家族构建、冻结筛选与评价。

它明确支持三种功能：

1. **应用已发表的 STCA 规则。** 对重复单元候选进行筛选，输出逐候选通过／未通过状态、缺失的必需 MACCS keys，以及意外出现的排除 keys。
2. **从实测数据提取可读规则。** 执行滑动阈值分析，保留正／负前缀规则家族，冻结代表规则，并评价独立留出集。
3. **用冻结规则指导候选设计。** 导出精确结构约束，由宿主智能体提出候选，再逐条执行明确核验。

对于多性能目标，每种性质保留自己的方向和档位。STCA 不会把 Tg、EC、TC 等性质强行转换到同一个数值尺度，而是分别应用对应规则，再报告同一候选的交集。

## 快速开始

### A. 筛选候选 CSV

候选文件的标识列可以使用**任意列名和任意文本值**：

```csv
CandidateKey,SMILES
sample-A7,*c1ccc(cc1)C(=O)N*
42-blue,*Oc1ccc(cc1)O*
```

标识只用于追踪记录，不会进入模型特征。候选文件也可以完全不提供标识列；筛选适配器会在运行记录中生成 `row-000001` 形式的稳定行号，而不会修改源文件。

可以这样调用：

```text
使用 STCA skill 筛选 candidates.csv，目标是高 Tg 和 Bottom 5% 低电导率。
标识列为 CandidateKey，重复单元结构列为 SMILES。
最终结果保留原始带星号 SMILES，H-cap 只用于 MACCS 计算，
使用冻结的 paper 规则，列出每条失败条件，并将结果保存到 out/screening。
```

### B. 从实测数据提取规则

```text
使用 STCA skill 分析 measured_tg.csv。
RecordKey 只是行标识，SMILES 是重复单元结构，Tg_degC 是实测值。
先审计重复结构和跨集重叠，在源数据上提取完整 STCA 规则家族，
冻结代表规则，再评价独立留出集。
不要把随机行标识当作材料分组键。
```

### C. 提出并核验候选

```text
使用 STCA skill 导出高热稳定性和低 EC 的结构约束。
提出 20 个带两个连接点的重复单元，保留全部原始提案，
只建立临时 H-cap 计算副本，最终通过／失败表仍显示原始带星号结构。
不得把结构规则符合写成实测性能已经确认。
```

## 标识列与结构列

### 标识列

- **不要求使用 `PID`。**
- 候选标识可以是 `CandidateKey`、`Name`、`RecordID` 或用户已有的任意文本列。
- 列名通过 `--id-column` 或 JSON 中的 `id_column` 指定。
- 候选筛选中，如果提供了标识列，其值应非空且唯一。
- 如果不提供标识列，`screen-candidates` 和 `joint-screen` 会根据输入行序生成运行回执 ID。
- 标识值不会作为 MACCS 特征或 STCA 变量使用。

### 行标识不等于划分分组键

随机行 ID 不自动具有科学分组意义。构建防泄漏的 source／holdout 划分时，应使用另一个有明确意义的分组，例如 canonical 重复单元结构、真实材料身份，或其他可辩护的分组变量。不能用随机 ID 声称实现了材料无重叠评价。

### H-cap 与最终结构

原始 STCA 表示在计算 MACCS 前采用 H-cap。因此 skill 执行以下顺序：

```text
原始带 * 的重复单元 SMILES
        ↓ 始终原样保留
临时 H-cap 计算副本
        ↓
MACCS 与冻结 STCA 规则
        ↓
最终结果重新显示原始带 * 的 SMILES
```

skill **不会**尝试从已经 H-cap 的分子中化学逆推出连接点，因为该过程会丢失信息。正确做法是从一开始保留原始输入，并在最终结果中把它作为主结构。完整审计文件仍可以包含 H-cap 计算副本。

## 安装 STCA

### GitHub 与 skills.sh

直接从公开源码仓库安装：

```bash
npx skills add foukusa/stca-agent-skill --skill stca
```

这条命令直接读取仓库中的 `skills/stca/`，**不要求 `main` 分支里存在 ZIP**。

也可以克隆仓库，把 skill 目录复制到其他兼容 Agent Skills 的宿主：

```bash
git clone https://github.com/foukusa/stca-agent-skill.git
cp -R stca-agent-skill/skills/stca /你的/agent/skills/stca
```

### ChatGPT 与 Codex

**普通使用者：** STCA 插件公开后，在 Plugins 目录安装。新建对话，输入 `@STCA`，附上输入文件，并说明目标性质、方向、档位和相关列。

**维护者：** 在本地构建 OpenAI 平台包：

```bash
python3 tools/build_packages.py --output-dir "$HOME/Desktop/STCA-release-0.1.0"
```

上传到 OpenAI 插件发布门户的文件是：

```text
STCA-release-0.1.0/stca-openai-plugin-0.1.0.zip
```

这个 ZIP 是发布产物，不需要提交到 GitHub 源码目录。

### DeepSeek Harness

在 macOS 上直接从源码安装：

```bash
git clone https://github.com/foukusa/stca-agent-skill.git
mkdir -p "$HOME/.dsh/skills"
rm -rf "$HOME/.dsh/skills/stca"
cp -R stca-agent-skill/skills/stca "$HOME/.dsh/skills/stca"
```

在 Harness 中调用：

```text
/stca 使用 paper 的低 EC 5% 规则筛选 candidates.csv。
标识列为 CandidateKey，H-cap 只用于计算，最终返回原始重复单元 SMILES 和每条失败条件。
```

维护者还可以把 `stca-deepseek-harness-0.1.0.zip` 放到 GitHub Release，供希望直接下载的人使用。

### WorkBuddy

**普通使用者：** STCA 上架后从 WorkBuddy 技能市场安装。本地测试时，也可以使用维护者构建的平台 ZIP，在“添加技能 → 上传技能”中导入。

**维护者：** 同一个构建命令会生成：

```text
STCA-release-0.1.0/stca-workbuddy-0.1.0.zip
```

启用后，在任务中明确点名调用：

```text
使用 STCA skill 筛选这份聚合物数据，目标是高 Tg 和低 EC。
标识列为 SampleName。最终输出保留原始 SMILES，并把全部结果文件保存到工作区。
```

## 如何调用 STCA

| 宿主 | 显式调用方式 | 示例 |
| --- | --- | --- |
| ChatGPT / ChatGPT Work | 输入 `@STCA` 并选择插件或 skill | `@STCA 使用低 EC 5% 规则筛选附件候选。` |
| Codex | 选择或提及已经安装的 STCA skill | `使用 $stca 审计并筛选 candidates.csv。` |
| DeepSeek Harness | 输入 `/stca` | `/stca 从 measured_td.csv 提取并冻结规则。` |
| WorkBuddy | 启用 STCA 后，在任务中点名 | `使用 STCA skill 核验这些生成候选。` |
| 其他 Agent Skills 宿主 | 在自然语言请求中明确写 STCA | `使用 STCA，并遵循 H-cap 与冻结规则流程。` |

一个可执行请求最好说明：

- 输入文件；
- 原始重复单元 SMILES 列；
- 可选的标识列；
- 性质和方向，例如高 Tg 或低 EC；
- 档位或严格程度，例如 `0.05`、`strict` 或 `extreme`；
- 使用已发表规则，还是从新数据提取规则；
- 输出目录或报告格式。

## 功能一：使用冻结规则筛选候选

**输入：** 原始重复单元 SMILES，或者已经验证的 167 位 MACCS 矩阵。

**处理步骤：**

1. 保留原始行和原始重复单元 SMILES。
2. 对支持的末端单键 `*` 连接点建立 H-cap 计算副本。
3. 计算 167 位 RDKit MACCS，并保留 K0 占位。
4. 加载指定的 STCA 冻结 profile 和 tier。
5. 检查全部“必须出现”和“必须缺失”条件。
6. 无效结构保留为未知／错误行，不把它当作真实负例。

**主结果：** `results.csv`，显示原始带星号的重复单元 SMILES。

**审计结果：** `rows.csv`，额外记录 H-cap 计算结构和表示信息。

可用的论文 profile：

- `tg-high`：`0.30`、`0.20`、`0.10`；
- `ec-low`：`0.20`、`0.15`、`0.10`、`0.05`；
- `ec-high`：`0.20`、`0.15`、`0.10`、`0.05`。

## 功能二：从实测数据提取规则

**输入：** 结构、实测性能、单位、数据角色，以及可选的行标识／分组列。

**处理步骤：**

1. 审计无效结构、重复测量、表示碰撞和跨集重叠。
2. 在源数据上扫描性能阈值。
3. 计算每个子结构频率轨迹与移动阈值的相关性。
4. 分别排序正向与负向 MACCS keys。
5. 构建原始的纯正、纯负和混合前缀规则家族。
6. 按声明的协议选择并冻结代表规则。
7. 评价没有参与规则选择的数据。

**输出：** 阈值轨迹、排序、完整规则家族、冻结 `model.json`、选择诊断和留出指标。

行标识列可以任意命名，也可以省略。需要分组无重叠划分时，必须另外使用具有科学意义的分组键。

## 功能三：规则引导候选设计

**输入：** 冻结规则、候选数量、连接点格式、允许的化学范围和设计目标。

**处理步骤：**

1. 导出精确结构约束。
2. 由宿主智能体提出指定数量的重复单元候选。
3. 保留每条原始提案和原始带星号 SMILES。
4. 建立临时 H-cap 计算结构。
5. 计算 MACCS 并逐条核验冻结规则。
6. 输出通过／未通过状态和精确失败原因。
7. 多目标时先分别评价，再计算同一候选的交集。

**输出：** 原始提案、完整审计记录、逐规则结果、失败条件和最终交集。结构规则符合不等于实测性能，也不保证可合成性。

## 命令行使用

最简单的单规则候选命令可以直接读取带星号的原始结构，并在 `results.csv` 中保留原结构：

```bash
export SKILL_DIR="$PWD/skills/stca"
export STCA_ENV_DIR="$HOME/.venvs/stca-0.1.0"

python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR" > stca-setup.json

STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"

"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --profile ec-low \
  --protocol paper \
  --tier 0.05 \
  --input candidates.csv \
  --id-column CandidateKey \
  --smiles-column SMILES \
  --output-dir out/ec-low-05
```

输入没有标识列时，删除 `--id-column CandidateKey`；适配器会生成运行回执 ID。原始 `SMILES` 保留在 `results.csv`，H-cap 计算细节保存在 `rows.csv`。

多目标可以使用以下目标文件。标识列是可选的，结构列应指向原始重复单元：

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "CandidateKey",
  "smiles_column": "SMILES",
  "hcap_before_maccs": true,
  "objectives": [
    {"property": "Tg", "direction": "high", "strictness": "standard"},
    {"property": "EC", "direction": "low", "strictness": "extreme"}
  ]
}
```

更多命令和数据合同见 [`skills/stca/references/commands.md`](skills/stca/references/commands.md)。

## 科学边界

- STCA 是透明的筛选和规则提取方法，不是数值物性预测器。
- 候选通过冻结规则只表示**结构规则符合**，不等于实验确认。
- 多性能筛选是分别定义的结构规则的交集；真实联合性能评价需要同一材料、可比条件下的配对标签。
- 保留原始 STCA 的前缀规则家族构建，不替换成任意组合搜索或 beam search。
- `paper` 流程与 `source_locked` 外部评价结果分别报告。
- H-cap 是计算表示步骤；原始重复单元结构始终是最终输出中的权威结构。

## 论文、源码与引用

- **论文：** [Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design](https://doi.org/10.1038/s41524-026-02345-x)
- **原始实现：** [foukusa/polymer-stca](https://github.com/foukusa/polymer-stca)
- **软件引用信息：** [`CITATION.cff`](CITATION.cff)

## 许可

再分发前请阅读 [`LICENSE`](LICENSE)、[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 和 [`PUBLISHER_LICENSE_NOTES.md`](PUBLISHER_LICENSE_NOTES.md)。Agent skill 封装、原始 STCA 实现、logo 和示例数据可能适用不同条款。
