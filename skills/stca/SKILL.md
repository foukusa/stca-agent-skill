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

## 默认计算范例：ADEPT 单体能隙

用户要体验完整计算流程时，读取[ADEPT案例配置](assets/examples/adept_gap_case.json)。使用官方 `BANDGAP_DFT.csv` 全部2,916行，结构列 `SMILES`，目标列 `BANDGAP`，单位eV。标签是氢封端孤立单体的DFT HOMO–LUMO能隙，保留这一含义。文件下载地址、表格位置和行数均在配置中，不要求用户拆表或操作Python。

主范例明确选择 `current-ad-gap-stca-high-30`，目标≥11.914537535 eV，原表匹配976条、未知0；独立Morgan留出584条，STCA精确率0.75、召回率0.778378、MCC0.651712。实际执行后读取结果再报告数字。目录由训练侧验证推荐的同档方法仍是WRAcc，示例明确指定STCA时必须保留用户选择；要求对比或使用推荐时如实提供两方法和目录推荐，不改写其身份或分数。

从同一固定文件、列绑定、百分比和默认距离协议重新学习，应得到对应当前冻结条件；保存后重新载入同一规则再筛同一输入，应逐行一致。生成读取当前选定的精确条件，由当前LLM提出本次候选，再核验并保留所有提案；不把静态案例复制为新生成。

RadonPy密度作为其他数据来源保留，用户明确选择时读取[密度配置](assets/examples/radonpy_density_case.json)。OpenPoly水接触角仅列入支持性质和现成规则目录，用于展示适用范围；不得主动推荐为主计算范例或声称其筛选质量优秀。用户选择该性质后仍可正常学习、筛选、生成，并如实交付三档双方法结果；读取[水接触角配置](assets/examples/water_contact_angle_case.json)，保留有效0°标签。

## 上传数据总结规则，并给出对应筛选结果

读取聚合物结构列、性质、单位、方向、实测/计算含义及可用条件。保留原始重复单元 SMILES 和原有 `*`；已封端的聚合物输入照原样读取，不凭空补连接点，也不因没有星号改变性质含义。ID 可任意命名或省略，绝不作为特征或材料身份。可选名称列或ID重复时，保留该原始字段，计算映射使用独立逐行标识；不将重复名称作为要求唯一的候选ID参数。只补问无法可靠确定的科学信息。

**先绑定输入列：**学习前明确文件、数据行范围、结构列、数值目标列、单位及高/低方向，并向用户简短说明实际绑定。用户已指定的列名优先；已知案例或表头含义唯一明确时自动填写并直接继续，不要求额外确认。存在多个密度/性质列、重复表头、不同温度/条件，或实测与计算标签不能区分时，先展示候选列并询问，得到选择后才学习；不能只凭数值范围猜测。程序按准确列名传入 `--smiles-column` 和必填的 `--target`，核对 `run_manifest.json` 中实际保存的列绑定，不能把“用户无需写列号”解释为程序无需目标列。

**星号与H-cap往返：**接收原始带 `*` 连接点的重复单元SMILES并保存；只在计算副本中将支持的末端单键连接点氢封端，用于MACCS指纹计算；筛选表及入选表返回保存的原始带星号SMILES。返回的星号及位置来自原始结构，不从H-cap结构反推，也不进行把氢字符替换为星号的文本操作。已封端输入按原样返回，不凭空补星号。

学习和生成由 agent 明确选用 `--structure-kind polymer_repeat_unit`，随模型保存，避免把无星号的聚合物输入误判为其他生成任务；不要求用户填写参数。生成新候选时使用带两个末端单键连接点的聚合物重复单元表示。已有规则按其原性质和来源选择，单体计算能隙保留其真实标签含义。

**固定执行入口：**不得用 agent 临时编写的学习器或直接对原始带星号结构调用 MACCS 代替本 skill 的适配流程。默认调用 `morgan_evaluation.py`，检查 `run_manifest.json` 的入口、方法身份及source指纹凭据。运行后通过 `fingerprint_contract.py --run-dir RUN_DIR` 核对 H-cap 表示和实际矩阵；缺少凭据或核对失败时报告未通过执行核验，不把手写汇总当作成功。原始数据不覆盖。交叉验证结论读取真实折外预测与分组文件，不能只复制一个均值。

**默认 Morgan 距离外推：**没有用户指定的固定数据角色时，通过 `agent_runtime.py run --script morgan_evaluation.py -- ARGS` 执行。首先只根据原始结构计算 H-cap ECFP4（Morgan radius=2、2048位），划分 source、holdout 和 buffer，逐条保证 holdout 到 source 的最近邻 Tanimoto 距离不小于默认 **0.5**；相同原始结构或相同 H-cap 副本不跨界。buffer 是为满足距离边界而隔离的结构，不计入训练或外推评分，但仍返回筛选结果。不通过全表标签、Top比例或最后分数挑选划分，不把随机分组五折、t-SNE外围留出或旧预测的事后距离分层称作严格距离外推。无法形成合格距离划分时明确报告，不静默退回随机划分。

仅使用 source 的标签做逐档准备、变换、步长、支持量和规则训练；source 内另设 Morgan 距离验证用于选择推荐方法。冻结后只评价一次外部 holdout，同一 source 数值阈值用于 source 与 holdout，不在 holdout 重算百分位或清理掉难例。保存 source 拟合的模型作为本次可复用规则，不在评价后悄悄改成全表重训模型。原上传表所有行另外返回冻结规则的逐行判断，并标注数据角色；回筛入选数不是外推指标。

用户可自定任意合法百分比，含15%、25%；未指定时直接执行默认10%、20%、30%。每档报告Top/Bottom、source产生的物理阈值、>=/<=及单位，同时返回两方法的原表入选/未入选/未知数、未满足条件表、独立holdout精确率/召回率/F1/MCC及推荐依据。读取真实 `screening_summary.json`、`recommendation.md`、划分和最近邻距离凭据交付。实际命令见[agent_workflows.md](references/agent_workflows.md)。
每档沿用作者STCA论文定义的平均筛选评分（Average Score）：马修斯相关系数、精确率和 F1 分数的平均值，AS=(MCC+Precision+F1)/3。比较 source 内 Morgan 距离验证的平均筛选评分；WRAcc 比 STCA 高超过 0.02 才列为主推，否则保留 STCA。证据不足时明确说明，不使用最终 holdout 选择赢家。首次向用户报告时解释含义，不裸用“CV AS”等缩写。两种方法的精确规则和分数都交付。用户可明确只用 STCA 或 WRAcc。**主推/备选是方法选择，不是把两方法 OR 并集或 AND 相交。** RF 只在用户要求时作为预测参照，不输出规则。

WRAcc 默认通过训练部分内部的分组验证，在 1、2、3、5、10 条及不限制条件数之间选择上限；只使用 source 或内部训练部分，最终模型在完整 source 内部重新选择。接受用户自然语言“最多 10 条条件”或“不限制条件数”，分别传 `--wracc-max-literals 10` 或 `--wracc-max-literals unlimited`；默认 `auto`，内部折数默认 3。记录实际长度、选择依据与证据不足状态，不能因看过外部评价结果而改长度。STCA 保留原作者的排序搜索设置，WRAcc 保留宽度 30 的 beam 与最小支持 5；两者都不是所有逻辑规则的穷举。无长度上限不保证更优，也不表示搜索无限运行。现成冻结规则不重新选择或改写条件。

自动准备包括结构/目标有效性、登记单位与尺度、明确元数据加工历史、可比重复观测处理、ECFP4 近邻与合理范围标记，以及可追踪的尾部影响诊断/隔离。保留全部原始行、字段、星号结构与处理映射。H-cap 相同不足以合并不同连接位置或测量条件。原 `inrange_evaluation.py` 的随机分组 CV 仅保留为 source 内部诊断或用户明确要求的范围内分析，不能代替独立 Morgan 外推。少于20正例是证据状态，不禁止学习或应用有效规则。

按每个档位读取准备审计的`D3_transform`及`C1_scan`，并读取`source_fit/run_manifest.json`的`per_tier_preparation`或单档兼容记录，报告实际采用的数据尺度、扫描步长及支持量；不能把第一个档位的设置当作全部档位设置，也不能凭默认值声称已自适应。单位与已log含义须从文件或用户确认；参考文献、期刊和DOI不作为样品加工描述。

**有明确 holdout/外推协议：**保留用户数据角色，使用原 `auto_screen.py` / `custom_fit.py` 的 source-only 路径；变换、步长和设置只在 source 内确定，冻结后评价 holdout，不将全量标签清理或 CV 方法选择跨入该留出集。ECFP4 为 radius=2、2048 位，用于结构诊断/分组/明确要求的 t-SNE 角色；规则计算为 H-cap MACCS167。

无论哪条学习路径，默认交付**每个请求档位对应的完整筛选结果及入选表**，不要求用户另说“筛选”。原上传表全部行保留；无效结构是 unknown，缺标签但可算结构仍可应用规则，无规则和计算失败另有状态。source 内部验证、原表回筛及独立 Morgan 外推结果分别保存，不能互相代替。独立候选表的结果另列。

有效规则自动导出精确约束及完整中英文生成 prompt，保存到用户工作目录下实际可写的规则目录。检查写入成功后显示真实文件名、路径和可下载规则包；不要虚构“我的规则”页面。用户可直接说“用刚才保存的规则筛选这份候选”或“按刚才的规则生成”，明确指代时接着执行。两方法各有模型/条件，不把 WRAcc 冒称 STCA 算法结果；冻结字面条件模型与完整原生训练模型保持真实类型。无有效条件不能登记为全通过规则。临时目录不承诺跨会话保留，新会话可上传规则包载入。

## 使用已有规则筛选

已有规则包含当前能读取的用户已保存规则、作者STCA论文中实现的 Tg/EC 规则及当前开源数据任务的 source 冻结规则。公开数据来源为GAS实测气体数据、RadonPy和ADEPT计算数据，以及OpenPoly文献水接触角数据，均提供STCA规则归纳与筛选验证结果，详见[来源说明](references/provenance.md)。当前开源目录提供 Top 10%、20%、30% 的 STCA 与 WRAcc 主推/备选；其他百分比可从用户数据重新归纳，不能插值或换成最近档。保留每条规则的精确条件；用户明确要求版本核对时读取相应来源记录。

先读取 `task_menu.py --rules --library-dir USER_RULES_DIR` 的规则目录。论文规则与当前开源方法结果的数量和可用状态以实际目录为准；不得硬编码旧版本规则数。未知或已移除ID应明确报错，不能静默替换；用户自己的已保存规则仍可导入使用。按来源 → 性质 → 方向/档位展示。目标已明确但未给百分比时，对实际支持的默认10%、20%、30%分别筛选，不再补问档位；缺档如实说明。默认分别返回STCA、WRAcc及每档主推，不能把方法/档位的多个结果自动AND；用户指定只用一种方法或“用推荐”时直接采用。已明确精确规则时直接执行，不重复询问。逐档显示实际物理阈值、比较符和单位。

内置条目由 `rule_library.py show ID` 读取精确条件，用 `rule_library.py screen ID ...` 核验。已保存规则用 `user_rule_library.py list/show` 读取，再用 `stca_tools.py screen-candidates` 应用对应模型和档位。无需重新训练或再上传训练数据。应用已有结构规则只需候选结构列，不要求候选表有密度等性质标签；仍须明确结构列，多个结构列含义不清时先询问。

用户要求“内置含氟候选示例”时，候选表为`assets/examples/quick_start_candidates.csv`；按用户指定规则实际筛选。该表只有结构，不能用于学习或评价密度性质。简短试用见[usage_examples.md](references/usage_examples.md)。

方法比较分别筛选 STCA 和 WRAcc；多性质联合筛选才将选定的不同目标规则作用于同一候选表，返回逐项判断及 AND 交集。同目标备选方法不自动相交。报告全部原始结构、未满足的规则条件、未知记录和入选表。

## 使用已有规则生成

用户要按规则生成但尚未明确目标时，先显示已保存规则及 STCA论文、GAS、RadonPy、ADEPT、OpenPoly的简洁目录，等待选定具体目标规则；每条冻结规则自带档位及数值阈值。未指定方法时使用该档主推并明确告知，用户可改用备选。若“刚保存的规则”仍包含多个性质/档位，只补问未明确的目标选择；用户明确要求多档生成时各档独立准备、生成、核验，不将同性质不同档位合成一个AND任务。

选择完成后读取已存完整 prompt：内置用 `rule_library.py prompt ID --language zh-CN`；保存条目用其精确 constraints/prompt。数量、偏好、多目标组合用标准库 `generation_prompt.py` 渲染。prompt 标明真实方法、性质、来源、阈值、全部 AND 条件、MACCS计数及特殊键语义、H-cap计算约定、聚合物重复单元 SMILES 格式与核验要求。

规则选定后提供两种生成方式；用户已明确说“先看 prompt”或“直接生成”时按其选择执行：

1. **先查看并调整 prompt，再生成。** 展示完整 prompt，允许修改数量、化学偏好及输出要求。保存每次修改后的完整文本，等待用户明确确认最终版本，再调用当前 LLM 实际生成候选并逐条核验。展示或修改 prompt 后不得自行确认、提前生成或用等待时间代替确认。
2. **直接生成并核验。** 按所选规则、数量及偏好准备完整 prompt，立即调用当前 LLM 生成，再执行精确条件核验，无需额外确认。

通过标准库 `generation_session.py` 管理准备、修改、确认及最终 prompt；读取其 `generation_allowed` 和 `next_action` 后继续。用户说“确认，开始生成”时，要在同次操作中完成确认、当前 LLM 生成和核验，不能停在批准状态。助手本身执行生成步骤；Python 模板渲染或状态更新不算调用 LLM。修改冻结目标、阈值或位条件时须明确选择/建立新规则，保留原规则用于核验，不能静默改写原条件。

保留最终使用的完整 prompt、全部原始提案、修订、通过表及逐条未满足的规则条件，交付后继续对话。用户只要 prompt 时直接交付可复制原文。RDKit/数值库因签名、导入或执行权限失败时先尝试其他兼容环境；仍无法计算则将已生成提案标为“待核验”，保留运行错误。未执行解析不等于 SMILES 无效，也不能报告“0 条通过”或“零覆盖”；只有实际完成解析后才能统计有效/无效结构。规则匹配与实际物性达标分别报告。具体命令见 [generation.md](references/generation.md)。

## 执行受阻与部分结果

默认加载随包、逐文件核验的作者源码，普通计算不执行 Git 克隆；不伪造 `.git`、手写提交号、关闭来源校验或修改作者算法。核验失败时停止使用该源码并说明实际错误。WorkBuddy 的运行资源与缓存默认放在当前任务工作区，安装目录保持只读。

遇到 `PermissionError`、文件操作或命令被平台拒绝时，保留首个失败命令、退出码和原始错误，停止受阻步骤；按平台正常授权流程处理具体目录或操作。不要为绕过拒绝而修改验证器、换用另一种系统接口、伪装权限成功或反复创建目录重跑。只有新的明确授权或已核实的输入修正后才重试。不能仅凭 LLM 推测断言“所有删除均被拦截”。

读取 `run_manifest.json` 与 `screening_summary.json` 的 `status`、`storage_warnings` 及真实保存凭据。`completed_with_storage_warning` 表示计算产物保留、规则目录保存或导出未全部完成；交付两方法已存在的模型、约束、prompt和结果，明确未完成项，不声称规则库保存成功，也不因保存问题再次训练。没有 WRAcc 导出文件不等于无规则或零覆盖。用户侧只汇报简短进度、实际阻碍和结果，不逐轮展示临时修补探索或编造成功状态。

## 共同约定

- 保留原始聚合物 SMILES；重复单元保留原有 `*` 连接点，H-cap只用于计算副本，MACCS167原编号及特殊/计数语义不变。不能把 K=0 一律解释为完全无该子结构。
- 输入只读、输出另存。保存来源、版本、精确方法、模型哈希、尺度与角色。用户数据和规则库不写入安装目录。
- 使用运行配置指定的原作者 STCA 实现。WRAcc 是单独的备选规则学习器。每条精确规则内部为 AND。
- 区分已有规则、零覆盖、零TP、无正例、无规则、计算错误和未定义指标。外推附录的零覆盖不用于覆盖当前当前冻结规则的支持或距离外推证据。
- 首次计算由 agent 使用随包 `scripts/launch_runtime.sh`（macOS/Linux）或 `scripts/launch_runtime.ps1`（Windows）自动发现解释器，再进入 `agent_runtime.py`；优先复用成功记录并检查未激活 Conda 与常见环境，不要求用户填写路径。明确指定的路径验证失败时如实报告，不静默换用其他环境。
- 复用 Python **3.10及以上**兼容 CPU 环境；历史依赖锁仅在明确复现时使用。由 `agent_runtime.py` 自动管理后台，不给普通用户安装命令。

## 按需读取

- [agent_workflows.md](references/agent_workflows.md)：内部命令、输出和保存复用。
- [custom_data.md](references/custom_data.md)、[auto_pipeline.md](references/auto_pipeline.md)：准备、单位、分组CV与留出协议。
- [effectiveness.md](references/effectiveness.md)、[provenance.md](references/provenance.md)：当前证据与来源。
- [usage_examples.md](references/usage_examples.md)：面向用户的简短用法。
- [algorithm.md](references/algorithm.md)、[generation.md](references/generation.md)、[commands.md](references/commands.md)：原理和低层接口。
