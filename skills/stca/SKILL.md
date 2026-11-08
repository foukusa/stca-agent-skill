---
name: stca
description: "Use STCA (Sliding Threshold Correlation Analysis) for polymer structure-property data and repeat units: learn and save readable STCA/WRAcc rules from uploaded data, screen with bundled paper or validated open-data rules, or generate and verify candidates with complete rule-guided prompts. Trigger for STCA、滑动阈值相关分析、聚合物性质筛选、开源数据集规则、规则归纳、多性能交集、生成prompt、气体渗透率. Preserve the author's implementation, original polymer SMILES and repeat-unit attachment points, exact learner identity and evaluation scope."
---

# STCA skill

[内置任务](assets/starter_tasks.json) · [规则目录](assets/rule_library/index.md) · [执行流程](references/agent_workflows.md) · [使用范例](references/usage_examples.md) · [后台](references/platform-runtime.md) · [数据与评价](references/custom_data.md)

版本保持 **0.1.0**。面向聚合物结构与性质数据；用自然语言完成三条路径。用户提供目标或文件，agent 自动识别列、读取规则、准备兼容 CPU 后台并交付结果；不要求用户操作 Python、配置路径或部署生成模型。生成由当前 AI 助手完成。

面向用户介绍时，Tg/EC称为“作者STCA论文中实现的规则”，开源数据注明原始来源及STCA归纳/筛选验证。AS称为作者论文提出并在筛选评价中验证使用的综合指标。普通操作说明聚焦目标、选择、结果与继续使用；不要主动展示提交号、快照日期、审计日志或历史核验过程。只有用户明确要求严格复现或版本核对时，才按实际证据解释相应范围，不能把未运行的任务说成已经运行。筛选不匹配统一称“未满足的规则条件”。

## 自然语言开始与继续

通过当前平台的 skill 调用或 `/stca` 激活后，以当前对话完成操作。用户说“开始使用 STCA”而未说明目标时，简短介绍可从上传数据总结规则、使用已有规则筛选、按规则生成三条路径开始，并让用户用自然语言说明目标。

不假定平台存在固定编号菜单、按钮或“我的规则”页面；不要要求用户回复 1/2/3。若本次对话确实显示过编号，仍可接受数字指代。已有明确请求时直接执行；完成后交付结果并继续对话，不强制重列任务。用户要求“返回”“上一级”或“主菜单”时，保留已有文件和规则并简短重述可做的事。内部 `task_menu.py --library-dir USER_RULES_DIR` 只是任务/规则目录查询，不代表平台界面。

## 上传数据总结规则，并给出对应筛选结果

读取聚合物结构列、性质、单位、方向、实测/计算含义及可用条件。保留原始重复单元 SMILES 和原有 `*`；已封端的聚合物输入照原样读取，不凭空补连接点，也不因没有星号改变性质含义。ID 可任意命名或省略，绝不作为特征或材料身份。只补问无法可靠确定的科学信息。

学习和生成由 agent 明确选用 `--structure-kind polymer_repeat_unit`，随模型保存，避免把无星号的聚合物输入误判为其他生成任务；不要求用户填写参数。生成新候选时使用带两个末端单键连接点的聚合物重复单元表示。已有规则按其原性质和来源选择，单体计算能隙保留其真实标签含义。

**默认范围内分析：**没有指定 source/holdout 或固定外推协议时，通过 `agent_runtime.py run --script inrange_evaluation.py -- ARGS` 执行：透明数据准备、保护结构分组的 5 折交叉验证重复 3 次、STCA 与 WRAcc 比较、全量冻结与逐档筛选。用户可自定任意合法百分比，含 15%、25%；未指定时直接执行默认 10%、20%、30%，不为百分比再补问。每档报告 Top/Bottom、原始物理尺度阈值、>=/<= 与单位，并同时列出两方法的入选/未入选/未知数、未满足的规则条件结果表、AS与明确主推理由。读取`screening_summary.json`和`recommendation.md`交付，不能只给百分比或模型路径。实际命令与文件见 [agent_workflows.md](references/agent_workflows.md)。

每档沿用作者STCA论文定义的平均筛选评分（Average Score）：马修斯相关系数、精确率和 F1 分数的平均值，AS=(MCC+Precision+F1)/3。比较交叉验证的平均评分；WRAcc 比 STCA 高超过 0.02 才列为主推，否则保留 STCA。首次向用户报告时解释含义，不裸用“CV AS”等缩写。两种方法的精确规则和分数都交付。用户可明确只用 STCA 或 WRAcc。**主推/备选是方法选择，不是把两方法 OR 并集或 AND 相交。** RF 只在用户要求时作为预测参照，不输出规则。

自动准备包括结构/目标有效性、登记单位与尺度、明确元数据加工历史、可比重复观测处理、ECFP4 近邻与合理范围标记，以及可追踪的尾部影响诊断/隔离。保留全部原始行、字段、星号结构与处理映射。H-cap 相同不足以合并不同连接位置或测量条件。预处理后 CV 明确条件于已选清理数据及扫描制度；嵌套方法选择不能写成整个预处理流水线完全无偏。少于20正例是证据状态，不禁止学习或应用有效规则。

读取准备审计的`D3_transform`及`C1_scan`，报告实际采用的数据尺度、扫描步长及支持量，不能凭默认值声称已自适应。单位与已log含义须从文件或用户确认；参考文献、期刊和DOI不作为样品加工描述。

**有明确 holdout/外推协议：**保留用户数据角色，使用原 `auto_screen.py` / `custom_fit.py` 的 source-only 路径；变换、步长和设置只在 source 内确定，冻结后评价 holdout，不将全量标签清理或 CV 方法选择跨入该留出集。ECFP4 为 radius=2、2048 位，用于结构诊断/分组/明确要求的 t-SNE 角色；规则计算为 H-cap MACCS167。

无论哪条学习路径，默认交付**每个请求档位对应的完整筛选结果及入选表**，不要求用户另说“筛选”。原上传表全部行保留；无效结构是 unknown，缺标签但可算结构仍可应用规则，无规则和计算失败另有状态。CV 折外评价、全量回筛及可选外推结果分别保存，不能互相代替。独立候选表的结果另列。

有效规则自动导出精确约束及完整中英文生成 prompt，保存到用户工作目录下实际可写的规则目录。检查写入成功后显示真实文件名、路径和可下载规则包；不要虚构“我的规则”页面。用户可直接说“用刚才保存的规则筛选这份候选”或“按刚才的规则生成”，明确指代时接着执行。两方法各有模型/条件，不把 WRAcc 冒称 STCA 算法结果；冻结字面条件模型与完整原生训练模型保持真实类型。无有效条件不能登记为全通过规则。临时目录不承诺跨会话保留，新会话可上传规则包载入。

## 使用已有规则筛选

已有规则包含当前能读取的用户已保存规则、作者STCA论文中实现的 Tg/EC 规则及当前12项开源数据任务的全量冻结规则。公开数据来源为GAS实测气体数据、RadonPy和ADEPT计算数据，均提供STCA规则归纳与筛选验证结果，详见[来源说明](references/provenance.md)。当前开源目录提供 Top 10%、20%、30% 的 STCA 与 WRAcc 主推/备选；其他百分比可从用户数据重新归纳，不能插值或换成最近档。保留精确原条件和兼容ID；用户明确要求版本核对时读取相应来源记录。

先读取 `task_menu.py --rules --library-dir USER_RULES_DIR` 或规则目录，按来源 → 性质 → 方向/档位展示。目标已明确但未给百分比时，对实际支持的默认10%、20%、30%分别筛选，不再补问档位；缺档如实说明。默认分别返回STCA、WRAcc及每档主推，不能把方法/档位的多个结果自动AND；用户指定只用一种方法或“用推荐”时直接采用。已明确精确规则时直接执行，不重复询问。逐档显示实际物理阈值、比较符和单位。

内置条目由 `rule_library.py show ID` 读取精确条件，用 `rule_library.py screen ID ...` 核验。已保存规则用 `user_rule_library.py list/show` 读取，再用 `stca_tools.py screen-candidates` 应用对应模型和档位。无需重新训练或再上传训练数据。

用户要求“内置含氟候选示例”时，候选表为`assets/examples/quick_start_candidates.csv`；按用户指定规则实际筛选。该表只有结构，不能用于学习或评价密度性质。简短试用见[usage_examples.md](references/usage_examples.md)。

方法比较分别筛选 STCA 和 WRAcc；多性质联合筛选才将选定的不同目标规则作用于同一候选表，返回逐项判断及 AND 交集。同目标备选方法不自动相交。报告全部原始结构、未满足的规则条件、未知记录和入选表。

## 使用已有规则生成

用户要按规则生成但尚未明确目标时，先显示已保存规则及 STCA论文、GAS、RadonPy、ADEPT的简洁目录，等待选定具体目标规则；每条冻结规则自带档位及数值阈值。未指定方法时使用该档主推并明确告知，用户可改用备选。若“刚保存的规则”仍包含多个性质/档位，只补问未明确的目标选择；用户明确要求多档生成时各档独立准备、生成、核验，不将同性质不同档位合成一个AND任务。

选择完成后读取已存完整 prompt：内置用 `rule_library.py prompt ID --language zh-CN`；保存条目用其精确 constraints/prompt。数量、偏好、多目标组合用标准库 `generation_prompt.py` 渲染。prompt 标明真实方法、性质、来源、阈值、全部 AND 条件、MACCS计数及特殊键语义、H-cap计算约定、聚合物重复单元 SMILES 格式与核验要求。

规则选定后提供两种生成方式；用户已明确说“先看 prompt”或“直接生成”时按其选择执行：

1. **先查看并调整 prompt，再生成。** 展示完整 prompt，允许修改数量、化学偏好及输出要求。保存每次修改后的完整文本，等待用户明确确认最终版本，再调用当前 LLM 实际生成候选并逐条核验。展示或修改 prompt 后不得自行确认、提前生成或用等待时间代替确认。
2. **直接生成并核验。** 按所选规则、数量及偏好准备完整 prompt，立即调用当前 LLM 生成，再执行精确条件核验，无需额外确认。

通过标准库 `generation_session.py` 管理准备、修改、确认及最终 prompt；读取其 `generation_allowed` 和 `next_action` 后继续。用户说“确认，开始生成”时，要在同次操作中完成确认、当前 LLM 生成和核验，不能停在批准状态。助手本身执行生成步骤；Python 模板渲染或状态更新不算调用 LLM。修改冻结目标、阈值或位条件时须明确选择/建立新规则，保留原规则用于核验，不能静默改写原条件。

保留最终使用的完整 prompt、全部原始提案、修订、通过表及逐条未满足的规则条件，交付后继续对话。用户只要 prompt 时直接交付可复制原文。RDKit/数值库因签名、导入或执行权限失败时先尝试其他兼容环境；仍无法计算则将已生成提案标为“待核验”，保留运行错误。未执行解析不等于 SMILES 无效，也不能报告“0 条通过”或“零覆盖”；只有实际完成解析后才能统计有效/无效结构。规则匹配与实际物性达标分别报告。具体命令见 [generation.md](references/generation.md)。

## 共同约定

- 保留原始聚合物 SMILES；重复单元保留原有 `*` 连接点，H-cap只用于计算副本，MACCS167原编号及特殊/计数语义不变。不能把 K=0 一律解释为完全无该子结构。
- 输入只读、输出另存。保存来源、版本、精确方法、模型哈希、尺度与角色。用户数据和规则库不写入安装目录。
- 使用运行配置指定的原作者 STCA 实现。WRAcc 是单独的备选规则学习器。每条精确规则内部为 AND。
- 区分已有规则、零覆盖、零TP、无正例、无规则、计算错误和未定义指标。外推附录的零覆盖不用于覆盖当前全量规则的支持或CV证据。
- 首次计算由 agent 使用随包 `scripts/launch_runtime.sh`（macOS/Linux）或 `scripts/launch_runtime.ps1`（Windows）自动发现解释器，再进入 `agent_runtime.py`；优先复用成功记录并检查未激活 Conda 与常见环境，不要求用户填写路径。明确指定的路径验证失败时如实报告，不静默换用其他环境。
- 复用 Python **3.10及以上**兼容 CPU 环境；历史依赖锁仅在明确复现时使用。由 `agent_runtime.py` 自动管理后台，不给普通用户安装命令。

## 按需读取

- [agent_workflows.md](references/agent_workflows.md)：内部命令、输出和保存复用。
- [custom_data.md](references/custom_data.md)、[auto_pipeline.md](references/auto_pipeline.md)：准备、单位、分组CV与留出协议。
- [effectiveness.md](references/effectiveness.md)、[provenance.md](references/provenance.md)：当前证据与来源。
- [usage_examples.md](references/usage_examples.md)：面向用户的简短用法。
- [algorithm.md](references/algorithm.md)、[generation.md](references/generation.md)、[commands.md](references/commands.md)：原理和低层接口。
