<p align="center"><img src="assets/stca-logo.png" alt="STCA logo" width="104"></p>
<h1 align="center">STCA Agent Skill</h1>
<p align="center">从数据总结规则，使用已有规则筛选，或按规则生成新结构</p>
<p align="center"><strong>0.1.0</strong> · <a href="README.md">English</a> · 简体中文</p>
<p align="center"><a href="https://doi.org/10.1038/s41524-026-02345-x">STCA 论文</a> · <a href="https://github.com/foukusa/polymer-stca">Python 程序库</a> · <a href="#下载与安装">安装 skill</a></p>

## 目录

- [开始使用](#开始使用)
- [试用范例](#试用范例)
- [保存规则并继续](#保存规则并继续)
- [安装后的自然语言使用案例](docs/USAGE.zh-CN.md)
- [下载与安装](#下载与安装)
- [DeepSeek Harness 专用说明](README.DSH.zh-CN.md)
- [现成规则与生成 prompt](#现成规则与生成-prompt)
- [准备数据](#准备数据)
- [数据划分与评价](#数据划分与评价)
- [论文与作者](#论文与作者)

## 开始使用

STCA 面向聚合物结构与性质数据。安装后输入 **“开始使用 STCA”**，或直接说明要完成的任务。完整对话范例见[自然语言使用案例](docs/USAGE.zh-CN.md)：

| 任务 | 做什么 | 简短请求 |
|---|---|---|
| **上传数据总结规则** | 学习规则并返回对应筛选结果 | “从这份数据总结高热导率规则。” |
| **用已有规则筛选** | 使用内置规则或自己保存的规则 | “用已有规则筛选这份候选表。” |
| **用已有规则生成** | 选规则后，预览确认 prompt 或直接生成 | “用这条规则直接生成 20 个候选。” |

STCA 是由当前 AI 助手在对话中使用的 skill，处理流程已内置。直接说明需求，按需上传数据，再用自然语言继续；AI 助手会读取文件、展示相关规则，并补问必要信息。归纳规则时，未指定百分比就直接使用 Top 或 Bottom **10%、20%、30%**；也可指定 0% 与 100% 之间的任意百分比，例如 **15%、25%**。你无需输入规则编号或操作 Python。计算使用 CPU，兼容 Python 3.10 及以上环境，生成使用当前 AI 助手。

开始学习前，AI 助手会说明本次使用的**结构列、性质列、单位及高低方向**。已知数据集按内置配置匹配；自己的表格可直接指定列名。若多个列都可能是目标，例如实测密度、计算密度或不同温度下的密度，会先请你选择，再开始学习。详见[准备数据](#准备数据)。

## 试用范例

下载 [ADEPT `BANDGAP_DFT.csv`](https://github.com/sobinalosious/PolyGraphMT/blob/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw/BANDGAP_DFT.csv)，上传到对话。文件有 **2,916 条记录、两列**，目标是**氢封端孤立单体的 DFT HOMO–LUMO 能隙**，单位 eV。

| 用途 | 列名 | 表格位置 |
|---|---|---|
| 重复单元结构 | `SMILES` | A · 第 1 列 |
| 孤立单体能隙 | `BANDGAP` | B · 第 2 列 |

第1行是表头，第 **2–2917行**是数据；全部数据行作为输入，无需标识列。

**使用已有 STCA 规则筛选：**

```text
使用已有的 ADEPT 高孤立单体 HOMO–LUMO 能隙 Top 30% STCA 规则筛选这份文件。
```

冻结目标为**能隙 ≥ 11.914537535 eV**。这份文件应返回 **976条匹配、1,940条未匹配、0条未知**。在584条独立 Morgan 距离留出记录上，该 STCA 规则的**精确率为0.7500、召回率为0.7784、F1为0.7639、马修斯相关系数为0.6517**。原表匹配数量与独立评价分别返回。

**重新总结规则、筛选并保存：**

```text
从这份 ADEPT 文件总结高孤立单体 HOMO–LUMO 能隙 Top 30% 规则。结构列为 SMILES，性质列为 BANDGAP，单位 eV。使用全部数据行，返回两种方法、外推评价和筛选结果，并保存规则。
```

AI助手在训练部分学习 STCA 与 WRAcc，分别交付结果。接着说**“重新载入刚保存的 Top 30% STCA 规则，再筛选同一份文件。”**，每行判断应与之前一致。

**按选定规则生成：**

```text
使用刚保存的 Top 30% STCA 规则，直接生成5个聚合物重复单元并核验。
```

想先调整，可说**“生成前先给我看完整 prompt。”**，修改后回复**“确认，开始生成。”**。当前LLM实际生成候选，STCA逐条核验精确结构条件。详见[完整 ADEPT 范例](examples/adept_gap/README.zh-CN.md)和[生成提案](examples/adept_gap/generated_examples.csv)。

## 保存规则并继续

学习会分别返回STCA与WRAcc，并给出每档推荐。推荐依据训练侧验证，沿用作者[STCA论文](https://doi.org/10.1038/s41524-026-02345-x)定义的**马修斯相关系数、精确率与F1分数的平均值**。说“使用推荐规则”即可继续，也可明确选择方法。[数据划分与评价](#数据划分与评价)。

WRAcc 默认在训练数据内自动选择条件数上限。也可以直接说 **“WRAcc 最多使用 10 条条件”** 或 **“不限制 WRAcc 条件数”**。

总结完成后，同时交付**两种方法在每个档位的结果与规则可用状态**：包含百分比对应的**具体物理数值、≥／≤ 比较符及单位**，以及原始 SMILES、入选判断、每条未满足的规则条件及不可计算记录。即使用 log10 归纳，也返回原始物理尺度的阈值。原上传表始终返回逐档结果；另传独立候选表时，其结果另列。

AI 助手将可用模型、规则、物理阈值和完整中英文生成 prompt 保存为文件，并报告文件名与位置。接着说 **“用刚才保存的规则筛选这份表”**，或 **“用刚才的能隙规则生成20个重复单元”**，即可继续。需要在新会话或其他平台复用时，下载并携带规则包；本地文件能否长期保留取决于当前工作区。

![STCA 工作流程](assets/workflow.zh-CN.svg)

提出“用已有规则生成”时，STCA **先显示可选规则目录**，包括内置规则和本次对话已载入的规则包。选定来源、性质与百分比后，再选择生成方式：

- **先预览，确认后生成**：展示完整 prompt，可调整候选数量、结构偏好或输出格式；你回复“确认，开始生成”后，当前 LLM 才生成候选。
- **直接生成**：当前 LLM 立即按选定规则生成候选，并逐条核验。

两种方式都会返回原始提案和聚合物 SMILES，再给出实际计算的规则核验与未满足条件。无法执行计算时，会明确标为待核验。请求中已说明“直接生成”时，就直接使用该方式。修改目标或冻结规则条件时，会重新选择并确认对应规则。无需另外配置 LLM API。

可以直接提出下一项任务，或说 **“接下来可以做什么？”**，让 AI 助手说明可继续的操作。换设备或平台时，在新对话中上传已保存的规则包即可复用。

## 下载与安装

按所用平台安装。下方分别列出步骤，[安装说明](docs/INSTALL.zh-CN.md)还提供环境处理方式与其他安装路径。

| 平台 | 安装方式 | 调用 |
|---|---|---|
| **Codex** | 安装 GitHub 中的 skill 目录，或使用 [Codex ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-codex-0.1.0.zip)。 | `使用 $stca` |
| **DeepSeek Harness** | 在“添加插件”中填写下方 GitHub 安装地址；无需先发布 npm。 | `/stca` |
| **WorkBuddy** | 导入 [WorkBuddy ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.5.zip)。 | “开始使用 STCA” |
| **ChatGPT** | 在支持 skill 安装的客户端中导入 [OpenAI skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-openai-skill-0.1.0.zip)。 | 选择 STCA 或要求使用 STCA。 |

### Codex

1. 在 Codex 中发送下方安装请求。
2. 安装完成后，输入 `$stca` 选择 STCA，或直接说“使用 $stca 筛选这份候选表”，按需附上文件。
3. 如需手动安装，解压 Codex ZIP，将完整 `stca` 文件夹放在 `~/.agents/skills/stca`。保留其中的 `SKILL.md`、`scripts`、`references` 和 `assets`。

```text
使用 $skill-installer 安装 https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

### DeepSeek Harness

1. 打开 **插件 → 添加插件**。
2. 在输入框填写下面的 **GitHub 安装地址**，点击安装：

```text
github:foukusa/stca-agent-skill
```

3. 安装并启用 STCA 后，输入 `/stca` 或“开始使用 STCA”，说明任务并按需上传数据。

也可在终端通过 DSH CLI 安装：

```bash
dsh plugin --profile web add github:foukusa/stca-agent-skill
```

**GitHub 地址安装不需要先发布 npm 包。** DSH 会从公开仓库读取插件配置和入口。只填 `dsh-plugin-stca` 的方式才需要该包已发布到 npm；尚未发布时使用上面的仓库地址。

已有 STCA 条目时先检查并启用，不必反复添加。安装报错、可选 CLI 及[插件 ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.zip)本地目录安装见[DSH 安装说明](docs/INSTALL.zh-CN.md#deepseek-harness)。另有[独立 skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip)，用于解压后放入 DSH 的 skill 目录；它与“添加插件”读取的插件根目录用途不同。详见 [DSH 专用说明](README.DSH.zh-CN.md)。

插件中心链接：—（上架后补充）。

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

### WorkBuddy

1. 从上表下载 `stca-workbuddy-0.1.5.zip`。
2. 打开 WorkBuddy 的 skill 管理页面，选择添加／上传本地 skill 包，直接选择 ZIP，完成导入并启用 **STCA Polymer Rules and Design**。
3. 输入“开始使用 STCA”，上传文件，再说明要总结规则、筛选候选还是生成重复单元。

商店安装链接将在审核通过并发布后补充。 建议在独立任务文件夹运行，STCA 的运行文件和结果会保存在该工作区。遇到文件操作被拒绝时，AI 助手会说明受阻步骤并保留已完成的结果。见[权限问题处理](docs/INSTALL.zh-CN.md#workbuddy-文件权限)。

### ChatGPT

1. 从上表下载 `stca-openai-skill-0.1.0.zip`。
2. 在支持安装 skill 的 ChatGPT 客户端中，通过导入入口加载；也可上传安装包并要求“请安装这个 STCA skill”。
3. STCA 出现在可用 skill 中后，选择它或说“使用 STCA 筛选这份表”。计算还需要客户端提供文件访问和代码执行能力。如果当前客户端没有 skill 安装能力，使用上面的其他平台。

### 下载文件

ZIP 和 TGZ 链接均指向本仓库 [`downloads` 目录](https://github.com/foukusa/stca-agent-skill/tree/main/downloads)内的文件页。打开后点击 **Download raw file** 下载，再到对应平台导入本地文件。也可打开[仓库首页](https://github.com/foukusa/stca-agent-skill)，选择 **Code → Download ZIP**，解压后获取 `skills/stca` 源码目录；该仓库版本包含的各平台安装包位于 `downloads`。源码 ZIP 需先解压再按文件夹安装，WorkBuddy 则直接上传其专用 ZIP。

首次计算会查找并检查合适的本地 Python 环境。普通 Python、虚拟环境均可使用，不要求 Conda。AI 助手需要读取指定文件、写入结果目录和执行本地计算；包内已包含经校验的作者实现，普通计算不再克隆 Git 仓库；准备缺失的 Python 依赖时可能访问 PyPI，生成使用当前对话的 LLM。详见[环境处理方式](docs/INSTALL.zh-CN.md#计算环境)。

## 现成规则与生成 prompt

[规则与 prompt 目录](docs/RULE_LIBRARY.zh-CN.md)按**数据来源 → 性质 → 百分比**列出选择；也可载入你自己归纳并保存的规则包。开源数据规则覆盖气体渗透率、聚合物体相性质与水接触角，目录标明可选百分比、两种方法的规则可用状态与推荐；也提供作者 STCA 论文中实现的 Tg 与电导率冻结规则。

| 来源 | 可选性质 |
|---|---|
| [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x) | 高 Tg、低电导率、高电导率 |
| [GAS 实测数据](https://github.com/jsunn-y/PolymerGasMembraneML) | CO₂、O₂ 渗透率 |
| [RadonPy 计算数据](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv) | 热导率、折射率、密度、比热、介电常数 |
| [ADEPT 计算数据](https://github.com/sobinalosious/PolyGraphMT/tree/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw) | 热导率、密度、孤立单体 HOMO–LUMO 能隙、介电常数、折射率 |
| [OpenPoly 文献数据](examples/water_contact_angle/README.zh-CN.md) | 水接触角 |

目录也支持水接触角Top **10%、20%、30%**的结构筛选。其他用法可参考[RadonPy密度案例](examples/radonpy_density/README.zh-CN.md)。

目录显示每个档位的**方法、规则可用状态、推荐、具体物理阈值、比较符及单位**。接受推荐就直接使用，也可明确选择可用方法；可用规则分别应用。所选冻结目录没有的百分比，例如开源数据目录之外的 15%、25%，需上传带标签数据学习新规则，不能插值或改用相邻档位。若只想将 prompt 用于其他 LLM，可明确请求“只给完整 prompt，暂不生成”。

Tg 与电导率规则用于作者 STCA 论文中展示的实验性质筛选任务。GAS、RadonPy、ADEPT 和 OpenPoly 的公开数据任务也已使用 STCA 完成规则归纳与筛选验证。选择符合目标的现成规则，或从自己的数据总结；详见[规则目录](docs/RULE_LIBRARY.zh-CN.md#stca-论文规则)、[数据来源](examples/open_data/dataset_registry.csv)和[应用示例](examples/open_data/README.zh-CN.md)。

## 准备数据

### 指定结构列与性质列

**使用现成规则筛选只需结构列；从数据学习规则还必须绑定数值性质列与单位。** 标识列可省略或任意命名，不参与性质学习。按列名绑定，表格列号仅用于帮助定位。

上传自己的数据时，可以直接说：

```text
使用 STCA 总结高密度规则。结构列为 SMILES，性质列为 Density，单位 g/cm³，使用全部数据行。返回筛选结果并保存规则。
```

AI 助手会在学习前说明读取的文件、数据行数、结构列、性质列、单位和方向。含义唯一时可自动匹配并继续；存在多个性质候选、重复表头或单位不明时，先确认再计算。ADEPT范例明确绑定 `SMILES` 与 `BANDGAP`，单位为eV。你指定的列名优先使用；已有数据划分也可要求保留。

### 输入星号、计算 H-cap、输出星号

上传聚合物重复单元时，**保留 SMILES 中原有的 `*` 连接点，无需先自行封端**。处理顺序如下：

| 环节 | SMILES 示例 | 处理方式 |
|---|---|---|
| 输入 | `*CCO*` | 保存原始重复单元及星号位置 |
| 计算 | `CCO` | 在计算副本中将末端单键 `*` 连接点替换为氢，完成 H-cap，再计算指纹 |
| 输出 | `*CCO*` | 从保留的原始结构返回带星号 SMILES，原始连接点位置与标记保持一致 |

**输入带 `*` → H-cap 副本计算 → 返回原始带 `*` 的结构。** H-cap 副本不覆盖原始 SMILES；筛选结果和生成候选核验均遵循这一流程。若输入本来已封端且没有 `*`，则照原样处理和返回。

仅筛选候选时，CSV 可以是：

```csv
CandidateKey,SMILES
sample-A7,*CCO*
42-blue,*CC*
```

学习时还需在同一行提供对应的数值性质列，并说明标签是实验测量还是计算结果。

## 数据划分与评价

结构距离使用 **ECFP4**：对 H-cap 计算副本生成 radius=2、2,048 位 Morgan 指纹，**距离 = 1 − Tanimoto 相似度**。相同原始结构及相同 H-cap 副本保持在同一保护组。

| 分区或评价 | 具体做法 |
|---|---|
| **内推区域（interpolation）** | 在这里归纳规则，选择数据变换、扫描步长及支持量。 |
| **外推区域（extrapolation）** | 使用性质标签前，先在结构空间外围选择一个邻域，目标约占有效结构记录的 20%；每条外推结构到 interpolation 区域的最近邻距离均 **≥0.5**。 |
| **相似性缓冲区** | 将与 extrapolation 区域距离不足 0.5 的其他结构组隔离，不训练、不外评，但仍返回筛选结果。 |
| **内推范围内评价** | 在 interpolation 区域中按保护结构组进行 5 折、3 次重复交叉验证；结果基于该区域的数据准备，不是另设的独立内推测试集。 |

这样划分是为了防止相同或近邻结构跨越 interpolation 与 extrapolation 边界，检验规则向不同聚合物结构的迁移能力。推荐方法由 **interpolation 区域内部的另一层 Morgan 距离验证**确定，再评价 extrapolation 区域；冻结后的阈值与规则保持不变。详见[评价说明](docs/MORGAN_EVALUATION.zh-CN.md)。

## 论文与作者

**Weihao Wang** — [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x) · [原始实现](https://github.com/foukusa/polymer-stca) · [软件引用](CITATION.cff)

也可打开 [Code Ocean 上的 STCA 简易复现版本](https://doi.org/10.24433/CO.1601774.v1)，查看代码与数据并在线运行示例。

[ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

源码公开，采用 **STCA Agent Skill Academic Use License**，允许非商业学术研究、教育与科学结果复现；商业使用及再分发需事先取得书面许可。详见 [LICENSE](LICENSE) 和 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

<p align="center"><em>化繁为简，拨云见日</em></p>
