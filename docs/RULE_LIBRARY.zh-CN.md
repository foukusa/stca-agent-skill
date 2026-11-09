# STCA 现成规则与生成 prompt

**版本 0.1.0** · [English](RULE_LIBRARY.md) · [返回首页](../README.zh-CN.md)

输入 **“开始使用 STCA”**，说明要筛选或生成，目录会自动显示。选定来源、性质、百分比及规则后，AI 助手载入完整条件；你无需输入规则编号。也可在下表点击方法名，直接获取完整中文生成 prompt。

## 目录

- [如何选择](#如何选择)
- [STCA 论文规则](#stca-论文规则)
- [GAS：实测气体渗透率](#gas实测气体渗透率)
- [RadonPy：五种计算性质](#radonpy五种计算性质)
- [ADEPT：五种计算性质](#adept五种计算性质)
- [OpenPoly：水接触角](#openpoly水接触角)
- [使用自己的数据](#使用自己的数据)

## 如何选择

目录提供 STCA 论文规则，以及从公开数据归纳的 source 冻结规则。每项保留精确条件、具体物理目标边界、方法、可用状态和对应评价；无有效规则时明确标记，不能用空条件代替。

当前开源规则与重新学习采用相同的先结构划分、仅 source 准备及逐百分比独立设置。同一来源文件、列名、距离划分设置及程序环境下，重新学习应重现对应规则。WRAcc 在训练数据内部选择条件数上限，也可指定固定上限或不设上限；保存后的规则保留精确条件。

开源数据目录覆盖 **13 项任务**，包括 OpenPoly 水接触角，均提供高值方向 Top **10%、20%、30%** 的结果。每档分别列出 **STCA 与 WRAcc** 的规则及可用状态。可接受当前目录的推荐，也可自行选择可用方法；下表链接按方法分别提供，AI 助手读取当前推荐及评分。

例如：“用 GAS 的高 CO₂ 渗透率 Top 10% 主推规则筛选这份候选。”或“用 ADEPT 高介电常数 Top 20% 的 WRAcc 规则直接生成 20 个候选。”

生成时，选定规则后可选**先预览，确认后生成**或**直接生成**。预览方式会展示完整 prompt 供修改，等待你回复“确认，开始生成”；直接方式则立即调用当前 LLM。两种方式都会实际生成候选，并按选定规则逐条核验。需要转到其他 LLM 时，可明确请求“只给完整 prompt”。

选定档位和完整 prompt 均包含**具体物理阈值、≥／≤ 比较符、单位**及全部结构条件。百分比表示原数据的目标范围，并非候选入选配额；筛选返回原始 SMILES、判断与每条未满足的规则条件。多目标时，分别选择各目标的规则，再报告同时满足的候选。

AS（Average Score）是作者 [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x)提出并定义、在聚合物筛选任务评价中验证使用的综合衡量指标，本 skill 沿用其马修斯相关系数（MCC）、精确率（Precision）与 F1 分数算术平均的计算方式。

方法推荐依据 **source 内的 Morgan 距离验证**，在独立外部 holdout 评价前冻结。两方法都有可用验证证据时，WRAcc 平均筛选评分高出 STCA **超过 0.02** 才主推 WRAcc，否则保留 STCA。独立 holdout 到 source 的 ECFP4 最近邻 Tanimoto 距离 **≥ 0.5**；原表回筛数量与这些外推评分分别交付。详见[评价协议](MORGAN_EVALUATION.zh-CN.md)。

## STCA 论文规则

这些 Tg 与电导率冻结规则用于作者 [STCA 论文](https://doi.org/10.1038/s41524-026-02345-x)中展示的结构筛选与生成任务。选择下表中的性质和百分比，即可使用完整的规则引导 prompt。

| 性质与方向 | 单位 | 完整 prompt |
|---|---|---|
| 高 Tg | °C | [Top 10%](../skills/stca/assets/rule_library/entries/paper-tg-high-10/prompt.zh-CN.md) · [Top 20%](../skills/stca/assets/rule_library/entries/paper-tg-high-20/prompt.zh-CN.md) · [Top 30%](../skills/stca/assets/rule_library/entries/paper-tg-high-30/prompt.zh-CN.md) |
| 低电导率 | S/cm | [Bottom 5%](../skills/stca/assets/rule_library/entries/paper-ec-low-5/prompt.zh-CN.md) · [Bottom 10%](../skills/stca/assets/rule_library/entries/paper-ec-low-10/prompt.zh-CN.md) · [Bottom 15%](../skills/stca/assets/rule_library/entries/paper-ec-low-15/prompt.zh-CN.md) · [Bottom 20%](../skills/stca/assets/rule_library/entries/paper-ec-low-20/prompt.zh-CN.md) |
| 高电导率 | S/cm | [Top 5%](../skills/stca/assets/rule_library/entries/paper-ec-high-5/prompt.zh-CN.md) · [Top 10%](../skills/stca/assets/rule_library/entries/paper-ec-high-10/prompt.zh-CN.md) · [Top 15%](../skills/stca/assets/rule_library/entries/paper-ec-high-15/prompt.zh-CN.md) · [Top 20%](../skills/stca/assets/rule_library/entries/paper-ec-high-20/prompt.zh-CN.md) |

## GAS：实测气体渗透率

数据来源：[PolymerGasMembraneML Dataset A](https://github.com/jsunn-y/PolymerGasMembraneML)，对应[气体渗透率研究](https://doi.org/10.1126/sciadv.abn9545)。CO₂ 与 O₂ 标签来自实验测量，已使用 STCA 完成规则归纳与筛选验证。

| 性质 | 单位 | Top 10% | Top 20% | Top 30% |
|---|---|---|---|---|
| CO₂ 渗透率 | Barrer | [WRAcc](../skills/stca/assets/rule_library/entries/current-gas-co2-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-gas-co2-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-gas-co2-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-gas-co2-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-gas-co2-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-gas-co2-stca-high-30/prompt.zh-CN.md) |
| O₂ 渗透率 | Barrer | [WRAcc](../skills/stca/assets/rule_library/entries/current-gas-o2-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-gas-o2-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-gas-o2-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-gas-o2-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-gas-o2-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-gas-o2-stca-high-30/prompt.zh-CN.md) |

## RadonPy：五种计算性质

数据来源：[RadonPy PI1070](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv)，对应[RadonPy 研究](https://doi.org/10.1038/s41524-022-00906-4)。以下标签来自聚合物分子动力学计算，已使用 STCA 完成规则归纳与筛选验证。

| 性质 | 单位 | Top 10% | Top 20% | Top 30% |
|---|---|---|---|---|
| 热导率 | W/(m K) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-tc-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-tc-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-tc-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-tc-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-tc-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-tc-stca-high-30/prompt.zh-CN.md) |
| 折射率 | 无量纲 | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-ri-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-ri-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-ri-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-ri-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-ri-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-ri-stca-high-30/prompt.zh-CN.md) |
| 密度 | g/cm³ | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-rho-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-rho-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-rho-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-rho-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-rho-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-rho-stca-high-30/prompt.zh-CN.md) |
| 比热容 | J/(kg K) | [STCA](../skills/stca/assets/rule_library/entries/current-pi-cp-stca-high-10/prompt.zh-CN.md) · [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-cp-wracc-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-cp-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-cp-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-cp-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-cp-stca-high-30/prompt.zh-CN.md) |
| 介电常数 | 无量纲 | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-dc-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-dc-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-dc-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-pi-dc-stca-high-20/prompt.zh-CN.md) | [STCA](../skills/stca/assets/rule_library/entries/current-pi-dc-stca-high-30/prompt.zh-CN.md) · [WRAcc](../skills/stca/assets/rule_library/entries/current-pi-dc-wracc-high-30/prompt.zh-CN.md) |

## ADEPT：五种计算性质

数据来源：[PolyGraphMT 提供的 ADEPT 数据](https://github.com/sobinalosious/PolyGraphMT/tree/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw)，对应[ADEPT 研究](https://doi.org/10.1039/D6DD00206D)。这些 MD／DFT 性质任务已使用 STCA 完成规则归纳与筛选验证。能隙指氢封端孤立单体的 HOMO–LUMO 能隙。

| 性质 | 单位 | Top 10% | Top 20% | Top 30% |
|---|---|---|---|---|
| 热导率 | W/(m K) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-tc-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-tc-stca-high-10/prompt.zh-CN.md) | [STCA](../skills/stca/assets/rule_library/entries/current-ad-tc-stca-high-20/prompt.zh-CN.md) · [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-tc-wracc-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-tc-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-tc-stca-high-30/prompt.zh-CN.md) |
| 密度 | g/cm³ | [STCA](../skills/stca/assets/rule_library/entries/current-ad-rho-stca-high-10/prompt.zh-CN.md) · [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-rho-wracc-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-rho-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-rho-stca-high-20/prompt.zh-CN.md) | [STCA](../skills/stca/assets/rule_library/entries/current-ad-rho-stca-high-30/prompt.zh-CN.md) · [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-rho-wracc-high-30/prompt.zh-CN.md) |
| 孤立单体 HOMO–LUMO 能隙 | eV | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-gap-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-gap-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-gap-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-gap-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-gap-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-gap-stca-high-30/prompt.zh-CN.md) |
| 介电常数 | 无量纲 | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-dc-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-dc-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-dc-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-dc-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-dc-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-dc-stca-high-30/prompt.zh-CN.md) |
| 折射率 | 无量纲 | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-ri-wracc-high-10/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-ri-stca-high-10/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-ri-wracc-high-20/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-ri-stca-high-20/prompt.zh-CN.md) | [WRAcc](../skills/stca/assets/rule_library/entries/current-ad-ri-wracc-high-30/prompt.zh-CN.md) · [STCA](../skills/stca/assets/rule_library/entries/current-ad-ri-stca-high-30/prompt.zh-CN.md) |

## OpenPoly：水接触角

数据来源：[OpenPoly](https://github.com/WangGroupFDU/Openpoly_benchmark)，收录文献报道的聚合物性质。水接触角使用同样的先结构划分、仅 source 学习及 Morgan 距离评价流程。该性质用于展示规则库的适用范围；三档两方法及实际分数全部保留，原表和字段见[来源说明](../examples/water_contact_angle/README.zh-CN.md)。

| 性质 | 单位 | Top 10% | Top 20% | Top 30% |
|---|---|---|---|---|
| 水接触角 | ° | [STCA](../skills/stca/assets/rule_library/entries/current-openpoly-wca-stca-high-10/prompt.zh-CN.md) · [WRAcc](../skills/stca/assets/rule_library/entries/current-openpoly-wca-wracc-high-10/prompt.zh-CN.md) | [STCA](../skills/stca/assets/rule_library/entries/current-openpoly-wca-stca-high-20/prompt.zh-CN.md) · [WRAcc](../skills/stca/assets/rule_library/entries/current-openpoly-wca-wracc-high-20/prompt.zh-CN.md) | [STCA](../skills/stca/assets/rule_library/entries/current-openpoly-wca-stca-high-30/prompt.zh-CN.md) · [WRAcc](../skills/stca/assets/rule_library/entries/current-openpoly-wca-wracc-high-30/prompt.zh-CN.md) |

## 使用自己的数据

需要冻结目录没有的百分比、低密度等新方向，或希望使用自己的数据条件时，直接要求 AI 助手从上传数据总结规则。可指定 0% 与 100% 之间的任意百分比，如 15%、25%；未指定时直接使用 Top 或 Bottom **10%、20%、30%**。冻结目录缺少的档位不能插值或替换成相邻档。AI 助手会学习两种方法，分别返回逐档原表筛选结果和带比较符、单位的具体物理阈值，标明主推与推荐理由，保存完整规则、模型与双语 prompt，并给出实际文件位置。接着说“用刚保存的规则筛选”或“按刚才的规则生成”即可；新会话可上传保存的规则包载入。

详见[自然语言使用案例](USAGE.zh-CN.md)和[公开数据应用示例](../examples/open_data/README.zh-CN.md)。规则版本、精确条件和方法信息保存在[机器可读目录](../skills/stca/assets/rule_library/catalog.json)中。
