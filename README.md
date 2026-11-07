<p align="center">
  <img src="assets/stca-logo.png" alt="STCA logo" width="88">
</p>

# STCA Agent Skill

**让智能体直接执行聚合物子结构筛选、从实测数据提取可读规则，并用多性能规则指导候选设计与核验。**

STCA Agent Skill 把 STCA 计算流程封装为可调用工具。宿主智能体负责理解用户目标、组织文件和汇总结果；固定版本的 STCA 代码负责阈值扫描、规则提取、候选筛选与评价。

## 可以做什么

### 1. 用已有 STCA 规则筛选候选

输入聚合物重复单元 SMILES，输出：

- 每个候选是否通过结构规则；
- 缺少的必需子结构与出现的排除子结构；
- 单性能结果和多性能交集；
- 可继续用于排序、计算或实验验证的候选表。

### 2. 从实测数据提取新的可读规则

输入结构、实测性能、单位和数据划分，skill 会执行滑动阈值分析，生成正/负子结构排名、规则家族、冻结代表规则和留出集评价结果。

### 3. 用规则指导候选设计

把冻结规则导出为精确约束，交给宿主智能体提出候选；随后自动进行结构处理、MACCS 计算和逐条规则核验，保留通过与未通过的全部候选及原因。

## 多性能目标会按用户需求自动连接

每个性能目标都保留自己的**性质、方向和档位**，不会把所有目标强行放到同一个刻度，也不会固定成某一组 Tg+EC 组合。

| 用户目标 | 使用的 STCA 规则来源 |
| --- | --- |
| 高 Tg | Tg 热学规则 |
| 高 Tm、高 Td、高 TC | Tg-derived thermal transfer |
| 高 EC / 低 EC | 对应方向的 EC 规则 |
| 高 ε-AC / 低 ε-AC | 对应方向的 EC-derived electrical transfer |

例如，“较高 Tg、极低 EC、高 TC”会分别建立三个目标：Tg 使用自己的热学档位，EC 使用更严格的低电导档位，TC 使用热学迁移规则；三条规则再作用于同一批候选并取交集。

用户可以直接给出百分位档位，也可以使用 `broad / standard / strict / extreme`。绝对数值目标会结合用户数据或论文参考档位进行映射，并在输出中记录该映射，不会把不同物理量当成同一数值尺度。

目标文件示例：

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "ID",
  "smiles_column": "SMILES_hcap",
  "objectives": [
    {"property": "Tg", "direction": "high", "strictness": "standard"},
    {"property": "EC", "direction": "low", "strictness": "extreme"},
    {"property": "TC", "direction": "high", "strictness": "strict"}
  ]
}
```

生成对应的多目标配置：

```bash
python skills/stca/scripts/stca_tools.py plan-objectives \
  --objectives objectives.json \
  --output-dir out/objective-plan
```

然后把生成的 `joint_config.json` 用于同候选多规则筛选。

## 输入与输出

| 输入 | 输出 |
| --- | --- |
| 候选重复单元 SMILES | 逐候选通过状态、失败条件、规则签名和交集结果 |
| 带实测性能的数据表 | 阈值轨迹、正负排名、规则家族、冻结模型和评价指标 |
| 用户的多性能目标 | 自动生成的目标—规则连接方案和联合筛选配置 |
| 冻结规则与生成预算 | 原始候选、H-cap 计算结构、逐规则核验和候选汇总 |

原 STCA 的重复单元输入在计算 MACCS 前采用 H-cap；skill 会保留原始 SMILES，并另建计算列。

## 装在哪里、发挥什么作用

| 平台 | 安装方式 | 在平台中的作用 |
| --- | --- | --- |
| ChatGPT / Codex | 上传 OpenAI plugin ZIP | 让 ChatGPT/Codex 识别 STCA 任务、调用脚本并解释结果 |
| DeepSeek Harness | 解压到 `~/.dsh/skills/stca` | 通过 `/stca` 调用筛选、规则提取和候选核验流程 |
| WorkBuddy | 在“添加技能 → 上传技能”中导入 ZIP | 在桌面任务中读取数据、执行 STCA 并保存结果文件 |
| GitHub / skills.sh | 从公开仓库安装 | 作为跨智能体分发、版本管理和复用入口 |

Mac 上从 GitHub Desktop 上传源码、提交 ChatGPT 插件、安装 DeepSeek/WorkBuddy，以及归档到 Zenodo 的完整步骤见 [PUBLISH_STEPS.zh-CN.md](PUBLISH_STEPS.zh-CN.md)。

## 最短使用示例

> 使用 STCA 筛选这份聚合物 SMILES。目标是高 Tg、低 EC 和高 TC；请根据每个目标分别选择档位，先生成多目标配置，再对同一批候选逐项核验并给出交集。

> 使用 STCA 从我的实测 Td 数据中提取规则，冻结后评价独立留出集，并输出最主要的正向和排除结构条件。

> 使用 STCA 导出低 ε-AC 与高热稳定性的结构约束，提出 20 个候选，保留全部原始提案并逐条说明通过或失败原因。

## 运行要求

实际计算需要 Python、RDKit 和 STCA 代码环境；各平台安装包会引导宿主智能体准备或复用该环境。详细命令见 [运行命令](skills/stca/references/commands.md)，算法与性能连接关系见 [算法说明](skills/stca/references/algorithm.md)。

## 论文、代码与研究主页

- [STCA paper](https://doi.org/10.1038/s41524-026-02345-x)
- [polymer-stca source code](https://github.com/foukusa/polymer-stca)
- [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)
- [ORCID](https://orcid.org/0009-0005-4445-7074)
- [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23)

软件引用信息见 [CITATION.cff](CITATION.cff)。
