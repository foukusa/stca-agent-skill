# STCA 命令与数据合同

## 目录

- [环境](#环境)
- [标识列、分组键与 H-cap](#标识列分组键与-h-cap)
- [1. 审计数据](#1-审计数据)
- [2. 应用论文预置规则](#2-应用论文预置规则)
- [3. 新测量数据的源内拟合](#3-新测量数据的源内拟合)
- [4. 自定义二值输入](#4-自定义二值输入)
- [5. 冻结评价](#5-冻结评价)
- [6. 精确约束及 prompt 导出](#6-精确约束及-prompt-导出)
- [7. 自动规划并执行多性能筛选](#7-自动规划并执行多性能筛选)
- [8. 原始研究结果重建](#8-原始研究结果重建)

## 环境

把 `SKILL_DIR` 设置为当前技能目录。发行版使用 CPython 3.12 建立隔离环境：

```bash
export SKILL_DIR="/absolute/path/to/stca"
export STCA_ENV_DIR="$HOME/.venvs/stca-0.1.0"

python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR" > stca-setup.json

STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"

"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" doctor
```

Linux x86_64 默认使用带 wheel SHA256 的锁定文件；其他系统使用精确版本快照并需在实际设备上验证。已有兼容源码时，可向安装器传入 `--source /absolute/clean/checkout`。输出始终写入用户工作目录，不写进 skill 安装目录。

## 标识列、分组键与 H-cap

### 标识列

- 不要求 `PID`。
- 可以使用 `ID`、`CandidateKey`、`RecordName`、`SampleCode` 等任意列名和任意文本值。
- 标识仅用于追踪记录，不作为 MACCS 或 STCA 特征。
- 候选筛选时，提供的标识应非空且唯一。
- 不提供标识列时，`screen-candidates`／`joint-screen` 自动生成 `row-000001` 形式的运行回执 ID。

### 分组键

随机行 ID 不等于材料分组键。需要防止划分泄漏时，`--group-column` 应指向 canonical 重复单元、真实材料身份或其他有科学意义的分组。没有可信分组键时，应使用预先固定且经过结构重叠审计的 split 列，而不是把随机 ID 当作材料身份。

### H-cap

原始带 `*` 结构始终保留。H-cap 只建立计算副本：

```text
原始 SMILES → 临时 H-cap → MACCS/STCA → 主结果恢复显示原始 SMILES
```

不是从 H-cap 分子逆推出星号，而是始终保留原始输入。`results.csv` 是主结果；`rows.csv` 保存 H-cap 审计列。

需要单独生成 H-cap 文件时：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/prepare_hcap.py" \
  --input candidates.csv \
  --output candidates_hcap.csv \
  --smiles-column SMILES \
  --output-column stca_calculation_smiles_hcap \
  --id-column CandidateKey
```

`--id-column` 可省略。该命令不覆盖原输入，也不会删除原始结构列。

## 1. 审计数据

标识列是可选的，列名任意：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/audit_dataset.py" \
  --input source.csv \
  --test holdout.csv \
  --id-column RecordKey \
  --smiles-column SMILES \
  --target Tg \
  --output data_audit.json
```

没有标识列时删除 `--id-column RecordKey`；审计器会生成仅用于回执的行 ID，并且不会据此判断跨集 ID 重叠。它仍会检查 canonical 结构重叠。

训练中使用 selection 数据时加 `--selection-input selection.csv`。二值矩阵加 `--features aromatic,ether,carbonyl`，并保证所有数据使用相同特征含义和列序。重复测量不应仅因标签不同而被删除；应保留测量条件和冲突证据。

## 2. 应用论文预置规则

### 推荐：直接筛选原始带星号候选

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --profile ec-low \
  --protocol paper \
  --tier 0.05 \
  --input candidates.csv \
  --id-column CandidateKey \
  --smiles-column SMILES \
  --output-dir ec_low_05
```

无标识列时删除 `--id-column CandidateKey`。输出：

- `results.csv`：用户主结果，保留原始带 `*` 的 SMILES；
- `rows.csv`：完整审计表，另含 H-cap 计算结构；
- `summary.json`：规则、数量、输入表示与运行信息；
- `joint_constraints.json`：本次冻结结构条件。

### 高级：输入已经是训练表示

如果输入已明确是 H-cap 表示，可以加 `--input-is-hcap`。只有在输入契约已经核实时才使用；不能因为原档案没有星号就默认新候选也无需 H-cap。

预置 `tg-high` 的 tier 为 0.30/0.20/0.10；`ec-low` 与 `ec-high` 为 0.20/0.15/0.10/0.05。不要插值未支持档位。

## 3. 新测量数据的源内拟合

`RecordKey` 可以是任意行标识；`StructureGroup` 才是有科学意义的划分分组：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  train-profile --profile tg-high --protocol source_locked \
  --input tg_source.csv --target Tg --tg-unit degC \
  --group-column StructureGroup --output-dir tg_fit

"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  train-profile --profile ec-low --protocol source_locked \
  --input ec_source.csv --target EC --ec-input-unit 'S/m' \
  --group-column StructureGroup --output-dir ec_fit
```

如果用户已经提供固定 `split` 列且上游命令支持该角色，可使用该划分并单独审计结构重叠；不要凭空生成 `PID`。EC 始终转换为 `log10(S/cm)` 后拟合。

论文历史选择重建：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  train-profile --profile ec-low --protocol paper \
  --input ec_source.csv --selection-input ec_selection.csv \
  --target EC --ec-input-unit 'log10(S/cm)' \
  --group-column StructureGroup \
  --acknowledge-selection-labels --output-dir ec_paper_refit
```

这里的 acknowledgement 表明 selection 标签参与过规则选择。继续评价时必须使用另一个真正独立的最终测试集。

## 4. 自定义二值输入

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  train --input binary_data.csv --features feature_a,feature_b,feature_c \
  --target measured_value --target-name example_property --target-unit explicit_unit \
  --direction high --tiers 0.20 --scan-mode value --scan-step 0.25 \
  --max-rank 3 --family-size 8 --split-column split \
  --group-column StructureGroup --output-dir binary_fit
```

普通二值列不能冒充 MACCS 结构位。`explicit_unit` 和 `0.25` 仅是参数示例，不是通用默认值。

## 5. 冻结评价

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  evaluate --model ec_fit/model.json --input ec_holdout.csv \
  --target EC --ec-input-unit 'S/m' --group-column StructureGroup \
  --tier 0.20 --cutoff-mode fixed_train --output ec_test_metrics.json
```

只有冻结规则的外部评价可以支持泛化判断。`paper` selection 重评和 `--allow-overlap` 结果不能称为 untouched test。无标签筛选不产生 F1/Precision。

## 6. 精确约束及 prompt 导出

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" export-rules \
  --profile ec-low --protocol paper --tier 0.10 --output-dir ec_rules
```

也可以用 `--model ec_fit/model.json` 替代 profile。输出 `rules.csv`、`constraints.json` 和 `prompt.md`。语言模型负责提出候选，结构是否符合规则必须由程序重新核验。

## 7. 自动规划并执行多性能筛选

目标文件直接引用原始重复单元列。标识列可任意命名，也可省略：

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "CandidateKey",
  "smiles_column": "SMILES",
  "hcap_before_maccs": true,
  "hcap_output_column": "stca_calculation_smiles_hcap",
  "objectives": [
    {"property": "Tg", "direction": "high", "strictness": "standard"},
    {"property": "EC", "direction": "low", "strictness": "extreme"},
    {"property": "TC", "direction": "high", "cutoff": 0.32, "unit": "W/(m·K)"}
  ]
}
```

如果没有标识列，删除 `id_column`。生成配置：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" plan-objectives \
  --objectives objectives.json \
  --output-dir objective_plan
```

执行：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" joint-screen \
  --input candidates.csv \
  --config objective_plan/joint_config.json \
  --output-dir multi_property_screen
```

`results.csv` 恢复显示原始 SMILES；`rows.csv` 包含 H-cap 计算副本。结构交集只表示同一候选同时满足各条冻结规则；真实性能联合命中仍需同一材料、可比条件下的配对多性能标签。

## 8. 原始研究结果重建

用户拥有原始研究结果包并明确要求重建时：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  verify-results --reference-dir /absolute/private/reference_archives \
  --output /absolute/work/reproduction_results
```

公开代码不包含原始测量表。不能用合成数据替代后声称完成论文复现，也不能把私有逐材料结果写入公开 skill 或外部服务。
