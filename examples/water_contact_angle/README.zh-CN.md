# 支持性质：水接触角

[English](README.md) · [现成规则目录](../../docs/RULE_LIBRARY.zh-CN.md#openpoly水接触角)

OpenPoly水接触角扩展了STCA规则库的性质范围。目录保留Top10%、20%、30%的STCA与WRAcc规则及实际评价结果。

## 原始数据

[OpenPoly.csv](OpenPoly.csv)为文献性质表，共741行、32列，其中175行有水接触角标签。结构列为`PSMILES`（B/第2列），目标列为`Water Contact Angle (deg)`（Y/第25列），单位为度。`PSMILES_2`与`PSMILES_4`不用于本条目的结构计算。0°是有效的完全润湿值。

来源：[OpenPoly原始表](https://github.com/WangGroupFDU/Openpoly_benchmark/blob/ccaa66900747bfc576ef935e3d5f220b6c9b1f85/data/final_polymer_properties_fromliterature.csv) · [原研究](https://doi.org/10.1007/s10118-025-3402-y) · [原始MIT许可](OpenPoly_LICENSE.txt)。表中未给出测量条件。

## 三档规则与实际结果

结构划分为461条source、148条holdout、131条buffer，另1条结构不支持当前计算。source准备后104条带标签观测；holdout中31条有标签可评分。最近邻ECFP4距离均≥0.5。

| 目标 | 冻结角度阈值 | 方法 | 精确率 | 召回率 | F1 | MCC |
|---|---:|---|---:|---:|---:|---:|
| Top30% | ≥87.714722219° | STCA | 0.5000 | 0.1818 | 0.2667 | 0.1168 |
| Top30% | ≥87.714722219° | WRAcc | 0.6000 | 0.2727 | 0.3750 | 0.2247 |
| Top20% | ≥97.368824894° | STCA | 0.0000 | 0.0000 | 0.0000 | -0.2079 |
| Top20% | ≥97.368824894° | WRAcc | 0.0000 | 0.0000 | 0.0000 | -0.2368 |
| Top10% | ≥104.17491015° | STCA | 0.0000 | 0.0000 | 0.0000 | -0.1886 |
| Top10% | ≥104.17491015° | WRAcc | 1.0000 | 0.5000 | 0.6667 | 0.6682 |

精确条件与完整prompt从现成规则目录选择。全部数值见[evaluation.csv](evaluation.csv)及[来源记录](source.json)。原始星号结构保留；H-cap只用于计算副本。
