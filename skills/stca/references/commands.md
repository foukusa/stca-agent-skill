# STCA 可执行命令

## 目录

- [环境](#环境)
- [论文冻结筛选](#论文冻结筛选)
- [自动新数据流程](#自动新数据流程)
- [新数据诊断](#新数据诊断)
- [自定义拟合与评价](#自定义拟合与评价)
- [模型约束与多目标](#模型约束与多目标)
- [原始上游命令](#原始上游命令)

## 环境

从当前 `SKILL.md` 位置获得 `SKILL_DIR`。首次准备全新目录：

```bash
python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" --env-dir "$HOME/.venvs/stca-0.1.0" > stca-setup.json
STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"
"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" doctor
```

若已安装直接复用，不覆盖旧环境。所有输出目录/文件用新路径，输入只读。锁定源码无修改；源码已有可显式 `--source` 指定。

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
"$STCA_PY" "$SKILL_DIR/scripts/auto_screen.py" \
  --input permeability.csv --target Permeability --unit Barrer \
  --direction high --tiers 0.10,0.15,0.20,0.25,0.30 \
  --smiles-column SMILES --data-kind experimental --output-dir out/permeability_auto
```

默认自动清理、ECFP4（radius2/2048）外层及source内角色、auto目标形式与步长、nested配置选择。已有角色用 `--role-column Role --source-value source --evaluation-value holdout`；显式 `--scan-policy fixed` 可固定扫描支持量。质量过滤用 `--quality-column QC --exclude-quality-value failed`，物理范围用 `--target-min`/`--target-max`；只执行声明条件。

输出：`input_format_audit.json`、`cleaned_input.csv`、`excluded_rows.csv`、`cleaning_audit.json`、`split_membership.csv`、`split_audit.json`、`fit/model.json`、`fit/source_settings.json`、`fit/tier_cutoffs.csv`、`fit/evaluation_metrics.json`、`tier_recommendations.json`。加 `--candidates candidates.csv` 可应用源内建议档位；`--screen-tier` 指定已学习档位。

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
"$STCA_PY" "$SKILL_DIR/scripts/custom_fit.py" \
  --input measured.csv --smiles-column SMILES \
  --target Permeability --unit Barrer --direction high --tiers 0.30,0.20,0.10 \
  --role-column Role --source-value source --evaluation-value holdout \
  --transform auto --scan-policy fixed --min-subset-size 1 \
  --output-dir out/permeability_fit
```

用户请求 source-only nested 适配时，改用：

```bash
"$STCA_PY" "$SKILL_DIR/scripts/custom_fit.py" \
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
