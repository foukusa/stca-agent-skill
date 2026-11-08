# 更多应用示例

[English](README.md) · [主说明](../../README.zh-CN.md) · 版本 **0.1.0**

## 目录

- [从内置任务开始](#从内置任务开始)
- [选择规则与方法](#选择规则与方法)
- [试用简短请求](#试用简短请求)
- [数据来源与字段](#数据来源与字段)
- [学习保存并继续使用](#学习保存并继续使用)

## 从内置任务开始

启用 STCA 后发送 **“开始使用 STCA”**，选择：

1. **上传数据总结规则**：提供结构和数值性质，选择高低方向及百分比。
2. **用已有规则筛选**：上传候选表，选择内置规则或“我的规则”。
3. **用已有规则生成**：查看目录并选定规则，再选择预览确认 prompt 或直接生成。

完整处理 prompt 已内置。AI 助手读取表头，展示可选来源、百分比与方法，只补问必要信息。无需输入规则 ID 或技术命令。

## 选择规则与方法

[规则与生成 prompt 目录](../../docs/RULE_LIBRARY.zh-CN.md)包含 **12 项公开数据性质任务**：GAS 实测数据 2 项、RadonPy 计算数据 5 项、ADEPT 计算数据 5 项。这些冻结规则均针对**高值方向的 Top 10%、20%、30%**。

每个来源、性质和百分比都有 **STCA 与 WRAcc 两套可独立使用的规则**。目录标明主推方法与备选方法，可按需查看评价分数；默认选择主推，也可以改选备选。**每档选择其中一种方法，两套规则不会用 OR 合并。** 选定规则内部的条件必须同时满足。

主推方法根据按结构分组交叉验证的 AS 选择，AS 是 Precision、F1、MCC 的平均值；两种方法的 AS 差值不超过 0.02 时保留 STCA。分数描述来源数据范围内的评价表现，不代表新候选一定达到相应物性。

需要其他方向或 **15%、25%** 等百分比时，可上传合适的带标签数据学习新规则。例如：“从这份计算数据总结高折射率 Top 15%、25% 规则。”

## 试用简短请求

上传候选表后，可以直接发送：

| 目标 | 一句话开始 |
|---|---|
| 高 CO₂ 渗透率 | “用 GAS 实测数据的高 CO₂ 渗透率 Top 10% 规则，选择主推 STCA 方法，筛选这份表。” |
| 高 O₂ 渗透率 | “用 GAS 实测数据的高 O₂ 渗透率 Top 10% STCA 规则筛选候选。” |
| 高比热容 | “使用 RadonPy 的高比热容 Top 10% STCA 规则筛选我的候选。” |
| 高介电常数 | “使用 ADEPT 的高介电常数 Top 20% WRAcc 规则筛选这份表。” |

前三个案例的主推方法是 STCA；ADEPT 高介电常数案例的主推方法是 WRAcc。也可以先要求查看两种方法的分数，再选择使用哪套规则。高介电常数与低介电常数是不同目标；需要低值方向时，可使用自己的数据重新学习。

需要生成时，先发送 **“3”**。目录出现后，再选择来源、性质、百分比和方法，例如：“选择 ADEPT 高介电常数、Top 20%、WRAcc，直接生成 20 个候选并核验。”想先检查时，发送“生成前先给我看完整 prompt”，可以修改后再回复“确认，开始生成”。两种方式都由当前 LLM 实际生成候选。

## 数据来源与字段

原始来源为 [Dataset A](https://github.com/jsunn-y/PolymerGasMembraneML/blob/main/datasets/datasetA_imputed_all.csv)、[RadonPy PI1070](https://github.com/RadonPy/RadonPy/blob/develop/data/PI1070.csv) 与 [ADEPT / PolyGraphMT](https://github.com/sobinalosious/PolyGraphMT/tree/main/data/raw)。GAS 规则使用 `CO2`、`O2` 列的实测值，排除缺失值，不使用插补值替代。RadonPy 标签来自分子模拟；ADEPT 除单体能隙来自 DFT 外，其余标签来自 MD。

上传这些来源文件时，可保留原始列名：

| 性质 | 数据文件 | 结构列 | 性质列 | 单位 |
|---|---|---|---|---|
| CO₂ 渗透率 | Dataset A：`datasetA_imputed_all.csv` | `Smiles` | `CO2` | Barrer |
| O₂ 渗透率 | Dataset A：`datasetA_imputed_all.csv` | `Smiles` | `O2` | Barrer |
| 热导率 | RadonPy：`PI1070.csv` | `smiles` | `thermal_conductivity` | W/(m K) |
| 折射率 | RadonPy：`PI1070.csv` | `smiles` | `refractive_index` | 无量纲 |
| 密度 | RadonPy：`PI1070.csv` | `smiles` | `density` | g/cm³ |
| 比热容 | RadonPy：`PI1070.csv` | `smiles` | `Cp` | J/(kg K) |
| 介电常数 | RadonPy：`PI1070.csv` | `smiles` | `dielectric_const_dc` | 无量纲 |
| 热导率 | ADEPT：`TC_MD.csv` | `SMILES` | `TC` | W/(m K) |
| 密度 | ADEPT：`RHO_MD.csv` | `SMILES` | `RHO` | g/cm³ |
| 孤立单体 HOMO–LUMO 能隙 | ADEPT：`BANDGAP_DFT.csv` | `SMILES` | `BANDGAP` | eV |
| 介电常数 | ADEPT：`DC_MD.csv` | `SMILES` | `DC` | 无量纲 |
| 折射率 | ADEPT：`RI_MD.csv` | `SMILES` | `RI` | 无量纲 |

ADEPT 能隙指氢封端孤立单体的 DFT HOMO–LUMO 能隙。[来源与字段索引](dataset_registry.csv)提供来源链接与许可说明，使用数据时请引用原始来源。ADEPT 来源仓库未提供明确的再分发许可，因此本包不附带其逐条数据。

自己的学习数据需要结构和数值性质；单位、实验或计算来源及已有划分等信息，可在需要时补充。标识列可省略或任意命名。仅筛选候选时只需结构，不要求提供性质标签。

## 学习保存并继续使用

总结完成后，STCA 返回规则、物理阈值，以及**每种方法在每个请求档位的独立筛选结果**。默认筛选原始上传表；如果另传独立候选表，会将该候选表的筛选结果另列。

各筛选表保留原始带星号 SMILES 和标识，包含入选判断、每条失败条件及无法计算记录。某种方法或档位没有有效规则时，仍返回状态与原因，不用空条件表示全部通过。

模型、规则及完整中英文生成 prompt 自动保存到**“我的规则”**。STCA 显示保存名称并返回主菜单，随后可选 **2** 或 **3** 复用。输入“返回主菜单”或“上一级”会保留规则。换会话或平台时，下载规则包并上传到新会话继续使用。

选 **3** 并选定规则后，可选**先预览，确认后生成**或**直接生成**。两种方式都返回全部提案及核验结果，包括失败条件，然后返回主菜单，无需另外配置 LLM API。需要转到其他 LLM 时，可明确请求 **“只给完整生成 prompt”**；之后上传其候选表，发送 **“按同一规则核验这些候选”**。结构规则核验与实际物性是否达标分别报告。安装步骤见[Mac 安装说明](../../docs/INSTALL.zh-CN.md)，完整对话见[自然语言使用案例](../../docs/USAGE.zh-CN.md)。
