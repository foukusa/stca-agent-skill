<p align="center"><img src="https://raw.githubusercontent.com/foukusa/stca-agent-skill/main/assets/stca-logo.png" alt="STCA logo" width="104"></p>

# STCA：DeepSeek Harness 版

从聚合物结构与性质数据总结可读规则、筛选候选，或调用当前 AI 按规则生成聚合物重复单元。

**DSH 包名：`dsh-plugin-stca` · 版本 0.1.0** · [English](https://github.com/foukusa/stca-agent-skill/blob/main/README.DSH.md)

## 目录

- [安装与开始](#安装与开始)
- [选择任务](#选择任务)
- [用 RadonPy 密度数据试用](#用-radonpy-密度数据试用)
- [运行环境与权限](#运行环境与权限)
- [许可与来源](#许可与来源)

## 安装与开始

1. 打开 **插件 → 添加插件**。
2. 填写下列任一来源，完成安装并启用 STCA。
3. 输入 `/stca`，直接说明希望完成的任务。

| 方式 | 填写内容 |
|---|---|
| GitHub 仓库 | `https://github.com/foukusa/stca-agent-skill.git` |
| npm 包名 | `dsh-plugin-stca`，npm 发布后可用 |
| 插件中心 | —（上架后补充链接） |

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

使用 CLI 时，选择实际使用的 profile。以下命令以 `web` 为例：

```bash
dsh plugin --profile web add github:foukusa/stca-agent-skill
```

npm 发布完成后，可按包名安装：

```bash
dsh plugin --profile web add dsh-plugin-stca
```

下面的安装包链接均指向本仓库内的文件页，打开后点击 **Download raw file** 下载。也可在[GitHub 仓库](https://github.com/foukusa/stca-agent-skill)选择 **Code → Download ZIP** 下载源码，其中 DSH skill 位于 `skills/stca`。下载[插件 TGZ](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz)，在“添加插件”中填写其完整本地路径。[skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) 则采用解压后放置文件夹的方式，具体见[安装说明](https://github.com/foukusa/stca-agent-skill/blob/main/docs/INSTALL.zh-CN.md#deepseek-harness)。

启用后输入 **`/stca`**，或直接说 **“开始使用 STCA”**。

## 选择任务

STCA 通过当前 LLM 对话工作。你可以直接提出任务；只说“开始使用 STCA”时，AI 助手会介绍可选的三种用法。直接用自然语言说明目标即可。

| 选择 | 得到什么 | 可以直接说 |
|---|---|---|
| **上传数据总结规则** | 保存 STCA 与 WRAcc 规则，返回对应筛选结果、实际阈值及推荐方法 | “从这份聚合物热导率数据总结高值规则并保存。” |
| **用已有规则筛选** | 每条原始候选的判断、未满足的规则条件及入选表 | “先显示规则目录，用我选的规则筛选这份候选。” |
| **用已有规则生成** | 当前 LLM 按规则生成重复单元，再逐条核验结构条件 | “先选规则，再直接生成 20 个聚合物重复单元并核验。” |

完整处理 prompt 已内置。归纳时未指定百分比，就使用 Top 或 Bottom **10%、20%、30%**；也可自定其他合法百分比。每档返回具体阈值、比较符和单位。WRAcc 默认在训练数据内选择条件数上限；也可直接说“WRAcc 最多使用 10 条条件”或“不限制 WRAcc 条件数”。两种方法分别返回，并给出推荐。保留原始 SMILES 与重复单元连接点，H-cap 仅用于计算副本。

尚未指定规则时，AI 助手先显示可选规则目录。可选择**先预览，确认后生成**，查看并调整 prompt；也可选择**直接生成**。AI 助手会返回保存的规则文件和位置。接着说“用刚才保存的规则筛选这份候选”或“用这些规则生成”，即可继续。完整对话见[自然语言使用案例](https://github.com/foukusa/stca-agent-skill/blob/main/docs/USAGE.zh-CN.md)，现成结论见[规则目录](https://github.com/foukusa/stca-agent-skill/blob/main/docs/RULE_LIBRARY.zh-CN.md)。

## 用 RadonPy 密度数据试用

在 GitHub 文件页下载 [RadonPy `PI1070.csv`](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv) 并上传到 DSH。先读取全部 **1,077 条记录**：第 1 行是表头，第 2–1078 行是数据。结构使用 `smiles`（B 列／第 2 列），目标使用 `density`（AA 列／第 27 列），单位 g/cm³，标签来自分子动力学计算；`monomer_ID`（A 列／第 1 列）是可选标识。AI 助手按列名读取，无需手工选取单元格，其他密度统计列不作为目标。

**现成规则筛选：**

```text
使用现成的 RadonPy 高密度 Top 30% STCA 规则筛选这份数据。
```

这个固定文件应返回 **137 条规则匹配、940 条未匹配、0 条未知**；规则的密度目标边界为 **≥ 1.222343047 g/cm³**。

**学习、筛选并保存：**

```text
从这份 RadonPy 数据总结高密度 Top 30% 规则，返回筛选结果，与现成规则比较，并保存新规则。
```

相同训练数据、预处理、指纹和设置下重新计算应得到相同规则；自适应重学可能与现成规则不同。重新载入刚保存的模型再筛同表，逐行判断应与该模型学习完成时一致，可直接说：“重新载入刚保存的 Top 30% STCA 规则，再筛选同一份数据。”

**生成：**

```text
使用刚保存的高密度 Top 30% STCA 规则，直接生成 5 个聚合物重复单元并核验。
```

也可先要求展示完整 prompt，调整后回复“确认，开始生成”。当前 DSH 的 LLM 实际生成提案，STCA 执行结构核验。详见[完整 RadonPy 案例](https://github.com/foukusa/stca-agent-skill/blob/main/examples/radonpy_density/README.zh-CN.md)。

也可查看[一次实际生成的五条提案及核验结果](https://github.com/foukusa/stca-agent-skill/blob/main/examples/radonpy_density/generated_examples.csv)。

## 运行环境与权限

- DSH 版本要求：**`>=0.0.1-rc.3 <0.3.0`**。
- 计算使用 **CPU 与 Python 3.10 及以上环境**。筛选和结构核验需要 RDKit，学习还使用数值计算依赖。STCA 自动查找并检查普通 Python、虚拟环境或 Conda 环境，**不要求安装 Conda，也不要求手工填写 Python 路径**。优先复用兼容环境，缺少依赖时可在用户缓存中准备独立环境。
- 当前 DSH 会话需允许读取指定数据、写入结果目录及执行本地命令。原输入保留，结果另存；查询规则和读取现成 prompt 不需要 RDKit。计算环境无法运行时，生成提案会标为“待核验”，不会据此把结构记为无效或规则不匹配。
- 准备依赖时可能访问 PyPI；学习时准备作者代码可能访问 GitHub，并需要 Git。生成使用当前 DSH 会话已配置的模型／服务商，STCA 无需另配模型 API；数据处理仍遵循当前会话与服务商的规则。

## 许可与来源

这是社区开发的 STCA 集成，与 DeepSeek AI 无官方隶属关系。源码采用 **[STCA Agent Skill Academic Use License](https://github.com/foukusa/stca-agent-skill/blob/main/LICENSE)**：允许非商业学术研究、教育与科学结果复现；商业使用和再分发需事先获得书面许可。第三方组件保留[各自的声明与条款](https://github.com/foukusa/stca-agent-skill/blob/main/THIRD_PARTY_NOTICES.md)。

**Weihao Wang** · [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x) · [原始实现](https://github.com/foukusa/polymer-stca) · [完整项目说明](https://github.com/foukusa/stca-agent-skill/blob/main/README.zh-CN.md) · [ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

<p align="center"><em>化繁为简，拨云见日</em></p>
