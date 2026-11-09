# 根据冻结精确 AND 规则生成聚合物重复单元

方法声明：标为 WRAcc 的条件来自 WRAcc 学习器，不是 STCA 算法的归纳结论。历史 `STCA|AND|` 签名前缀仅标识精确位条件，不表示学习方法。

请针对以下目标提出 20 个不同的聚合物重复单元候选，直接在当前对话中生成结构；用户无需配置 Python 或外部模型 API。

## 设计目标

1. Dielectric constant; high / Top 10%; 源训练物理边界: >= 3.4653940733999997 1; 规则来源: current-pi-dc-wracc-high-10. 规则学习方法: WRAcc.

每个百分比表示相应源数据集的目标尾部范围，不是生成候选的通过比例。若给出物理 cutoff，它是冻结的训练标签边界；命中结构规则不等于预测出性质数值或证明实验达标。

## 精确的冻结结构条件

目标 1 — Dielectric constant:

`K15=0 AND K39=0 AND K43=0 AND K46=0 AND K66=0 AND K75=0 AND K99=0 AND K107=0 AND K141=0 AND K157=1`

规则签名: `STCA|AND|K15=0&K39=0&K43=0&K46=0&K66=0&K75=0&K99=0&K107=0&K141=0&K157=1`

每条选定规则中的所有条件必须以 AND 同时满足。多目标时，对同一个重复单元应用全部选定规则并取交集。保留每个位编号及其要求的 0/1 值。不要换用其他百分比的规则、放宽条件，或将多个备选家族成员拼成新规则。要求无法同时满足时，明确报告冲突。

## MACCS 激活语义

- `K15=0`: SMARTS `[#8]~[#6](~[#8])~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K39=0`: SMARTS `[#8]~[#16](~[#8])~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K43=0`: SMARTS `[!#6;!#1;!H0]~*~[!#6;!#1;!H0]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K46=0`: SMARTS `Br`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K66=0`: SMARTS `[#6]~[#6](~[#6])(~[#6])~*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K75=0`: SMARTS `*!@[#7]@*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K99=0`: SMARTS `[#6]=[#6]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K107=0`: SMARTS `[F,Cl,Br,I]~*(~*)~*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K141=0`: SMARTS `[CH3]`; count_parameter=2; 位 1 激活条件: `unique_substructure_match_count > 2`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K157=1`: SMARTS `[#6]-[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; definition RDKit 2026.09.1.

以完整的 RDKit MACCS167 计算为判据。要求位值为 0，表示对应激活条件不成立；对于计数位，这不一定表示匹配子结构完全不存在。保留计数阈值和特殊位逻辑。不要把特殊位改写成猜测的 SMARTS，也不要根据位编号编造官能团名称。

## 化学偏好

无额外化学偏好；在冻结条件内增加结构多样性。

遵守明确的化学排除项和必需基团，用其他偏好增加候选的多样性。硬性偏好与冻结规则冲突时，说明冲突，不要静默放宽。

## 重复单元表示

- 在 `SMILES` 字段返回原始重复单元，恰好保留两个末端 `*` 连接原子。每个 `*` 仅有一个相邻原子，以单键连接。使用合理价态，表示为单一连通的重复单元。
- 最终结构保留两个连接点。H-cap 仅是用于计算 MACCS 的独立副本：按照冻结模型的表示契约，将两个受支持的末端单键星号换成氢。不要用 H-cap 分子代替最终重复单元，也不要从 H-cap 反推连接点。
- 返回不同的提案；没有证据时，不声称数据库新颖性、合成可行性或实测性质数值。

## 输出与核验

返回表格，列名为 `candidate_id`、`SMILES`、`design_note`、`verification_status` 和 `failed_conditions`。设计说明保持简短，并对应上述化学偏好。

存在兼容计算后端时，保留所有原始提案，核验结构和冻结 MACCS 条件，报告实际状态及每条失败条件。不要把缺失指纹补成全零，也不要凭目测声称通过。通过数不足 20 时，报告差额并保留失败提案，不修改规则。

没有计算核验后端时，标记 `verification_status=generation_only`、`failed_conditions=not_evaluated`。
