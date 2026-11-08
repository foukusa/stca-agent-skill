# 规则指导的宿主 LLM 生成

本工作流使用当前宿主 LLM 提出新聚合物重复单元。skill 提供冻结规则、生成 prompt 和可用时的计算核验；用户通过自然语言调用，agent 自动准备所需后台；使用当前宿主 LLM，不要求用户配置 Python、GPU、模型 API 或自行部署大模型。

## 选定规则

1. 用户选择内置数据集时，读取实际规则 catalog 中的该条目，确认真实目标名、方向、支持的百分比及规则文件。内置来源可以是论文冻结结论，也可以是明确标注的自定义数据规则；不要互相冒称。
2. 用户上传数据时，由 skill 执行自动数据工作流；随后 agent 对各有效请求档位自动导出 `constraints.json` 和完整双语生成 prompt，随模型一并交付。如允许探索多个档位，保留全部结果与源内建议；不要用看过的外评成绩挑一条再冒称预先选定。
3. 用户已经提供规则 JSON 时，先检查目标、单位、表示契约和完整性。对 `stca-constraints-v1`，只有 `status=frozen_representative` 且 `rule` 非空时才能按冻结结构条件生成。`no_valid_rule` 必须如实交付，不能把空条件当作所有候选通过。
4. 每个目标分别选择档位。`high` 对应 Top，`low` 对应 Bottom；百分比为 `100 * tier_fraction`。规则名称中的 `Top1_positive` 等前缀数量不是目标百分比。档位不存在时列出实际支持值，不插值、不默认 5%。

目标与规则须属于同一性质。跨性质迁移需要用户明确选择，目标段必须标出源性质与 transfer hypothesis；源性质 cutoff 不能改名成目标性质 cutoff。未知目标或只有未定义二值特征映射时，不编造化学生成约束。

## 填写可直接使用的 prompt

使用 [generation_prompt.py](../scripts/generation_prompt.py) 的 `render_prompt(constraints, language='zh-CN', count=20, preferences='') -> str`，把单条约束 dict 或多条 dict 的列表渲染为完整 prompt。支持 `stca-constraints-v1` 和 `stca-library-constraints-v1`；列表表示所有规则的 AND 交集，矛盾位条件会被拒绝。渲染只依赖标准库，不运行生成模型或科学计算。

`stca_tools.py export-rules` 对已确认 H-cap MACCS 契约的有效规则直接输出 `prompt.en.md`、`prompt.zh-CN.md`，`prompt.md` 为完整中文版。读取 `prompt_generation.json` 确认 `status=rendered`。无规则、不兼容表示或自定义二值描述符时，导出仍保留规则与 JSON；`prompt.md` 仅为说明性摘要，状态为 `not_available`，不能冒称完整生成 prompt。

渲染使用 [英文模板](../assets/prompts/generate.en.md) 或 [中文模板](../assets/prompts/generate.zh-CN.md)，填好下面全部占位。根据用户语言，将完整 prompt 直接交给用户；用户要求立即生成并核验时，由当前宿主 LLM 按同一 prompt 提案，agent 连续核验并交付候选结果，不要求用户手动执行中间步骤。不要只返回文件路径、命令或让用户自行拼接 JSON。

| 占位 | 必须填写的内容 |
|---|---|
| `{{COUNT}}` | 用户要求的候选数量；未指定时使用 20，并明确这个数量。 |
| `{{OBJECTIVES}}` | 每个目标独立一项：真实名称、方向、Top/Bottom 百分比、规则来源/标识；已知时加物理 cutoff、比较符和单位。 |
| `{{EXACT_AND_CONDITIONS}}` | 每个目标的精确 `rule.expression` 和规则签名；与 `rule.keys`、`rule.values`、`literals` 逐项一致。 |
| `{{MACCS_LITERAL_SEMANTICS}}` | 所选规则涉及的 `literals[].definition`：位编号、要求值、SMARTS（若有）、准确激活条件/计数阈值或特殊位说明。 |
| `{{CHEMICAL_PREFERENCES}}` | 用户指定的必需/禁止元素、基团、骨架、柔性、复杂度等；区分硬约束与偏好。未指定时填写“无额外化学偏好；在冻结条件内增加结构多样性”。 |

目标段使用可读的具体内容，例如“目标名称；high / Top 15%；源训练物理边界 `>= 数值 单位`；规则来源与标识”。例子中的数值必须来自本次选定规则，不能沿用其他数据集。

优先使用 `target.physical_train_cutoff`、`target.physical_unit` 和 `target.label_comparison`。模型尺度 cutoff 为 `target.model_space_cutoff` 或旧字段 `reference_train_cutoff`，模型单位为 `model_space_unit` 或 `unit`。没有可靠物理逆变换时明确“物理 cutoff 未提供”，可另写模型尺度边界，不能把对数值直接标成 Barrer 等物理单位。对数输入和自动 log10 以保存的 transform/`input_already_logarithmic` 为准，不重复逆变换。低方向保留 `<=`。

核对目标元数据与模型契约、catalog 和来源是否一致。`p`、`u` 等未解释的占位、互相冲突的目标名/单位或未确认的物理含义，必须先追溯并修正模型元数据再重新导出；不要从旧 prompt 猜测或复制。特别是历史 `export_gap10/prompt.md` 的 `p/u` 不能作为真实目标。单体计算 gap 也不能改称实测聚合物体相 bandgap。

prompt 只保留生成所需的目标和结构约束。MCC、Precision、Recall、enrichment、基线比较及其他性能报告另行交付，不放进生成 prompt。需要交代可用性时，在 prompt 外用一句话说明证据状态。

## 保留准确 MACCS 语义

按导出 JSON 保留每个实际激活定义。普通键的 SMARTS 和 `count_parameter` 共同定义激活：阈值为零时存在匹配即可；正计数阈值按导出的严格 `unique_substructure_match_count > n` 表达。需要 0 的计数键表示该阈值未达到，不等于禁止所有匹配。

`rdkit_special_or_undefined_key` 必须保留完整 MACCS 算法要求，不改写成单个 SMARTS 或推断化学名称。缺少定义时保留精确位条件并说明需要计算核验；不要自行补定义。二进制自定义描述符不是自动的 MACCS：缺少经过验证的结构到描述符映射时，只能交付二值约束，不能宣称据此生成并核验分子。

使用选定代表规则，不把 `rules.csv` 中整个候选家族都 AND 起来。多目标逐目标保留签名，对同一候选取规则交集；出现同一位同时要求 0/1 等硬冲突时，报告不可同时满足，不偷偷删除条件。

## 生成与核验

生成输出必须有原始 `SMILES`，恰好两个受支持的末端单键 `*`。最终结果始终保留连接点；H-cap 仅作为计算副本，不据此合并不同重复单元或重建连接点。新候选的两星号格式是本生成任务的表示约定，不用于改写历史源数据。

没有计算后端时，正常生成并用一句话说明 `generation_only`，不声称精确位条件已经通过。存在兼容后端时，使用冻结模型的表示和 MACCS 编号，对全部原始提案逐条核验；保存通过、失败、无效、未知状态及每个失败条件。普通筛选状态不得改写成实测性能达标。

保留初始数量、原始提案、后续修订与计算结果。不要只留下通过项来掩盖生成失败；不够用户所需数量时报告实际通过数。无需为了调用宿主 LLM 额外申请发送权限；此流程没有发送动作。
