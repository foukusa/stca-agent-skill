<p align="center"><img src="assets/stca-logo.png" alt="STCA logo" width="104"></p>
<h1 align="center">STCA Agent Skill</h1>
<p align="center">从数据总结规则，使用已有规则筛选，或按规则生成新结构。</p>
<p align="center"><strong>0.1.0</strong> · <a href="README.md">English</a> · 简体中文</p>

## 目录

- [开始使用](#开始使用)
- [简单试用](#简单试用)
- [保存规则并继续](#保存规则并继续)
- [安装后的自然语言使用案例](docs/USAGE.zh-CN.md)
- [下载与安装](#下载与安装)
- [现成规则与生成 prompt](#现成规则与生成-prompt)
- [准备数据](#准备数据)
- [论文与作者](#论文与作者)

## 开始使用

安装后输入 **“开始使用 STCA”**，选择以下任务。完整对话范例见[自然语言使用案例](docs/USAGE.zh-CN.md)：

| 选择 | 做什么 | 简短请求 |
|---|---|---|
| **1 · 上传数据总结规则** | 学习规则并返回对应筛选结果 | “从这份数据总结高热导率规则。” |
| **2 · 用已有规则筛选** | 使用内置规则或自己保存的规则 | “用已有规则筛选这份候选表。” |
| **3 · 用已有规则生成** | 选规则后，预览确认 prompt 或直接生成 | “用这条规则直接生成 20 个候选。” |

完整处理 prompt 已内置。AI 助手读取文件、展示相关来源，并补问必要信息。归纳规则时，未指定百分比就直接使用 Top 或 Bottom **10%、20%、30%**；也可指定 0% 与 100% 之间的任意百分比，例如 **15%、25%**。你无需输入规则编号或操作 Python。计算使用 CPU，兼容 Python 3.10 及以上环境，生成使用当前 AI 助手。

## 简单试用

**直接使用已有规则筛选。** 可上传随包的 [5 条候选示例 CSV](examples/quick_start/candidates.csv?raw=true)，也可直接发送：

```text
使用内置含氟候选示例，按 RadonPy 高密度 Top 30% 的 STCA 规则筛选，并给出每条未满足的规则条件。
```

这个示例会返回 3 条结构规则匹配和 2 条未匹配，保留原始带星号 SMILES。

**从开源数据总结规则。** 下载 [GAS Dataset A CSV](https://github.com/jsunn-y/PolymerGasMembraneML/blob/30981d71e1e3f12a057e009cd79f119bc659c7f5/datasets/datasetA_imputed_all.csv)，上传后发送：

```text
从这份实测 CO₂ 渗透率数据总结高值规则，单位 Barrer，考虑 Top 10%、20%、30%。自动调整数据形式与步长，返回各档筛选结果并保存规则。
```

AI 助手会使用原始实测 `CO2` 列，自动准备数据、返回规则及筛选结果，再存入“我的规则”；不会把 Bayesian 或 Etree 插补列当作实测标签。

## 保存规则并继续

上传自己的数据后，STCA 自动清理不可用记录、调整数据形式与扫描设置，并在你的数据范围内比较 **STCA 与 WRAcc**。两种方法分别交付，每档明确主推、备选及推荐理由。推荐采用作者 [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x)提出并在筛选任务评价中验证使用的综合衡量指标 **AS（Average Score）**：`AS = (MCC + Precision + F1) / 3`；两种方法均可评价时，WRAcc 的 CV AS 高出 STCA 超过 0.02 才主推 WRAcc，否则保留 STCA。说“使用推荐结果”即可直接继续，也可明确指定方法。

总结完成后，同时交付**两种方法在每个档位的规则与对应筛选结果**：包含百分比对应的**具体物理数值、≥／≤ 比较符及单位**，以及原始 SMILES、入选判断、每条未满足的规则条件及不可计算记录。即使用 log10 归纳，也返回原始物理尺度的阈值。原上传表始终返回逐档结果；另传独立候选表时，其结果另列。

模型、规则、物理阈值和完整中英文生成 prompt 会自动保存到“我的规则”，显示名称并返回主菜单。选 **2** 或 **3** 就能继续复用。

![STCA 工作流程](assets/workflow.zh-CN.svg)

选择 **3** 后，STCA **先显示可选规则目录**，包括内置规则和已载入的“我的规则”。选定来源、性质与百分比后，再选择生成方式：

- **先预览，确认后生成**：展示完整 prompt，可调整候选数量、结构偏好或输出格式；你回复“确认，开始生成”后，当前 LLM 才生成候选。
- **直接生成**：当前 LLM 立即按选定规则生成候选，并逐条核验。

两种方式都会返回原始提案、带星号 SMILES、通过／未通过判断及每条未满足的规则条件，完成后返回主菜单。请求中已说明“直接生成”时，就直接使用该方式。修改目标或冻结规则条件时，会重新选择并确认对应规则。无需另外配置 LLM API。

随时说 **“返回主菜单”** 或 **“上一级”**。返回会保留已保存的规则。需要换设备或平台时，下载规则包并在新会话上传，即可继续使用。

## 下载与安装

ChatGPT 和 Codex 使用同一份 skill 包，按各自客户端的[安装说明](docs/INSTALL.zh-CN.md)加载即可。

| 平台 | 下载 | 官方说明与调用 |
|---|---|---|
| **ChatGPT＋Codex** | [OpenAI skill ZIP](downloads/stca-openai-skill-0.1.0.zip?raw=true) | [ChatGPT 安装帮助](https://help.openai.com/en/articles/20001066-skills-in-chatgpt/) · [Codex skill 说明](https://learn.chatgpt.com/docs/build-skills)。ChatGPT 选择 STCA；Codex 输入“使用 $stca”。 |
| **DeepSeek Harness** | [DSH 插件 TGZ](downloads/dsh-plugin-stca-0.1.0.tgz?raw=true) · [本地 skill ZIP](downloads/stca-deepseek-harness-0.1.0.zip?raw=true) | [产品入口](https://www.deepseek.com/harness/) · [安装说明](docs/INSTALL.zh-CN.md#deepseek-harness)。输入 `/stca`。 |
| **WorkBuddy** | [WorkBuddy ZIP](downloads/stca-workbuddy-0.1.0.zip?raw=true) | [官方 skill 管理说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。选择 STCA 后直接描述任务。 |

Codex 也可在对话中请求：

```text
使用 $skill-installer 安装 https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

ChatGPT 的创建和导入入口依账号与工作区权限开放。ChatGPT 和 Codex 使用同一份 skill 内容，按各自客户端的安装方式加载即可。

## 现成规则与生成 prompt

[规则与 prompt 目录](docs/RULE_LIBRARY.zh-CN.md)按**数据来源 → 性质 → 百分比**列出选择；“我的规则”保存你自己归纳的结果。开源数据规则覆盖 **12 项任务**，均提供 Top **10%、20%、30%** 及两种方法的主推／备选；也提供作者 STCA 论文中实现的 Tg 与电导率冻结规则。

| 来源 | 可选性质 |
|---|---|
| [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x) | 高 Tg、低电导率、高电导率 |
| [GAS 实测数据](https://github.com/jsunn-y/PolymerGasMembraneML) | CO₂、O₂ 渗透率 |
| [RadonPy 计算数据](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv) | 热导率、折射率、密度、比热、介电常数 |
| [ADEPT 计算数据](https://github.com/sobinalosious/PolyGraphMT/tree/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw) | 热导率、密度、孤立单体 HOMO–LUMO 能隙、介电常数、折射率 |

目录显示每个档位的**方法、主推与备选、具体物理阈值、比较符及单位**。接受推荐就直接使用主推，也可明确指定方法；两套规则分别应用。所选冻结目录没有的百分比，例如开源数据目录之外的 15%、25%，需上传带标签数据学习新规则，不能插值或改用相邻档位。若只想将 prompt 用于其他 LLM，可明确请求“只给完整 prompt，暂不生成”。

Tg 与电导率规则用于作者 STCA 论文中展示的实验性质筛选任务。GAS、RadonPy 和 ADEPT 的 12 项公开数据任务也已使用 STCA 完成规则归纳与筛选验证。选择符合目标的现成规则，或从自己的数据总结；详见[规则目录](docs/RULE_LIBRARY.zh-CN.md#stca-论文规则)、[数据来源](examples/open_data/dataset_registry.csv)和[应用示例](examples/open_data/README.zh-CN.md)。

## 准备数据

筛选候选需要重复单元 SMILES；学习规则还需数值性质列：

```csv
CandidateKey,SMILES
sample-A7,*CC*
42-blue,*CCO*
```

标识列可省略或任意命名。原始 `*` 连接点会保留，氢封端仅用于计算。AI 助手会识别表格，只询问尚不明确的目标、单位、实验或计算来源及高低方向；已有划分可要求保留。

## 论文与作者

**Weihao Wang** — [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x) · [原始实现](https://github.com/foukusa/polymer-stca) · [软件引用](CITATION.cff)

也可打开 [Code Ocean 上的 STCA 简易复现版本](https://doi.org/10.24433/CO.1601774.v1)，查看代码与数据并在线运行示例。

[ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

许可见 [LICENSE](LICENSE) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

<p align="center"><em>化繁为简，拨云见日</em></p>
