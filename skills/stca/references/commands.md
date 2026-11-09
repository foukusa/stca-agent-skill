# STCA 可执行命令

> 新数据默认先按 ECFP4／Morgan 最近邻 Tanimoto 距离划分 source、holdout 和 buffer，再仅在 source 学习；方法推荐来自 source 内 Morgan 距离验证。来源及规则目录见 [effectiveness.md](effectiveness.md)，执行见 [agent_workflows.md](agent_workflows.md)。历史结果保留其原评价协议。


## 目录

- [环境](#环境)
- [论文冻结筛选](#论文冻结筛选)
- [自动新数据流程](#自动新数据流程)
- [新数据诊断](#新数据诊断)
- [自定义拟合与评价](#自定义拟合与评价)
- [模型约束与多目标](#模型约束与多目标)
- [原始上游命令](#原始上游命令)

## 环境

本文供平台 agent 调用后端时参考。面向用户的入口是自然语言任务；无需把本页命令、Python 路径或安装步骤转交给用户。优先使用 [agent_workflows.md](agent_workflows.md) 的三个完整流程。

以当前 SKILL.md 所在目录定位资源。平台通过 `scripts/agent_runtime.py run --script <后端脚本> -- <参数>` 自动复用或准备计算环境。内部低层命令中的 `STCA_PY` 与 `STCA_SOURCE` 由平台从运行回执读取。所有输出写入新的任务目录，输入只读。 默认使用 Python 3.10 及以上的兼容后台，按所需功能检查复用现有依赖；固定历史依赖环境为显式复现选项。STCA 使用 CPU，用户无需自行选择解释器或配置 GPU。

## 论文冻结筛选

标识列可任意命名或省略；无标识生成行回执。原始星号 SMILES 返回到主结果，H-cap 自动在计算副本完成。

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --profile tg-high --protocol paper --tier 0.20 \
  --input candidates.csv --id-column CandidateKey --smiles-column SMILES \
  --output-dir out/tg_top20
```

paper profiles：Tg high 0.30/0.20/0.10；EC low 或 high 0.20/0.15/0.10/0.05。没有默认 5%。最终看 `results.csv`；审计看 `rows.csv` 和 `summary.json`。无标签不计算真实性能 Precision。

## 自动新数据流程

```bash
"$STCA_PY" "$SKILL_DIR/scripts/morgan_evaluation.py" \
  --input permeability.csv --target Permeability --unit Barrer \
  --direction high --tiers 0.10 0.15 0.20 0.25 0.30 \
  --smiles-column SMILES --structure-kind polymer_repeat_unit \
  --distance-threshold 0.5 --output-dir out/permeability_morgan
```

结构先划分，所有依赖标签的数据准备和规则拟合仅使用source；source内部Morgan距离验证确定方法推荐。每条外部holdout到source的最近邻Tanimoto距离至少0.5，buffer单独保留，不参与拟合和外评。默认请求的留出比例为0.2，整组保护和距离约束可能改变实际数量；读取 `split_audit.json`，不能假定恰好20%。

输出包括 `original_input.csv`、`split_membership.csv`、`split_audit.json`、`source_input.csv`、`holdout_input.csv`、`buffer_input.csv`、`source_fit/`、`source_inner_selection.json`、`screening_summary.json`、`holdout_metrics.json`、`morgan_holdout_evaluation.csv`、`all_rows_screening.csv` 及每方法模型/逐档筛选/约束。`--already-log` 明确声明已log输入；`--wracc-max-literals` 可取auto、正整数或unlimited。自然语言用户不需填写这些命令。

距离划分不可用时保留失败状态，不静默改用随机或t-SNE。下列显式角色与旧协议接口仍可在用户明确要求时使用。

## 新数据诊断

先在 JSON 中或自然语言确认列、单位和数据角色。诊断只读 source 决定 transform/网格，外评只报告目标支持量。

```bash
"$STCA_PY" "$SKILL_DIR/scripts/data_readiness.py" \
  --input measured.csv --target Permeability --unit Barrer --direction high \
  --tiers 0.30,0.20,0.10 --role-column Role --source-value source \
  --evaluation-value holdout --smiles-column SMILES \
  --transform auto --output out/readiness.json
```

已是 log 输入必须声明 `--already-log`，并给出真实的 log 单位。处理历史、重复冲突和 outlier 标记默认不触发删除或聚合。某 tier 外评只有 0–1 正例不阻止筛选，但不能给出可靠的外推能力结论。

## 自定义拟合与评价

输入示例：

```csv
CandidateKey,SMILES,Permeability,Role,InnerRole
obs-a,*CC*,10,source,train
obs-b,*CO*,100,source,validation
obs-c,*CF*,25,holdout,
```

示例仅说明字段，三条记录不足以训练真实规则。`Role` 决定 source/holdout，`InnerRole` 只在 nested 选择时使用；ID 不自动定义材料身份。真实结构不能跨 source/holdout 而声称独立。

```bash
"$STCA_PY" "$SKILL_DIR/scripts/custom_fit.py" --structure-kind polymer_repeat_unit \
  --input measured.csv --smiles-column SMILES \
  --target Permeability --unit Barrer --direction high --tiers 0.30,0.20,0.10 \
  --role-column Role --source-value source --evaluation-value holdout \
  --transform auto --scan-policy fixed --min-subset-size 1 \
  --output-dir out/permeability_fit
```

用户请求 source-only nested 适配时，改用：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/custom_fit.py" --structure-kind polymer_repeat_unit \
  --input measured.csv --smiles-column SMILES \
  --target Permeability --unit Barrer --direction high --tiers 0.30,0.20,0.10 \
  --role-column Role --source-value source --evaluation-value holdout \
  --inner-role-column InnerRole --inner-train-value train \
  --inner-validation-value validation --scan-policy nested --transform auto \
  --output-dir out/permeability_nested
```

nested 必须显式 source 内角色，不能从外评标签调参。固定扫描可显式 `--scan-step`；步长与 min subset 写入合同。自定义 generic STCA 与命名 Tg/EC `source_locked` 配方不同。

主要交付：`model.json`、`source_audit.json`、`source_settings.json`、`tier_cutoffs.csv`、`evaluation_metrics.json`、`prepared_rows.csv`、`excluded_rows.csv`、`diagnostics/` 下的完整规则家族和 `run_manifest.json`。默认变换为 none；auto 必须显式选择。`--invalid-policy error` 默认遇无效行报错；`report` 显式排除拟合无效行并保留 exclusion 表。查看状态字段区分无规则、零覆盖、有限支持和运行异常；拟合失败写 `failure.json`，不能将异常转成 0 分。源空间变换为 log 时 cutoff 表同时含物理单位阈值。

对同性质新来源的标签，复用已经冻结的模型和保存的 transform：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/evaluate_custom.py" \
  --model out/permeability_fit/model.json --input independent.csv \
  --target Permeability --property Permeability --unit Barrer \
  --smiles-column SMILES --cutoff-mode fixed_train \
  --output-dir out/independent_evaluation
```

`--target` 是新表标签列，`--property` 与 `--unit` 必须匹配保存的目标身份和输入单位。不重训；输出 `rows.csv`、原始结构主表 `results.csv`、`evaluation_metrics.json`。`--cutoff-mode dataset_relative` 需显式声明，并报告重定义的 cutoff。目标不足只标状态，不把无定义 MCC/Recall 写成 0。

## 模型约束与多目标

自定义模型直接通过 `--model` 调用；不附一个与其不符的 `--protocol paper`。

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --model out/permeability_fit/model.json --tier 0.20 \
  --input candidates.csv --smiles-column SMILES \
  --output-dir out/permeability_candidates

"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" export-rules \
  --model out/permeability_fit/model.json --tier 0.20 \
  --output-dir out/permeability_constraints
```

目标 JSON（模型路径相对 JSON 所在目录）：

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "CandidateKey",
  "smiles_column": "SMILES",
  "hcap_before_maccs": true,
  "objectives": [
    {"property": "Tg", "direction": "high", "tier": 0.20},
    {"name": "permeability", "property": "Permeability", "direction": "high", "tier": 0.20,
     "unit": "Barrer", "model": "out/permeability_fit/model.json"}
  ]
}
```

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" plan-objectives \
  --objectives objectives.json --output-dir out/plan
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" joint-screen \
  --input candidates.csv --config out/plan/joint_config.json \
  --output-dir out/joint
```

`plan-objectives` 每项显式 tier。数值 cutoff 可另作评价/说明，不能用“最近论文阈值”偷偷替用户选 tier。跨性质 paper 迁移必须显式 `allow_transfer:true` 并在输出标注；新性质优先使用该性质自己的模型。不同模型方向、单位、target 身份应校验。

## 原始上游命令

论文精确复现、MACCS 矩阵和现有命名训练配方仍可用 `stca_runtime.py run -- <原命令>`。例：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run --   profiles --protocol paper
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" run --   train-profile --profile tg-high --protocol source_locked \
  --input tg_source.csv --target Tg --tg-unit degC --output-dir out/tg_source_fit
```

paper 重建保留原数据角色及参数，selection 标签参与选优时必须承认。不要因为 source-only 赢者不同便报告原 paper 复现失败。普通二值列显式输入 `train --features ...`，绝不当作 MACCS 自动解释；用户 ID/role/目标列不可作为特征。
