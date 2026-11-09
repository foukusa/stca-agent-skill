<p align="center"><img src="https://raw.githubusercontent.com/foukusa/stca-agent-skill/main/assets/stca-logo.png" alt="STCA logo" width="104"></p>

# STCA：DeepSeek Harness 版

从聚合物结构与性质数据总结可读规则、筛选候选，或调用当前 AI 按规则生成聚合物重复单元。

**版本 0.1.0** · [English](https://github.com/foukusa/stca-agent-skill/blob/main/README.DSH.md)

## 目录

- [安装与开始](#安装与开始)
- [选择任务](#选择任务)
- [数据列与星号连接点](#数据列与星号连接点)
- [用 RadonPy 密度数据试用](#用-radonpy-密度数据试用)
- [运行环境与权限](#运行环境与权限)
- [许可与来源](#许可与来源)

## 安装与开始

1. 在 DSH 打开 **插件 → 添加插件**。
2. 在“包名、GitHub 仓库地址或本地目录路径”输入框中填写：

```text
github:foukusa/stca-agent-skill
```

3. 点击安装，完成后启用 STCA，再输入 `/stca` 或“开始使用 STCA”。

**这是从 GitHub 仓库安装插件，无需先发布 npm 包。** 仓库中已提供 `package.json`、插件入口和完整 skill 资源。不要将 `dsh plugin ...` 命令粘贴到这个图形界面输入框。

| 方式 | 在“添加插件”中填写 |
|---|---|
| **GitHub 仓库，当前推荐** | `github:foukusa/stca-agent-skill` |
| 下载插件 ZIP 后安装 | [插件 ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.zip)解压后，直接包含 `package.json` 的文件夹完整路径 |
| npm 包名，发布后可用 | `dsh-plugin-stca` |
| 插件中心 | —（上架后补充链接） |

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

在“添加插件”中使用上面的 `github:` 地址。若之前用 HTTPS 地址安装时出现“无法从依赖变更中确定安装了哪一个包”，改用此地址重试。已有 STCA 条目时先检查并启用；替换旧版时保留数据、结果和保存的规则。安装报错及可选 CLI 操作见[安装说明](https://github.com/foukusa/stca-agent-skill/blob/main/docs/INSTALL.zh-CN.md#deepseek-harness)。

本地目录方式是备选：打开插件 ZIP 文件页，点击 **Download raw file** 下载并解压，再填写完整目录路径。另有[独立 skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip)，用于手动放置含 `SKILL.md` 的完整 `stca` 文件夹，与插件目录的安装方式分开。

## 选择任务

STCA 通过当前 LLM 对话工作。你可以直接提出任务；只说“开始使用 STCA”时，AI 助手会介绍可选的三种用法。直接用自然语言说明目标即可。

| 选择 | 得到什么 | 可以直接说 |
|---|---|---|
| **上传数据总结规则** | 返回两种方法的结果与可用状态，保存可用规则并给出阈值和推荐 | “从这份聚合物热导率数据总结高值规则并保存。” |
| **用已有规则筛选** | 每条原始候选的判断、未满足的规则条件及入选表 | “先显示规则目录，用我选的规则筛选这份候选。” |
| **用已有规则生成** | 当前 LLM 按规则生成重复单元，再逐条核验结构条件 | “先选规则，再直接生成 20 个聚合物重复单元并核验。” |

完整处理 prompt 已内置。归纳时未指定百分比，就使用 Top 或 Bottom **10%、20%、30%**；也可自定其他合法百分比。每档返回具体阈值、比较符和单位。WRAcc 默认在训练数据内选择条件数上限；也可直接说“WRAcc 最多使用 10 条条件”或“不限制 WRAcc 条件数”。两种方法分别返回，并给出推荐。保留原始 SMILES 与重复单元连接点，H-cap 仅用于计算副本。

尚未指定规则时，AI 助手先显示可选规则目录。可选择**先预览，确认后生成**，查看并调整 prompt；也可选择**直接生成**。AI 助手会返回保存的规则文件和位置。接着说“用刚才保存的规则筛选这份候选”或“用这些规则生成”，即可继续。完整对话见[自然语言使用案例](https://github.com/foukusa/stca-agent-skill/blob/main/docs/USAGE.zh-CN.md)，现成结论见[规则目录](https://github.com/foukusa/stca-agent-skill/blob/main/docs/RULE_LIBRARY.zh-CN.md)。

## 数据列与星号连接点

总结规则必须明确绑定**结构列、数值性质列及单位**，可以在请求中直接指定。对于下面的 RadonPy 等已知案例，配置已给出列映射；自己的文件则先读取表头，并在学习前显示将使用的列名、目标含义和单位。如果同时有实测与计算密度、不同温度，或均值与最小／最大值等多个可能目标，会先请你选择。你明确指定的列名优先；不能只看数值范围判断哪列是密度。使用已有规则筛选候选只需结构列，不要求候选已有性质标签。

上传原始重复单元 SMILES 时，**保留其中的 `*` 连接点**。STCA 保存这份原文，另建计算副本：把支持的末端单键连接点用氢封端（**H-cap**），再计算指纹。返回结果时使用保存的原始 SMILES，`*` 的位置与输入一致。这里不是字符串替换，也不从封端分子反推连接点。已经封端的输入保持原样，不凭空补星号。

| 上传的原始结构 | H-cap 计算副本 | 返回的结构 |
|---|---|---|
| `*CCO*` | `CCO` | `*CCO*` |

## 用 RadonPy 密度数据试用

在 GitHub 文件页下载 [RadonPy `PI1070.csv`](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv) 并上传到 DSH。先读取全部 **1,077 条记录**：第 1 行是表头，第 2–1078 行是数据。结构使用 `smiles`（B 列／第 2 列），目标使用 `density`（AA 列／第 27 列），单位 g/cm³，标签来自分子动力学计算；`monomer_ID`（A 列／第 1 列）是可选标识。AI 助手按列名读取，无需手工选取单元格，其他密度统计列不作为目标。

**现成规则筛选：**

```text
使用推荐的 RadonPy 高密度 Top 30% 规则筛选这份数据。
```

本例推荐 **WRAcc**，应返回 **389 条规则匹配、688 条未匹配、0 条未知**；明确选择 STCA 时为 **282 条匹配、795 条未匹配、0 条未知**。两种方法的密度目标边界均为 **≥ 1.222080875 g/cm³**。WRAcc 的交叉验证平均筛选评分为 **0.7014**，STCA 为 **0.6479**；WRAcc 的召回率和 F1 更高，STCA 的精确率更高。

**学习、筛选并保存：**

```text
从这份 RadonPy 文件的全部数据行总结高密度 Top 30% 规则。结构列为 smiles，性质列为 density，单位 g/cm³。返回筛选结果，与现成规则比较，并保存新规则。
```

每个百分比独立准备并学习。使用这份固定文件、同一版本和默认设置时，新学习的两种 Top 30% 规则应分别与对应内置规则一致，单独运行或同时请求其他百分比均相同。要复用推荐规则，可说：“重新载入刚保存的 Top 30% WRAcc 规则，再筛选同一份数据。”每行判断应与刚才一致。

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
- 包内已包含经校验的作者实现，普通计算无需 Git，也不再克隆源码；准备缺失的 Python 依赖时可能访问 PyPI。生成使用当前 DSH 会话已配置的模型／服务商，STCA 无需另配模型 API；数据处理仍遵循当前会话与服务商的规则。

## 许可与来源

这是社区开发的 STCA 集成，与 DeepSeek AI 无官方隶属关系。源码采用 **[STCA Agent Skill Academic Use License](https://github.com/foukusa/stca-agent-skill/blob/main/LICENSE)**：允许非商业学术研究、教育与科学结果复现；商业使用和再分发需事先获得书面许可。第三方组件保留[各自的声明与条款](https://github.com/foukusa/stca-agent-skill/blob/main/THIRD_PARTY_NOTICES.md)。

**Weihao Wang** · [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x) · [原始实现](https://github.com/foukusa/polymer-stca) · [完整项目说明](https://github.com/foukusa/stca-agent-skill/blob/main/README.zh-CN.md) · [ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

<p align="center"><em>化繁为简，拨云见日</em></p>
