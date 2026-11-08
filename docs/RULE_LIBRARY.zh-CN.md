# STCA 现成规则与生成 prompt

**版本 0.1.0** · [English](RULE_LIBRARY.md) · [返回首页](../README.zh-CN.md) · [完整机器可读目录](../skills/stca/assets/rule_library/catalog.json)

按数据来源、性质、方向和百分比选择现成规则。此目录提供 77 个冻结规则选项；每个选项都有可直接复制的中文生成 prompt 和精确约束 JSON。

## 目录

- [选择并调用规则](#选择并调用规则)
- [STCA 论文：高 Tg、高与低电导率](#stca-论文高-tg高与低电导率)
- [GAS：实测气体渗透率](#gas实测气体渗透率)
- [RadonPy：五种计算性质](#radonpy五种计算性质)
- [ADEPT：六种计算性质](#adept六种计算性质)
- [AD_GAP：作者默认规则与更多选项](#ad_gap作者默认规则与更多选项)

## 选择并调用规则

1. 先选数据来源和性质，再选高/低方向与百分比。表格中的百分比链接直接打开对应规则的中文 prompt；“约束 JSON”链接打开其精确条件。
2. 打开 prompt，复制完整内容到当前 LLM 或另一个 LLM。可补充候选数量、化学偏好和排除项，并保留原有的规则编号、位条件和 AND 关系。
3. 筛选已有候选或核验生成结构时，在已启用 STCA 的宿主中上传 CSV，并指明所选规则 ID。规则 ID 位于 prompt 的“规则来源”中，也是链接目录名。

例如，选择 GAS 的 CO₂ 高渗透率 Top 15% 后，可以直接请求：

```text
使用 STCA 现成规则 gas-co2-high-15 筛选我上传的 candidates.csv。
结构列为 SMILES，CandidateKey 是可选标识列。
保留原始带 * 的重复单元，返回每条候选的规则判定与全部失败条件。
```

组合多个目标时，分别指定每项规则 ID，例如 `paper-tg-high-20` 与 `paper-ec-low-10`，并要求同一候选同时满足全部规则。

Top/Bottom 百分比表示相应源数据集的目标尾部范围，并不规定新候选或生成结构的通过比例。prompt 中的物理阈值是冻结的训练标签边界；结构命中规则不能替代性质测量或计算。同一性质来自不同数据集时，请保留来源和单位。

## STCA 论文：高 Tg、高与低电导率

这些选项使用 STCA 论文的冻结规则。Tg 提供高值方向；电导率 EC 分别提供高值与低值方向。

| 性质与方向 | 单位 | 可选百分比：打开中文 prompt / 约束 |
|---|---|---|
| 高玻璃化转变温度 Tg | degC | [Top 10%](../skills/stca/assets/rule_library/entries/paper-tg-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-tg-high-10/constraints.json); [Top 20%](../skills/stca/assets/rule_library/entries/paper-tg-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-tg-high-20/constraints.json); [Top 30%](../skills/stca/assets/rule_library/entries/paper-tg-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-tg-high-30/constraints.json) |
| 高电导率 EC | S/cm | [Top 5%](../skills/stca/assets/rule_library/entries/paper-ec-high-5/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-ec-high-5/constraints.json); [Top 10%](../skills/stca/assets/rule_library/entries/paper-ec-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-ec-high-10/constraints.json); [Top 15%](../skills/stca/assets/rule_library/entries/paper-ec-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-ec-high-15/constraints.json); [Top 20%](../skills/stca/assets/rule_library/entries/paper-ec-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-ec-high-20/constraints.json) |
| 低电导率 EC | S/cm | [Bottom 5%](../skills/stca/assets/rule_library/entries/paper-ec-low-5/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-ec-low-5/constraints.json); [Bottom 10%](../skills/stca/assets/rule_library/entries/paper-ec-low-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-ec-low-10/constraints.json); [Bottom 15%](../skills/stca/assets/rule_library/entries/paper-ec-low-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-ec-low-15/constraints.json); [Bottom 20%](../skills/stca/assets/rule_library/entries/paper-ec-low-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/paper-ec-low-20/constraints.json) |

## GAS：实测气体渗透率

GAS 的实测 CO₂ 与 O₂ 渗透率规则均为高值方向，每种性质可选 Top 10%、15%、20%、25%、30%。

| 数据集 | 性质 | 单位 | Top 10% | Top 15% | Top 20% | Top 25% | Top 30% |
|---|---|---|---|---|---|---|---|
| `GAS_CO2` | CO₂ 渗透率 | Barrer | [10%](../skills/stca/assets/rule_library/entries/gas-co2-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/gas-co2-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/gas-co2-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/gas-co2-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/gas-co2-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-30/constraints.json) |
| `GAS_O2` | O₂ 渗透率 | Barrer | [10%](../skills/stca/assets/rule_library/entries/gas-o2-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/gas-o2-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/gas-o2-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/gas-o2-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/gas-o2-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-30/constraints.json) |

## RadonPy：五种计算性质

RadonPy 数据提供热导率、折射率、密度、比热容和介电常数五种计算性质。以下规则均为高值方向；`dimensionless` 表示无量纲。

| 数据集 | 性质 | 单位 | Top 10% | Top 15% | Top 20% | Top 25% | Top 30% |
|---|---|---|---|---|---|---|---|
| `PI_TC` | 热导率 | W/(m K) | [10%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-30/constraints.json) |
| `PI_RI` | 折射率 | dimensionless | [10%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-30/constraints.json) |
| `PI_RHO` | 密度 | g/cm3 | [10%](../skills/stca/assets/rule_library/entries/radonpy-density-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-density-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-density-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-density-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-density-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-30/constraints.json) |
| `PI_CP` | 比热容 | J/(kg K) | [10%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-30/constraints.json) |
| `PI_DC` | 介电常数 | dimensionless | [10%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-30/constraints.json) |

## ADEPT：六种计算性质

ADEPT 数据提供热导率、密度、孤立单体 HOMO–LUMO 能隙、介电常数、折射率和玻璃化转变温度六种计算性质。以下五种性质均可选高值 Top 10%、15%、20%、25%、30%；能隙选项单列在下一节。单位 `1` 表示无量纲。

| 数据集 | 性质 | 单位 | Top 10% | Top 15% | Top 20% | Top 25% | Top 30% |
|---|---|---|---|---|---|---|---|
| `AD_TC` | 热导率 | W/(m K) | [10%](../skills/stca/assets/rule_library/entries/adept-tc-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-tc-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-tc-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-tc-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-tc-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-30/constraints.json) |
| `AD_RHO` | 密度 | g/cm3 | [10%](../skills/stca/assets/rule_library/entries/adept-density-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-density-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-density-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-density-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-density-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-density-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-density-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-density-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-density-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-density-high-30/constraints.json) |
| `AD_DC` | 介电常数 | 1 | [10%](../skills/stca/assets/rule_library/entries/adept-dc-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-dc-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-dc-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-dc-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-dc-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-30/constraints.json) |
| `AD_RI` | 折射率 | 1 | [10%](../skills/stca/assets/rule_library/entries/adept-ri-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-ri-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-ri-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-ri-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-ri-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-30/constraints.json) |
| `AD_TG` | 玻璃化转变温度 | K | [10%](../skills/stca/assets/rule_library/entries/adept-tg-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-tg-high-15/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-tg-high-20/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-tg-high-25/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-tg-high-30/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-30/constraints.json) |

## AD_GAP：作者默认规则与更多选项

`AD_GAP` 的目标是**孤立单体 HOMO–LUMO 能隙**，单位为 eV。选择 Top 10% 时，默认使用作者提供的冻结代表 `adept-gap-author-high-10`；Top 15%、20%、25%、30% 使用各自的数据集规则。

| 选项 | 百分比 | 中文 prompt | 精确约束 |
|---|---|---|---|
| 作者提供的冻结代表（默认） | Top 10% | [复制 prompt](../skills/stca/assets/rule_library/entries/adept-gap-author-high-10/prompt.zh-CN.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-author-high-10/constraints.json) |
| 数据集规则 | Top 15% | [复制 prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-15/prompt.zh-CN.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-15/constraints.json) |
| 数据集规则 | Top 20% | [复制 prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-20/prompt.zh-CN.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-20/constraints.json) |
| 数据集规则 | Top 25% | [复制 prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-25/prompt.zh-CN.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-25/constraints.json) |
| 数据集规则 | Top 30% | [复制 prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-30/prompt.zh-CN.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-30/constraints.json) |

<details>
<summary>更多选项：另一条 AD_GAP Top 10% 规则</summary>

`adept-gap-high-10` 是根据公开数据生成的另一条冻结 Top 10% 规则，目录中标为非默认选项。需要明确选择此变体时，打开以下文件：

- [Top 10% 变体中文 prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-10/prompt.zh-CN.md) · [约束 JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-10/constraints.json)

它与作者默认项具有不同的规则 ID；调用或核验时保留所选 ID 和该 prompt 中的全部条件。

</details>
