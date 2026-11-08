# {{GENERATION_TITLE}}

请针对以下目标提出 {{COUNT}} 个不同的{{CANDIDATE_KIND}}候选，直接在当前对话中生成结构；用户无需配置 Python 或外部模型 API。

## 设计目标

{{OBJECTIVES}}

每个百分比表示相应源数据集的目标尾部范围，不是生成候选的通过比例。若给出物理 cutoff，它是冻结的训练标签边界；命中结构规则不等于预测出性质数值或证明实验达标。

## 精确的冻结结构条件

{{EXACT_AND_CONDITIONS}}

每条选定规则中的所有条件必须以 AND 同时满足。多目标时，对同一个{{STRUCTURE_SUBJECT}}应用全部选定规则并取交集。保留每个位编号及其要求的 0/1 值。不要换用其他百分比的规则、放宽条件，或将多个备选家族成员拼成新规则。要求无法同时满足时，明确报告冲突。

## MACCS 激活语义

{{MACCS_LITERAL_SEMANTICS}}

以完整的 RDKit MACCS167 计算为判据。要求位值为 0，表示对应激活条件不成立；对于计数位，这不一定表示匹配子结构完全不存在。保留计数阈值和特殊位逻辑。不要把特殊位改写成猜测的 SMARTS，也不要根据位编号编造官能团名称。

## 化学偏好

{{CHEMICAL_PREFERENCES}}

遵守明确的化学排除项和必需基团，用其他偏好增加候选的多样性。硬性偏好与冻结规则冲突时，说明冲突，不要静默放宽。

{{STRUCTURE_REPRESENTATION}}

## 输出与核验

返回表格，列名为 `candidate_id`、`SMILES`、`design_note`、`verification_status` 和 `failed_conditions`。设计说明保持简短，并对应上述化学偏好。

存在兼容计算后端时，保留所有原始提案，核验结构和冻结 MACCS 条件，报告实际状态及每条失败条件。不要把缺失指纹补成全零，也不要凭目测声称通过。通过数不足 {{COUNT}} 时，报告差额并保留失败提案，不修改规则。

没有计算核验后端时，标记 `verification_status=generation_only`、`failed_conditions=not_evaluated`。
