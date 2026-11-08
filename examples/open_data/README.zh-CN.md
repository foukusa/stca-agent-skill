# 更多应用示例

[English](README.md) · [主说明](../../README.zh-CN.md) · 版本 **0.1.0**

STCA skill 随包提供 **77 条冻结规则、154 份中英文生成 prompt**，包含全部 **13 项公开数据性质任务**的现成规则。打开[规则与 prompt 目录](../../docs/RULE_LIBRARY.zh-CN.md)即可选择；也可上传自己的性质 CSV 学习新规则，再核验 LLM 生成的候选。

所有示例均通过自然语言调用。agent 自动处理数据、后台准备、规则与 prompt 导出；计算使用 CPU，生成沿用当前宿主 LLM。

## 目录

- [查找并应用现有规则](#查找并应用现有规则)
- [气体分离膜](#气体分离膜)
- [导热与光学材料](#导热与光学材料)
- [密度与比热](#密度与比热)
- [介电材料](#介电材料)
- [孤立单体 HOMO–LUMO 能隙](#孤立单体-homolumo-能隙)
- [数据来源与字段](#数据来源与字段)
- [使用自己的数据并生成候选](#使用自己的数据并生成候选)

## 查找并应用现有规则

先让已安装的 skill 返回当前目录：

```text
列出 STCA 内置规则集，给出各自的数据集、性质、方向和可选百分比，
并告诉我筛选时需要提供什么候选文件。
```

目录包括论文规则 11 条、13 项公开数据任务各 5 档共 65 条，以及作者提供的单体能隙规则 1 条。公开任务均提供高值 Top 10%/15%/20%/25%/30% 规则。下方数据来源也可用于学习自己需要的新方向或百分比。

选中条目后，上传候选 CSV 并发送：

```text
使用我选定的规则筛选上传的 candidates.csv。
结构列为 SMILES，保留原始 * 连接点。
返回匹配候选和每条失败条件，
再给我一段使用该规则生成更多候选的完整 prompt。
```

## 气体分离膜

使用已有 CO2 渗透率规则时，只需提供新候选：

```text
列出 STCA 内置高 CO2 渗透率规则及其可选百分比。
我要按 SMILES 列筛选 candidates.csv。
选定百分比后，返回匹配结构和生成 prompt。
```

从自己的测量数据学习时：

```text
使用 STCA 从我上传的 gas.csv 学习高渗透率规则。
结构列为 SMILES，实验目标列为 CO2，单位 Barrer。
探索 Top 10%、15%、20%、25%、30%，自动准备数据并选择规则设置。
返回可复用规则、物理阈值，以及用于生成 20 个候选的完整 prompt。
```

氧气渗透率可用 `O2` 作为目标，也可将实测选择性作为独立目标。使用公开气体 CSV 时，结构列为 `Smiles`。

## 导热与光学材料

研究热导率：

```text
使用 STCA 从我上传的 thermal.csv 学习高热导率规则。
结构列为 SMILES，计算目标列为 ThermalConductivity，单位 W/(m K)。
探索 Top 10%、15%、20%、25%、30%，自动选择设置。
返回规则、可复用模型和可直接复制的生成 prompt。
```

研究光学材料：

```text
使用 STCA 从我上传的 optical.csv 学习高折射率规则。
结构列为 SMILES，计算目标列为 RefractiveIndex，单位 dimensionless。
探索 Top 10%、15%、20%、25%、30%。
返回规则和生成 prompt，再筛选我上传的 candidates.csv。
```

玻璃化转变温度可直接选择目录中的论文高 Tg 规则，也可用自己的 `Tg` 数值学习规则，并声明单位，例如 K。

## 密度与比热

可直接选用 [RadonPy 高密度规则](../../docs/RULE_LIBRARY.zh-CN.md#radonpy五种计算性质)。需要从自己的数据学习低密度规则时：

```text
使用 STCA 从我上传的 density.csv 学习低密度规则。
结构列为 SMILES，目标列为 Density，单位 g/cm3，数据来自计算。
探索 Bottom 10%、15%、20%、25%、30%，自动选择设置。
返回可复用模型，以及用于生成 20 个低密度候选的 prompt。
```

研究比热时，同一请求可改用目标 `Cp`、单位 `J/(kg K)`、方向 `high` 和自己选择的 Top 百分位。

## 介电材料

按应用选择方向：

```text
使用 STCA 从我上传的 dielectric.csv 学习低介电常数规则。
结构列为 SMILES，计算目标列为 DielectricConstant，单位 dimensionless。
探索 Bottom 10%、15%、20%、25%、30%。
返回规则、模型和可直接复制的生成 prompt。
```

高介电常数任务选择方向 `high` 和 Top 百分位。电导率规则在内置目录中单独列出。

## 孤立单体 HOMO–LUMO 能隙

ADEPT 的该目标是氢封端孤立单体的 DFT HOMO–LUMO 能隙。可先查询已有规则：

```text
列出内置单体 HOMO–LUMO 能隙规则及其百分比。
根据我选中的规则，给出用于生成 20 个重复单元的完整 prompt，
要求两个末端 * 连接点，并以 CandidateKey、SMILES 两列 CSV 返回。
```

学习自己的规则时，上传带标签 CSV，指定结构列、能隙列、单位 `eV`、方向与百分比。

## 数据来源与字段

可以将这些公开 CSV 上传给 skill，并直接使用原列名。[Dataset A](https://github.com/jsunn-y/PolymerGasMembraneML/blob/main/datasets/datasetA_imputed_all.csv)包含实验气体渗透率测量值；[RadonPy](https://github.com/RadonPy/RadonPy/blob/develop/data/PI1070.csv)提供聚合物分子模拟数据；[ADEPT / PolyGraphMT](https://github.com/sobinalosious/PolyGraphMT/tree/main/data/raw)提供 MD/DFT 计算数据。

[数据来源与字段索引](dataset_registry.csv)提供全部 **13 项性质任务**的下载链接与来源条款。

| 性质 | 数据文件 | 结构列 | 性质列 | 单位 |
|---|---|---|---|---|
| CO2 渗透率 | Dataset A：`datasetA_imputed_all.csv` | `Smiles` | `CO2` | Barrer |
| O2 渗透率 | Dataset A：`datasetA_imputed_all.csv` | `Smiles` | `O2` | Barrer |
| 热导率 | RadonPy：`PI1070.csv` | `smiles` | `thermal_conductivity` | W/(m K) |
| 折射率 | RadonPy：`PI1070.csv` | `smiles` | `refractive_index` | 无量纲 |
| 密度 | RadonPy：`PI1070.csv` | `smiles` | `density` | g/cm3 |
| 比热 | RadonPy：`PI1070.csv` | `smiles` | `Cp` | J/(kg K) |
| 介电常数 | RadonPy：`PI1070.csv` | `smiles` | `dielectric_const_dc` | 无量纲 |
| 热导率 | ADEPT：`TC_MD.csv` | `SMILES` | `TC` | W/(m K) |
| 密度 | ADEPT：`RHO_MD.csv` | `SMILES` | `RHO` | g/cm3 |
| 单体 HOMO–LUMO 能隙 | ADEPT：`BANDGAP_DFT.csv` | `SMILES` | `BANDGAP` | eV |
| 介电常数 | ADEPT：`DC_MD.csv` | `SMILES` | `DC` | 无量纲 |
| 折射率 | ADEPT：`RI_MD.csv` | `SMILES` | `RI` | 无量纲 |
| 玻璃化转变温度 | ADEPT：`TG_MD.csv` | `SMILES` | `TG` | K |

例如，上传 RadonPy 的 `PI1070.csv` 后可请求：“使用结构列 `smiles`、计算目标 `refractive_index`、单位 dimensionless，学习 Top 10%、15%、20% 的高折射率规则。”

## 使用自己的数据并生成候选

带标签 CSV 需要重复单元结构与数值性质。告诉 STCA 列名、性质单位、实验/计算标签类型、方向与所需百分比。标识列可选、名称任意；原始带星号 SMILES 会保留。

```text
对我上传的 materials.csv 使用 STCA。
结构列为 RepeatUnit，目标列为 MyProperty，单位为[我的单位]。
数值来自[实验或计算]，希望得到[high 或 low]值，百分比为[我的百分比列表]。
自动学习规则，返回可复用模型与完整生成 prompt。
```

百分比由你选择，上述列表只是示例。组合目标时，让 STCA 将分别选定或学到的规则用于同一批候选，例如高热导与低密度，每个性质独立指定百分比。

将生成 prompt 复制到当前或其他 LLM，再将其返回的候选 CSV 上传给已启用 STCA 的宿主：

```text
按我的 prompt 所用规则核验这些生成候选。
保留原始 SMILES，返回每条通过和未通过的条件，以及匹配候选。
```

已有训练/测试划分时，告诉 skill 需保留的列名与角色值。安装与三种核心流程见[主说明](../../README.zh-CN.md)。
