# STCA 命令与数据合同

## 目录

- [环境](#环境)
- [审计数据](#1-审计数据)
- [应用论文预置规则](#2-应用论文预置规则)
- [新测量数据的源内拟合](#3-新测量数据的源内拟合)
- [自定义二值输入](#4-自定义二值输入)
- [冻结评价](#5-冻结评价)
- [精确约束及-prompt-导出](#6-精确约束及-prompt-导出)
- [自动规划并执行多性能筛选](#7-自动规划并执行多性能筛选)
- [原始研究结果重建](#8-原始研究结果重建)

## 环境

把 `SKILL_DIR` 设置为当前技能目录。公开发行版首次安装用 CPython 3.12 建立全新隔离环境，`STCA_ENV_DIR` 指向一个不存在的可写目录：

```bash
python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR" > stca-setup.json
STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" doctor
```

Linux x86_64 默认使用 `assets/requirements-py312-linux-x86_64.lock` 中的版本与 wheel SHA256；其他系统使用 `assets/requirements-py312.txt` 的精确版本。只在 Linux x86_64 完成全新安装与候选验收，不能据此称 macOS/Windows 已验证。安装器可加 `--source /absolute/clean/checkout` 使用已有固定版本源码；不覆盖已有环境，也不在安装失败时更换依赖版本。已有成功输出时复用 `python` 与 `source`，不要随后调用旧 bootstrap。

原便利入口保留供已有兼容环境使用。它复用系统包并采用较宽版本条件，独立于上述锁定发行环境。运行后仍从 JSON `python` 字段取得解释器：

```bash
python3 "$SKILL_DIR/scripts/stca_runtime.py" bootstrap --chem
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" doctor
```

如果已有原始源码，用脚本全局 `--source /absolute/checkout`，该参数放在子命令前。只接受 skill 锁定版本。运行输出写到工作目录；不要放进安装目录。

## 1. 审计数据

候选表采用 UTF-8 CSV，含 `ID,SMILES`。训练/评价表再加 `Tg` 或 `EC` 等测量列。ID 始终作为标识，不作为模型特征。测量条件应保存在独立列；共同分析前明确温度、频率、测试方式等可比性。多次观测可以共享材料 ID，但候选联合筛选的 ID 必须唯一。

所有适配命令保留文本 ID 的前导零，并拒绝字段数与表头不一致的 CSV。不要绕开数据审计：保存模型的单一分组口径不能替代材料 ID 与结构两项检查。作者已确认原 STCA 使用 H-cap；无星号档案是已准备的输入，不能据此跳过带星号新候选的预处理。

对原始带星号的输入执行下列步骤，保留 `SMILES`，新增 `SMILES_hcap`。后续核心 `screen`/`train-profile`/`evaluate` 显式使用 `--smiles-column SMILES_hcap`，联合筛选配置使用 `"smiles_column": "SMILES_hcap"`。无星号行不改文本；已有 MACCS 矩阵跳过此步骤。以下其他示例中的默认 SMILES 列均指已符合模型训练表示的计算列。

```bash
"$STCA_PY" "$SKILL_DIR/scripts/prepare_hcap.py" \
  --input candidates.csv --output candidates_hcap.csv \
  --smiles-column SMILES --output-column SMILES_hcap
```

若模型是在明确的非 H-cap 表示上训练，不得套用此转换；先保留并核对该模型的输入契约。H-cap 后的表示碰撞必须报告，但不自动删除原始连接图不同的候选。

```bash
"$STCA_PY" "$SKILL_DIR/scripts/audit_dataset.py" \
  --input source.csv --test holdout.csv \
  --id-column PID --smiles-column SMILES --target Tg \
  --output data_audit.json
```

训练中使用 selection 数据时加 `--selection-input selection.csv`。二值矩阵加 `--features aromatic,ether,carbonyl`，并用同一特征含义和列序。先读审计结果；相同二值向量只说明表示重叠，不能单凭它确定原结构相同。处理确定的跨集材料/结构重叠后再作独立评价，不丢掉全部重复测量。

## 2. 应用论文预置规则

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  profiles --protocol paper
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  screen --profile ec-low --protocol paper --tier 0.10 \
  --input candidates.csv --smiles-column SMILES \
  --errors report --output ec_low_candidates.csv
```

`--errors report` 保留所有输入行，把非法 SMILES 标为无效和未知；不要把它们算作拒绝的真实负例。脚本保留原输入列及逐条规则缺失原因。预置 `tg-high` 的 tier 为 0.30/0.20/0.10，`ec-low` 与 `ec-high` 为 0.20/0.15/0.10/0.05。不要插值未支持的 tier。

## 3. 新测量数据的源内拟合

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  train-profile --profile tg-high --protocol source_locked \
  --input tg_source.csv --target Tg --tg-unit degC \
  --group-column PID --output-dir tg_fit
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  train-profile --profile ec-low --protocol source_locked \
  --input ec_source.csv --target EC --ec-input-unit 'S/m' \
  --group-column PID --output-dir ec_fit
```

输出 `model.json`、扫描表、候选家族与选择诊断、`skill_run_manifest.json`。EC 始终转换为 `log10(S/cm)` 后拟合。源数据不支持原模板深度时报告该状态；若用户要探索较小家族，再显式运行 `generic`，不能把它宣称为原 EC 主分析复现。

原论文历史选择的重建则显式调用：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  train-profile --profile ec-low --protocol paper \
  --input ec_source.csv --selection-input ec_selection.csv \
  --target EC --ec-input-unit 'log10(S/cm)' --group-column PID \
  --acknowledge-selection-labels --output-dir ec_paper_refit
```

这里的 acknowledgement 是数据参与选优的程序声明；有已授权的复现任务即可执行，不要新增一个用户审批步骤。继续评价时使用另一个真正独立的最终测试集。

## 4. 自定义二值输入

对于用户明确要求的自定义特征，使用通用源内前缀协议，保留 STCA 扫描逻辑并记录该扩展：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  train --input binary_data.csv --features feature_a,feature_b,feature_c \
  --target measured_value --target-name example_property --target-unit explicit_unit \
  --direction high --tiers 0.20 --scan-mode value --scan-step 0.25 \
  --max-rank 3 --family-size 8 --split-column split --group-column ID \
  --output-dir binary_fit
```

`explicit_unit` 与 `0.25` 仅用于展示参数，不是任意性质的默认单位/步长。`split` 必须只含 `train` 与 `test`；输入只用源标签建立规则，test 不参与排序或选择。自定义二值模型用 `screen --model ... --features ...` 应用，不能把普通二值列冒充 MACCS 直接处理 SMILES。

## 5. 冻结评价

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  evaluate --model ec_fit/model.json --input ec_holdout.csv \
  --target EC --ec-input-unit 'S/m' --group-column PID \
  --tier 0.20 --cutoff-mode fixed_train --output ec_test_metrics.json
```

Tg 评价的上游 CLI 没有 `--tg-unit`；如果输入是 K，先明确转换到 degC，保留原表，再评价。EC 评价保持显式输入单位。若设置 `--cutoff`，传模型存储单位的数值（EC 为 log10(S/cm)），而不是原始 S/m 数值。输出同时报告实际 cutoff。

只有冻结规则的外评可以支持泛化判断。`paper` 的选择集重评及 `--allow-overlap` 结果不能称作 untouched test。无标签筛选不产生 F1/Precision。

## 6. 精确约束及 prompt 导出

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" export-rules \
  --profile ec-low --protocol paper --tier 0.10 --output-dir ec_rules
```

也可用 `--model ec_fit/model.json` 替代 profile，模型内协议优先。输出 `rules.csv`、`constraints.json` 和 `prompt.md`；只执行明确 bit 定义，不从模型相关性推断因果、不把语言生成当结构检验。

生成任务继续由宿主 agent 提出候选，再执行本页数据审计与联合筛选。逐候选保留失败原因、用户要求的连接点格式和 canonical 去重记录；上游化学接口在 `stca.chemistry.maccs_from_smiles`，不是包顶层的同名函数。没有真实标签时只交付结构规则命中，不生成预测性能、联合精度或新颖性结论。

## 7. 自动规划并执行多性能筛选

先把用户目标写成独立 objective。每个 objective 有自己的性质、方向和 tier/strictness/cutoff；不同性质不共享一个固定档位。

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "ID",
  "smiles_column": "SMILES_hcap",
  "objectives": [
    {"property": "Tg", "direction": "high", "strictness": "standard"},
    {"property": "EC", "direction": "low", "strictness": "extreme"},
    {"property": "TC", "direction": "high", "cutoff": 0.32, "unit": "W/(m·K)"}
  ]
}
```

自动生成目标连接方案和 joint 配置：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" plan-objectives \
  --objectives objectives.json \
  --output-dir objective_plan
```

路由关系：

- Tg → `tg-high`；
- Tm / Td / TC → `tg-high` 的热学迁移规则；
- EC high / low → `ec-high` / `ec-low`；
- ε-AC high / low → 对应方向的 EC 迁移规则。

`plan-objectives` 支持三种指定方式：

1. 直接给 tier；
2. 给 `broad / standard / strict / extreme`；
3. 给绝对 cutoff 与单位，映射到最近的论文参考档位。

随后对同一候选表执行：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" joint-screen \
  --input candidates_hcap.csv \
  --config objective_plan/joint_config.json \
  --output-dir multi_property_screen
```

输出 `rows.csv`、`summary.json`、`joint_constraints.json` 与运行清单。每个要求都会保留用户目标性质、方向、tier、规则来源和迁移角色。结构交集表示同一候选同时满足这些冻结结构规则；真实性能的联合评价仍需同一材料、可比条件下的配对多性能标签。

若用户只要求一个目标，直接使用对应 profile 的 `screen`；objective plan 主要用于两个及以上目标的自动连接。

## 8. 原始研究结果重建

用户已有五个原始研究结果包且明确要求重建时，按上游 `docs/VERIFIED_RESULTS.md` 的文件角色调用：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run -- \
  verify-results --reference-dir /absolute/private/reference_archives \
  --output /absolute/work/reproduction_results
```

公开代码不包含这些测量表。不要让缺少原始数据阻止已授权的预置候选筛选或新数据拟合，也不要用合成数据代替后宣称完成论文复现。私有逐材料结果只交付用户，不写入技能、公开代码或外部服务。
