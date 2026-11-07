---
name: stca
description: "Use Sliding Threshold Correlation Analysis (STCA) to apply published polymer substructure rules, derive new readable rule families from user-supplied measured data with explicit percentage thresholds, and verify rule-guided repeat-unit candidates. Trigger on STCA、滑动阈值相关分析、聚合物子结构筛选、规则提取、多性能筛选、候选设计、生成约束."
---

# STCA 聚合物筛选

把聚合物重复单元结构、实测性能和设计目标转换为可执行的 STCA 工作流。宿主智能体负责理解任务、组织文件和解释结果；固定版本的 `polymer-stca` 实现负责阈值扫描、子结构排序、前缀规则家族构建、冻结筛选和评价。

## 1. 先区分两种模式

### 已发表规则模式

使用论文已经冻结的规则。规则来源保留论文中**基于 ECFP2 的 interpolation／extrapolation 划分**。把已发表规则应用到新的候选表时：

- 不重新训练规则；
- 不重新划分候选表；
- 明确指定 profile 和百分位档位；
- 输出逐候选通过状态和失败条件。

### 自定义数据模式

在用户自己的实测数据上重新提取规则。用户必须明确提供：

- 性质与单位；
- 目标方向或 EC regime；
- 一个或多个百分位阈值；
- 需要独立评价时的 source／evaluation 数据角色。

自定义数据模式得到的是该数据集的新规则，不得称为论文冻结规则或论文 ECFP2 划分复现。随机行 ID 只用于记录追踪，不用于定义数据角色。

## 2. 识别用户要做什么

| 用户需求 | 执行工作流 |
| --- | --- |
| 用论文结论筛选新的重复单元 | 使用已发表规则模式，H-cap 后计算 MACCS，输出逐候选通过状态与失败条件 |
| 在自己的实测数据上重新归纳规则 | 使用自定义数据模式，按用户明确的百分位阈值提取完整规则家族并冻结代表规则 |
| 组合多个性能要求 | 为每个目标分别指定 profile、方向和百分位档位，再在同一候选表逐项筛选并取交集 |
| 用规则指导候选设计 | 导出精确结构约束，由宿主提出候选，再进行 H-cap、MACCS 和冻结规则核验 |
| 复现论文规则 | 使用 `paper` 协议及论文原数据角色；不得用任意新划分替代论文 ECFP2 划分后仍称复现 |

用户没有给出百分位档位时，不要静默选择“标准”或“严格”等默认档位。应列出该 profile 可用的明确百分位，等待用户选择；若用户已经给出绝对数值 cutoff，只有在明确报告映射依据时才能映射到最近的论文档位。

## 3. 已发表 profile 与百分位

| profile | 含义 | 已发表档位 |
| --- | --- | --- |
| `tg-high` | 高 Tg 分支 | 0.30、0.20、0.10 |
| `ec-low` | 低 EC／绝缘 regime | 0.20、0.15、0.10、0.05 |
| `ec-high` | 高 EC／导电 regime | 0.20、0.15、0.10、0.05 |

在已发表 profile 中，Tg 只有高性能分支。`high / low` 的双向区分主要用于 EC：`ec-low` 是绝缘，`ec-high` 是导电。百分位档位是单独参数；5% 不是默认值。

多性能 objective 写成：

```text
property + direction + explicit tier
```

例如：

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "CandidateKey",
  "smiles_column": "SMILES",
  "hcap_before_maccs": true,
  "objectives": [
    {"property": "Tg", "direction": "high", "tier": 0.20},
    {"property": "EC", "direction": "low", "tier": 0.10}
  ]
}
```

使用：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" plan-objectives \
  --objectives objectives.json \
  --output-dir out/objective-plan
```

不要把不同性质放到同一个全局档位，也不要用 `broad / standard / strict / extreme` 代替论文百分位。

## 4. 准备运行环境

令 `SKILL_DIR` 为当前 `SKILL.md` 所在目录。优先使用 CPython 3.12 创建独立环境：

```bash
python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" --env-dir "$STCA_ENV_DIR"
```

从输出 JSON 读取 `python` 作为 `STCA_PY`，读取 `source` 并设置 `STCA_SOURCE`。已有兼容环境时可以复用。运行命令与平台说明见：

- [commands.md](references/commands.md)
- [platform-runtime.md](references/platform-runtime.md)
- [platforms.md](references/platforms.md)

源码或依赖不可用时，明确说明缺少项；不要临时重写相关性算法代替 STCA。

## 5. 准备候选结构

- 标识列可任意命名，也可以省略；不要求 `PID`。
- 标识只用于追踪记录，不进入 MACCS 或 STCA。
- 保留原始带 `*` 的重复单元 SMILES，并把它作为最终结果中的权威结构。
- 对末端单键 `*` 建立独立的 H-cap 计算副本；不要覆盖原始结构，也不要从 H-cap 结果反推连接点。
- 在 H-cap 结构上计算 167 位 RDKit MACCS，保留 K0 占位。
- 无效结构保留错误状态，不填成全零指纹。

优先使用 `stca_tools.py screen-candidates` 处理单一冻结规则。输出：

- `results.csv`：面向用户的主结果，显示原始带 `*` 的重复单元；
- `rows.csv`：审计结果，另含 H-cap 计算结构和表示信息。

## 6. 准备自定义实测数据

确认：结构列、目标列、单位、百分位阈值和数据角色。行标识可任意命名或省略，但不会自动成为划分变量。

- 用户已经给出 source／evaluation 角色时，严格使用并审计角色重叠。
- 用户只要求在全量数据上归纳规则时，明确说明没有独立外部评价。
- 用户要求复现论文时，只能使用论文原始 ECFP2 划分角色；任意新划分属于自定义分析。

用 `audit_dataset.py` 检查无效结构、重复测量、角色重叠和冲突记录。保留原始数据，所有转换另存文件。

EC 支持 `S/m`、`S/cm`、`log10(S/m)` 和 `log10(S/cm)`；Tg/Tm/Td 明确 degC 或 K；TC 明确 W/(m·K)；ε-AC 为无量纲。不同单位不得直接混用。

## 7. 提取、冻结和应用规则

用 `stca_runtime.py run -- <上游命令>` 调用固定版本的 STCA 核心。

STCA 执行：

1. 沿明确百分位对应的性能阈值扫描子集；
2. 计算阈值与子结构频率轨迹的 Pearson 相关性；
3. 分别排序正向和负向子结构；
4. 按排名前缀形成纯正、纯负和混合 AND 规则家族；
5. 按声明模式确定代表规则；
6. 冻结后筛选候选或评价 evaluation 数据。

保留完整规则家族、代表规则、实际 cutoff、单位、百分位、数据角色和规则来源。不要因结果不理想而临时改变规则结构或百分位。

## 8. 多性能筛选

先生成 `joint_config.json`，再在同一候选表执行：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" joint-screen \
  --input candidates.csv \
  --config out/objective-plan/joint_config.json \
  --output-dir out/multi-property-screen
```

输出逐项包含：性质、profile、direction、tier、规则来源、单项通过状态、失败条件和最终交集。`results.csv` 显示原始结构；`rows.csv` 保留计算副本。

联合筛选是“同一候选同时满足多条结构规则”。若要评价真实性能的联合命中率，必须提供同一材料、可比条件下的配对多性能标签。

## 9. 规则引导候选设计

用 `export-rules` 导出规则 JSON 与 prompt。宿主智能体按照用户给定的候选数量、允许元素、结构范围和明确百分位目标提出候选。随后：

1. 保留全部原始提案；
2. H-cap 并检查结构有效性；
3. 计算 MACCS；
4. 应用每条冻结规则；
5. 输出通过、未通过和失败原因；
6. 对多目标计算同候选交集。

候选数量不足时，在用户预算内继续生成或如实返回不足；不要修改冻结规则来凑数量。

## 10. 评价和交付

有真实标签时输出：TP、FP、TN、FN、Precision、Recall、F1、MCC、coverage、enrichment factor、样本数、数值 cutoff、百分位和单位。没有标签时只报告结构规则筛选结果。

最终交付：

- 数据审计；
- 阈值轨迹和子结构排名；
- 完整规则家族与冻结模型；
- 候选筛选表；
- 多性能 objective plan 与交集结果；
- 可用于候选设计的约束；
- 运行记录和版本信息。

先说明用户得到什么，再解释主要规则和结果；技术验证、环境细节和历史复现记录放入附件，不堆在结果开头。

## 包内资源

- `scripts/stca_runtime.py`：调用固定 STCA 实现。
- `scripts/setup_locked_environment.py`：准备运行环境。
- `scripts/prepare_hcap.py`：生成 H-cap 计算列。
- `scripts/audit_dataset.py`：数据与角色审计。
- `scripts/stca_tools.py`：目标规划、规则导出和多性能筛选。
- `references/algorithm.md`：算法、profile 与百分位。
- `references/commands.md`：命令与输入输出示例。
- `references/validation.md`：验证记录。
- `assets/objectives_example.json`：多性能目标示例。
