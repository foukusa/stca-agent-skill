# 当前公开数据与主计算范例

主计算范例使用ADEPT高单体HOMO–LUMO能隙Top30%的STCA规则。原始数据与字段见[案例配置](../assets/examples/adept_gap_case.json)；完整命令见[执行流程](agent_workflows.md)。

## 数据、表示与结果

- 文件为公开 `BANDGAP_DFT.csv`，共2,916行、2列；结构`SMILES`，目标`BANDGAP`，单位eV。
- 标签是氢封端孤立单体的DFT HOMO–LUMO能隙，不是体相聚合物带隙。
- 用H-cap计算副本的ECFP4（Morgan radius=2、2,048位）划分角色，MACCS167学习精确条件。原始SMILES与连接点保留。
- Top30%目标边界为≥11.914537535 eV；STCA全表匹配976条、未知0条。
- 独立距离外推584条：STCA选中192条、其中144条达标，精确率0.7500、召回率0.7784、F1为0.7639、MCC为0.6517。

这是当前39个开源任务中STCA外推MCC最高的一档，因此用于演示STCA的筛选、重新学习和生成。目录的训练侧自动推荐仍为WRAcc；演示明确指定STCA，不能将其改称自动主推或声称超过WRAcc。

## 支持的其他性质

现成目录还包含论文Tg/电导率，以及GAS、RadonPy、ADEPT其他性质和OpenPoly水接触角。OpenPoly只用于体现规则库支持的性质范围，保留Top10%、20%、30%两方法的规则、数值阈值和全部评价结果；不作为默认计算范例或优良效果展示。

使用已有规则只需候选结构；学习新规则需要目标列和单位；生成前选定精确规则，当前LLM提出候选后由计算工具逐条核验。主范例遵从[使用范例](usage_examples.md)，不把保存的示例结构复制为新生成。

## 数据划分

先仅按结构划分source、外部holdout及buffer。外部holdout到实际训练结构的最近邻Tanimoto距离均≥0.5；自动清理、变换、步长和支持量仅用source。source内另做Morgan验证选择方法，外部holdout只用于冻结后的评价。source内随机分组CV是范围内诊断，不是距离约束内推测试。

历史结果保留在原证据文件中，仅在用户明确要求历史核对时引用；不能替换当前 `current-*` 规则及其Morgan外推成绩。
