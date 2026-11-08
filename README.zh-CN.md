<p align="center"><img src="assets/stca-logo.png" alt="STCA logo" width="104"></p>
<h1 align="center">STCA Agent Skill</h1>
<p align="center">选择聚合物结构规则，从自己的数据学习新规则，再转成分子设计 prompt。</p>
<p align="center"><strong>0.1.0</strong> · <a href="README.md">English</a> · 简体中文</p>

## 目录

- [77 条现成规则与 154 份生成 prompt](docs/RULE_LIBRARY.zh-CN.md)
- [选择你的任务](#选择你的任务)
- [安装与调用](#安装与调用)
- [准备输入](#准备输入)
- [1. 选择内置规则筛选候选](#1-选择内置规则筛选候选)
- [2. 从自己的 CSV 学习规则](#2-从自己的-csv-学习规则)
- [3. 获取候选生成 prompt](#3-获取候选生成-prompt)
- [你会得到什么](#你会得到什么)
- [更多示例](#更多示例)
- [论文与作者](#论文与作者)
- [许可](#许可)

## 选择你的任务

STCA（**滑动阈值相关分析**）将聚合物性质数据转成可读的子结构规则。这个 agent skill 让你通过自然语言使用这些规则。

| 我想做什么 | 提供什么 | 让 STCA 做什么 |
|---|---|---|
| 用现有规则筛选 | 候选 CSV 和选定的内置规则 | 返回匹配的重复单元及每条失败条件 |
| 为自己的性质学习规则 | 带标签 CSV、目标、单位、方向与百分比 | 自动提取可复用规则，并导出生成 prompt |
| 按规则设计 | 内置规则或刚学到的规则 | 给出可在当前或其他 LLM 使用的完整 prompt，再核验生成的候选 |

随包提供 **77 条冻结规则、154 份中英文生成 prompt**：论文规则 11 条、13 项公开数据性质任务各 5 档共 65 条，以及 1 条作者提供的单体能隙规则。直接打开[现成规则与 prompt 目录](docs/RULE_LIBRARY.zh-CN.md)，按性质选择并复制。RadonPy 是聚合物分子模拟数据来源，ADEPT 是 MD/DFT 计算数据来源。

全部功能均可通过自然语言调用：选择规则、筛选候选、学习新规则、导出 prompt、生成与核验。agent 自动复用或准备所需后台；STCA 计算使用 CPU，生成使用当前宿主 LLM，无需用户配置 Python、GPU 或自行部署模型。

同一候选文件可组合多个规则，每个性质分别选择方向和百分比。

## 安装与调用

到[本 GitHub 仓库](https://github.com/foukusa/stca-agent-skill)选择 **Code → Download ZIP**，在 Mac Finder 中双击下载的 ZIP。打开解压后的仓库，找到 `skills/stca` 下的[完整 STCA skill](skills/stca)。支持本地 skill 目录的宿主可加载这个完整 `stca` 文件夹。

如果已获得对应平台的 STCA 发行包，使用宿主支持的 skill 导入入口加载。入口要求 ZIP 时，可在 Finder 中对完整 `stca` 文件夹选择“压缩”，得到所需 ZIP。加载后启用 STCA；计算依赖与配套工具由宿主 agent 负责准备。

ChatGPT 中已安装 STCA 时，直接选择调用。个人 skill 的安装方式以账号或工作区提供的入口为准。ChatGPT 插件发行包用于插件发布，拖入普通聊天不等于安装个人 skill。

| 平台 | 开始请求 |
|---|---|
| 已安装 STCA 的 ChatGPT | 选择 STCA，输入“使用 STCA……” |
| Codex | 输入“使用 $stca……” |
| 支持 skill 的 DeepSeek Harness agent 宿主 | 加载 STCA，输入 `/stca ……` |
| WorkBuddy | 导入并启用 STCA skill，输入“使用 STCA skill……” |

导出的文字 prompt 可用于任意 LLM。规则学习和结构核验在已启用 STCA 的宿主中完成。

## 准备输入

筛选时，上传包含原始重复单元 SMILES 的 CSV：

```csv
CandidateKey,SMILES
sample-A7,*CC*
42-blue,*CCO*
```

标识列可省略，也可任意命名、使用任意编号。STCA 保留原始 `*` 连接点；氢封端仅作为临时计算步骤。

学习规则时，上传含结构列和数值性质的 CSV，并告诉 skill：

- 结构列和性质列的名称。
- 性质单位，以及标签来自实验还是计算。
- 希望得到 **high** 还是 **low** 值。
- 百分比或百分比列表，例如 Top 10%、15%、20%。

`high/low` 决定方向，百分比决定目标范围。每个性质独立选择。已有训练/测试划分时，告诉 STCA 需要保留的列名与角色值。

## 1. 选择内置规则筛选候选

先询问当前安装版本实际包含的规则：

```text
列出 STCA 的内置规则集，逐项给出数据集、性质、
high/low 方向和可选百分比，供我选择。
```

选择列表中的规则并上传候选。例如：

```text
使用 STCA 的论文规则筛选我上传的 candidates.csv。
选择高 Tg，Top 20%；低电导率，Bottom 10%。
结构列为 SMILES，CandidateKey 是可选标识。
返回同时满足两个规则的候选、各项判断和每条失败条件。
保留原始带星号 SMILES，将结果作为文件返回。
```

论文规则包括高 Tg 的 Top 30%/20%/10%，低电导率的 Bottom 20%/15%/10%/5%，以及高电导率的 Top 20%/15%/10%/5%。CO2、O2 及 RadonPy 的 5 项、ADEPT 的 6 项性质任务也已随包提供高值 Top 10%/15%/20%/25%/30% 规则。完整选择和中英文 prompt 见[规则目录](docs/RULE_LIBRARY.zh-CN.md)。新目标可用下一流程建立规则。

## 2. 从自己的 CSV 学习规则

上传性质表并发送：

```text
使用 STCA 从我上传的 permeability.csv 学习规则。
结构列为 SMILES，目标列为 CO2Permeability，单位 Barrer。
这些是实验测量值，希望得到 high 值。
探索 Top 10%、15%、20%、25%、30%。
自动准备数据，选择适合的尺度、扫描步长和规则设置。
返回所有请求档位的规则、物理阈值、建议的可用范围、
可复用模型，以及可直接复制的候选生成 prompt。
```

skill 负责自动准备数据、基于 ECFP4 的数据划分，以及根据训练数据选择设置。计算与模型复用由宿主管理。原始数据会保留，排除记录和不可用规则也会说明。学习完成后，完整生成 prompt 会随规则和模型一起返回，无需另行执行导出步骤。

之后筛选时，可以直接引用刚完成的任务：

```text
使用我们刚学到的高 CO2 渗透率 Top 15% 规则，
按 SMILES 列筛选我上传的 new_candidates.csv。
返回原始结构、匹配候选和每条失败条件。
```

百分比由你选择。较窄范围不适合时，STCA 可以继续检查你请求的其他范围。多个性质分别学习模型，例如高热导与低密度，再请求筛选同一候选表的交集。

## 3. 获取候选生成 prompt

可以直接使用现有规则，无需新的训练 CSV：

```text
选择 STCA 的高 Tg Top 20% 规则和低电导率 Bottom 10% 规则。
给我一段可完整复制到其他 LLM 的 prompt，用来生成 20 个聚合物重复单元。
写入实际结构条件、两个末端 * 连接点要求，
以及包含 CandidateKey、SMILES 的 CSV 输出格式。
prompt 既以文字展示，也提供可下载文件。
```

也可以使用刚学到的规则：

```text
把我们刚学到的高 CO2 渗透率 Top 15% 规则转成生成 prompt。
要求生成 20 个具有两个末端 * 连接点的候选重复单元。
写入每项规则条件与输出格式，让我可以直接复制到其他 LLM。
```

将 prompt 粘贴到当前或其他 LLM。生成 CSV 后，带回已启用 STCA 的宿主并请求：

```text
按该生成 prompt 使用的规则，检查我上传的 generated_candidates.csv。
逐条核验候选，保留原始 SMILES，返回匹配结构，
并列出每条通过和未通过的条件。
```

也可用一句请求在当前宿主中完成生成与核验：

```text
使用 STCA 的 gas-co2-high-15 规则生成 20 个不同的聚合物重复单元。
自动准备生成 prompt，并核验全部提案。
返回原始带星号 SMILES、通过的候选和每条失败条件。
```

LLM 提出结构，STCA 核验是否符合规则；agent 完成中间步骤。

## 你会得到什么

- 候选表：原始 SMILES、规则判断和失败条件。
- 可读规则，以及所选百分比对应的性质阈值。
- 从数据学习时产生的可复用模型。
- 可复制或下载的完整生成 prompt。

agent 返回所请求任务的文件，也可在后续请求中继续使用选定规则。

## 更多示例

[更多应用示例](examples/open_data/README.zh-CN.md)提供可用数据集规则，以及气体膜、导热、光学、密度、比热、介电、单体轨道能隙任务；也提供学习自有规则时可用的公开数据来源与字段。

## 论文与作者

**Weihao Wang** — [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x) · [原始实现](https://github.com/foukusa/polymer-stca) · [软件引用](CITATION.cff)

[ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

## 许可

见 [LICENSE](LICENSE) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
