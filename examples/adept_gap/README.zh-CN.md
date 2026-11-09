# ADEPT 能隙：筛选、学习与生成

[English](README.md) · [返回首页](../../README.zh-CN.md)

用同一份公开数据体验 STCA 的三种用法：直接筛选、总结并保存规则，以及调用当前 LLM 按规则生成重复单元。本例选择 **STCA、高能隙 Top30%**。

## 目录

- [数据与列名](#数据与列名)
- [使用现成规则筛选](#使用现成规则筛选)
- [从数据总结规则](#从数据总结规则)
- [按规则生成](#按规则生成)
- [结果与来源](#结果与来源)

## 数据与列名

打开 [ADEPT 数据文件页](https://github.com/sobinalosious/PolyGraphMT/blob/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw/BANDGAP_DFT.csv)，点击 **Download raw file** 下载 `BANDGAP_DFT.csv`，然后上传到已安装 STCA 的对话。文件有 **2,916 条记录、2 列**；第1行是表头，第2–2917行是数据。

| 用途 | 原列名 | 位置 |
|---|---|---|
| 聚合物重复单元 | `SMILES` | A，第1列 |
| 计算能隙 | `BANDGAP` | B，第2列，eV |

这里的标签是 **DFT 计算的氢封端孤立单体 HOMO–LUMO 能隙**，不是体相聚合物带隙。保留输入中原有的 `*`；H-cap 只用于计算副本，输出使用原始重复单元。

## 使用现成规则筛选

上传数据后发送：

```text
使用 ADEPT 高孤立单体 HOMO–LUMO 能隙 Top30% 的 STCA 规则筛选这份数据，返回入选表和每条未满足的规则条件。
```

所选规则的目标边界为 **能隙 ≥11.914537535 eV**。对上述固定文件，STCA 应匹配 **976 条**，未匹配1,940条，未知0条。Top30%是性质目标的定义，不是要求恰好选中30%的候选。仅应用规则时，候选文件只需结构列。

[查看 STCA 精确条件](../../skills/stca/assets/rule_library/entries/current-ad-gap-stca-high-30/constraints.json) · [查看完整生成 prompt](generation_prompt.zh-CN.md)

## 从数据总结规则

```text
从这份 ADEPT 数据总结高孤立单体 HOMO–LUMO 能隙 Top30% 规则。结构列为 SMILES，性质列为 BANDGAP，单位 eV，使用全部数据行。返回筛选结果，与现成规则比较，并保存新规则。
```

AI 助手先按结构划分数据，再只在训练部分自动选择变换、扫描步长与支持量。两种方法分别返回规则、数值阈值、完整筛选表和外推成绩，并保存可复用规则包。同一文件和默认设置可复现对应现成规则。

学习同时返回 **STCA 与 WRAcc**，推荐由训练内部验证决定。继续本页 STCA 示例时说：

```text
选择刚保存的 Top30% STCA 规则，重新载入后再筛选同一份数据，核对每行结果是否一致。
```

## 按规则生成

直接生成：

```text
使用刚选定的 ADEPT 高能隙 Top30% STCA 规则，直接生成5个聚合物重复单元并逐条核验。
```

先预览和调整：

```text
使用同一条 STCA 规则，先展示生成5个重复单元的完整 prompt，暂不生成。
```

调整数量或结构偏好后，回复“确认，开始生成”。当前 LLM 实际提出候选，计算工具逐条核验冻结条件；最终保留全部提案、原始星号结构及未满足条件。

[五条生成提案及核验](generated_examples.csv) · [生成核验记录](generation_verification.json) · [该示例使用的完整 prompt](generation_prompt.used.zh-CN.md)

## 结果与来源

在584条独立外推记录上，STCA选中192条，其中144条达到能隙目标。留出结构到实际训练结构的最近邻 ECFP4 Tanimoto 距离均 **≥0.5**。

| 方法 | 精确率 | 召回率 | F1 | 马修斯相关系数 |
|---|---:|---:|---:|---:|
| STCA | 0.7500 | 0.7784 | 0.7639 | 0.6517 |
| WRAcc | 0.8241 | 0.8865 | 0.8542 | 0.7840 |

原表回筛匹配数分别为STCA 976条、WRAcc 1,019条，均无未知记录。原表包含训练和缓冲记录，独立外推分数只使用584条留出记录。完整三档双方法结果见 [evaluation.csv](evaluation.csv)，划分说明见[数据划分与评价](../../docs/MORGAN_EVALUATION.zh-CN.md)。结构规则核验不预测新候选的能隙数值。

来源：[PolyGraphMT 提供的 ADEPT 数据](https://github.com/sobinalosious/PolyGraphMT/tree/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw) · [ADEPT 研究](https://doi.org/10.1039/D6DD00206D)。使用时引用原始来源；原始CSV由用户从来源页下载。[机器可读案例配置](case.json)提供列绑定、规则及预期结果。
