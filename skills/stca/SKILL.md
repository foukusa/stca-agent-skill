---
name: stca
description: "Use Sliding Threshold Correlation Analysis (STCA) to screen polymer repeat units, extract readable substructure rule families from measured data, connect independent thermal and electrical objectives, and verify rule-guided candidate proposals. Trigger on STCA、滑动阈值相关分析、聚合物子结构筛选、多性能筛选、规则提取、候选设计、生成约束."
---

# STCA 聚合物筛选

把用户的聚合物结构、实测性能和设计目标转换为可执行的 STCA 工作流。宿主智能体负责理解目标和组织文件；固定版本的 STCA 实现负责阈值扫描、规则提取、冻结筛选和评价。

## 1. 先识别用户要做什么

| 用户需求 | 执行工作流 |
| --- | --- |
| 用已发表规则筛选新的重复单元 | 加载 `paper` profile，H-cap 后计算 MACCS，输出逐候选通过状态与失败条件 |
| 从新的实测数据提取规则 | 审计数据，运行滑动阈值分析，保留完整规则家族，冻结代表规则并评价留出集 |
| 组合多个性能要求 | 为每个目标单独确定性质、方向和档位，自动生成 objective plan，再在同一候选表逐项筛选并取交集 |
| 用规则指导候选设计 | 导出精确结构约束，由宿主智能体提出候选，再进行 H-cap、MACCS 和冻结规则核验 |
| 复现论文选优过程 | 使用 `paper` 协议及对应数据角色，保留论文流程与规则家族 |
| 只用源数据选规则并外部评价 | 使用 `source_locked`，先在源数据冻结，再评价独立数据 |

已知信息足够时直接执行。用户没有给出档位时，从其文字目标提取 `broad / standard / strict / extreme`；不同性能分别映射，不使用一个全局 joint tier。

## 2. 自动连接不同性能目标

先把每个目标写成独立 objective：`property + direction + tier/strictness/cutoff`。

| 目标性质 | 方向 | 使用的规则来源 |
| --- | --- | --- |
| Tg | high | `tg-high`，原生热学规则 |
| Tm、Td、TC | high | `tg-high`，Tg-derived thermal transfer |
| EC | high / low | `ec-high` / `ec-low` |
| ε-AC | high / low | 对应方向的 EC-derived electrical transfer |

每个 objective 可以使用：

- 明确 tier；
- `broad / standard / strict / extreme`；
- 绝对 cutoff 与单位，映射到最近的论文参考档位。

使用 `stca_tools.py plan-objectives` 自动生成配置：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" plan-objectives \
  --objectives objectives.json \
  --output-dir out/objective-plan
```

输出：

- `objective_plan.json`：每个目标的性质、方向、tier、规则来源与映射依据；
- `joint_config.json`：可直接交给 `joint-screen` 的同候选多规则配置。

不要把 Tm/Td/TC 当成独立预训练 profile；它们使用论文中的热学迁移关系。不要把 ε-AC 当成 EC 数值本身；它使用对应方向的电学规则迁移。若用户提供实测标签，另外按该性质自己的 cutoff 评价。

## 3. 准备运行环境

令 `SKILL_DIR` 为当前 `SKILL.md` 所在目录。优先使用 CPython 3.12 创建独立环境：

```bash
python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" --env-dir "$STCA_ENV_DIR"
```

从输出 JSON 读取 `python` 作为 `STCA_PY`，读取 `source` 并设置 `STCA_SOURCE`。已有兼容环境时可以复用。运行命令与平台说明见：

- [commands.md](references/commands.md)
- [platform-runtime.md](references/platform-runtime.md)
- [platforms.md](references/platforms.md)

源码或依赖不可用时，明确说明缺少项；不要临时重写相关性算法代替 STCA。

## 4. 准备结构和数据

### 候选 SMILES

- 标识列名称和值均可由用户任意指定；不要求 `PID`。候选表没有标识列时，筛选适配器按输入行序生成回执 ID。标识不进入模型特征。
- 保留原始重复单元 SMILES，并把它作为最终结果中的权威结构。
- 对末端单键 `*` 建立独立的 H-cap 计算副本；不要覆盖原始结构，也不要从 H-cap 结果反推连接点。
- 在 H-cap 结构上计算 167 位 RDKit MACCS，保留 K0 占位。
- 无效结构保留错误状态，不填成全零指纹。

优先使用 `stca_tools.py screen-candidates` 处理单一冻结规则。它会直接读取原始带星号结构，内部建立 H-cap 副本，并输出：

- `results.csv`：面向用户的主结果，显示原始带 `*` 的重复单元；
- `rows.csv`：完整审计结果，另含 H-cap 计算结构和表示信息。

### 实测数据

确认：可选的行标识、结构列、目标列、单位、方向、测量条件和数据角色。行标识可以任意命名或省略；它不自动等于材料分组键。构建防泄漏划分时，使用 canonical 结构、真实材料身份或其他有科学意义的独立分组变量，不能把随机行 ID 当作分组依据。用 `audit_dataset.py` 检查重复结构、重复测量、跨集重叠和冲突记录。保留原始数据，所有转换另存文件。

EC 支持 `S/m`、`S/cm`、`log10(S/m)` 和 `log10(S/cm)`；Tg/Tm/Td 明确 degC 或 K；TC 明确 W/(m·K)；ε-AC 为无量纲。不同单位不得直接混用。

## 5. 提取、冻结和应用规则

用 `stca_runtime.py run -- <上游命令>` 调用固定版本的 STCA 核心。

STCA 执行：

1. 沿性能阈值扫描子集；
2. 计算阈值与子结构频率轨迹的 Pearson 相关性；
3. 分别排序正向和负向子结构；
4. 按排名前缀形成纯正、纯负和混合 AND 规则家族；
5. 按所选协议确定代表规则；
6. 冻结后筛选候选或评价留出数据。

保留完整规则家族、代表规则、实际 cutoff、单位、协议和数据角色。不要因结果不理想而临时改变规则结构或档位。

预置 profile：

- `tg-high`：tiers 0.30、0.20、0.10；
- `ec-low`：tiers 0.20、0.15、0.10、0.05；
- `ec-high`：tiers 0.20、0.15、0.10、0.05。

## 6. 多性能筛选

先根据用户目标生成 `joint_config.json`，然后在同一候选表执行：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" joint-screen \
  --input candidates.csv \
  --config out/objective-plan/joint_config.json \
  --output-dir out/multi-property-screen
```

默认配置把 `SMILES` 视为原始重复单元，并在内部 H-cap。输出应逐项包含：目标性质、方向、tier、规则来源、单项通过状态、失败条件和最终交集。`results.csv` 显示原始结构；`rows.csv` 保留计算副本。

联合筛选是“同一候选同时满足多条结构规则”。若要评价真实性能的联合命中率，必须提供同一材料、可比条件下的配对多性能标签。

## 7. 规则引导候选设计

用 `export-rules` 导出规则 JSON 与 prompt。宿主智能体按照用户给定的候选数量、允许元素、结构范围和性能目标提出候选。随后：

1. 保留全部原始提案；
2. H-cap 并检查结构有效性；
3. 计算 MACCS；
4. 应用每条冻结规则；
5. 输出通过、未通过和失败原因；
6. 对多目标计算同候选交集。

候选数量不足时，在用户预算内继续生成或如实返回不足；不要修改冻结规则来凑数量。

## 8. 评价和交付

有真实标签时输出：TP、FP、TN、FN、Precision、Recall、F1、MCC、coverage、enrichment factor、样本数、数值 cutoff 和单位。没有标签时只报告结构规则筛选结果。

最终交付：

- 数据审计；
- 阈值轨迹和子结构排名；
- 完整规则家族与冻结模型；
- 候选筛选表；
- 多性能 objective plan 与交集结果；
- 可用于候选设计的约束；
- 运行记录和版本信息。

先说明用户得到什么，再解释主要规则和结果；技术验证、环境细节和历史复现记录放入对应附件，不堆在用户结果开头。

## 包内资源

- `scripts/stca_runtime.py`：调用固定 STCA 实现。
- `scripts/setup_locked_environment.py`：准备运行环境。
- `scripts/prepare_hcap.py`：生成 H-cap 计算列。
- `scripts/audit_dataset.py`：数据与划分审计。
- `scripts/stca_tools.py`：目标规划、规则导出和多性能筛选。
- `references/algorithm.md`：算法、迁移关系和档位。
- `references/commands.md`：命令与输入输出示例。
- `references/validation.md`：验证记录。
- `assets/objectives_example.json`：多性能目标示例。
