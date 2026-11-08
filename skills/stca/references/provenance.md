# 论文、代码与数据来源

## STCA 论文与实现

本 skill 基于作者 STCA 论文中的方法与实现，提供论文中展示的 Tg 与电导率结构规则，用于候选筛选、规则解释和 LLM 引导生成。

- **论文：**[Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design](https://doi.org/10.1038/s41524-026-02345-x)。
- **作者：**Weihao Wang、Haoou Ruan、Keith T. Butler、Akiko Kumada、Masahiro Sato。
- **原始代码：**[foukusa/polymer-stca](https://github.com/foukusa/polymer-stca)。

## 在线尝试 STCA

[在 Code Ocean 打开 STCA 简易复现版本](https://doi.org/10.24433/CO.1601774.v1)，查看配套代码与数据，在线运行示例，体验从规则归纳到筛选结果的过程。需要在自己的数据上使用时，可通过本 skill 直接描述目标并上传数据。

## 开源数据与筛选验证

下列公开数据已用于 STCA 的规则归纳与筛选验证，提供论文案例之外可直接选择的规则。

| 数据来源 | 性质与标签类型 | 公开入口 |
|---|---|---|
| PolymerGasMembraneML / GAS Dataset A | 实测 CO₂、O₂ 渗透率 | [数据与代码](https://github.com/jsunn-y/PolymerGasMembraneML) · [研究论文](https://doi.org/10.1126/sciadv.abn9545) |
| RadonPy / PI1070 | MD 计算的热导率、折射率、密度、比热、介电常数 | [数据与代码](https://github.com/RadonPy/RadonPy) · [研究论文](https://doi.org/10.1038/s41524-022-00906-4) |
| ADEPT / PolyGraphMT | 计算的热导率、密度、孤立单体 HOMO–LUMO 能隙、介电常数、折射率 | [数据与代码](https://github.com/sobinalosious/PolyGraphMT) · [研究论文](https://doi.org/10.1039/D6DD00206D) |

每条规则保留对应的数据来源、性质、方向、百分比及数值阈值。选择与你的目标相符的规则即可筛选或生成，也可上传自己的数据重新归纳。

## AS 综合评价指标

**AS（Average Score）由 STCA 论文提出并定义，在论文的聚合物筛选任务评价中验证使用。**它将 MCC、Precision 和 F1 取算术平均，用作筛选效果的综合衡量指标：

`AS = (MCC + Precision + F1) / 3`

本 skill 沿用该定义，在同一数据与目标档位上比较 STCA 和 WRAcc，分别返回两种方法的结果，并给出推荐方法及理由。

## 进一步使用

- [自然语言使用案例](usage_examples.md)
- [规则与 prompt 目录](../assets/rule_library/index.md)
- [数据准备与自己的规则](custom_data.md)
- [软件许可](https://github.com/foukusa/stca-agent-skill/blob/main/LICENSE) · [第三方声明](https://github.com/foukusa/stca-agent-skill/blob/main/THIRD_PARTY_NOTICES.md)

**化繁为简，拨云见日。**
