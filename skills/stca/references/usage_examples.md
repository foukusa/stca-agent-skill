# STCA: natural-language examples after installation

STCA is used by the current LLM in the conversation. It does not create a fixed numbered application menu or a separate saved-rules page. Follow a complete request directly. When the goal is missing, briefly offer learning, screening or generation in the user's language. Use actual output files and execution receipts; fill counts only after running the requested calculation.

## 用 ADEPT 单体能隙数据筛选

读取[案例配置](../assets/examples/adept_gap_case.json)。用户上传完整 `BANDGAP_DFT.csv`，说明：“使用现成的 ADEPT 高单体能隙 Top30% STCA 规则筛选这份数据。”

按列名读取全部2,916条输入：结构`SMILES`（A/第1列）、目标`BANDGAP`（B/第2列），单位eV。目标是氢封端孤立单体的DFT HOMO–LUMO能隙，不是体相聚合物带隙。此演示明确选择STCA，使用`current-ad-gap-stca-high-30`；不要替换成目录自动推荐的WRAcc。实际运行后核对冻结边界≥11.914537535 eV、全表976条匹配、0条未知；保留全部原始字段、星号和未满足条件。

## 从同一份公开数据学习并复用

用户：“从这份 ADEPT 文件总结高单体能隙 Top30% 规则。结构列SMILES，性质列BANDGAP，单位eV，使用全部数据行。返回两种方法和筛选结果，与现成规则比较并保存。”

学习前简短说明文件、2,916行、实际列名、单位和DFT标签含义。调用默认 `morgan_evaluation.py`：仅结构决定source/holdout/buffer，外推最近邻ECFP4距离≥0.5；数据清理、形式、步长、支持量和拟合仅用source。用户明确给出的百分比优先，未给时直接用10%、20%、30%。source内部另一次Morgan验证选择方法，不使用最终holdout选优。

每档交付STCA与WRAcc的精确条件、实际数值阈值、比较符和单位、全部原表筛选、独立外推分数及自动推荐理由。本例随后明确复用STCA；不据此改动目录的WRAcc自动推荐。独立外推不是原表回筛；source内随机分组CV仅作范围内诊断。

执行 `fingerprint_contract.py --run-dir RUN_DIR` 核对source指纹、距离和冻结模型。读取真实保存凭据后交付便携规则包。用户接着说：

> 重新载入刚保存的Top30% STCA规则，再筛选同一份ADEPT文件，核对每行是否一致。

应用保存模型，不重新训练，不要求再上传原训练数据。新会话可导入规则包继续。

RadonPy密度仍是可选任务，按其[案例配置](../assets/examples/radonpy_density_case.json)绑定原始列。OpenPoly水接触角保留在现成规则目录，用于展示支持的性质范围；不作为效果展示或默认计算范例。

## 原始星号结构的处理

用户上传的聚合物SMILES保留 `*` 连接点。先保存原始列，仅将计算副本的末端单键连接点换为氢（H-cap）以计算MACCS指纹；结果表和入选表返回原始带 `*` 的SMILES及相同连接位置。这里“返回时恢复星号”是取回原始结构，不是从H-cap分子反推星号。已封端输入保持原样。应用已有规则只需结构列，无需候选性质标签。

## 从自己的数据总结规则

用户：这是我的聚合物热导率数据，单位 W/(m K)，计算值。我想总结高值规则，考虑 Top 15% 和 25%。

只询问缺失的科学信息，使用用户的百分比，不替换为默认值。交付两方法独立结果和推荐理由。首次解释评分时，说明推荐使用source内Morgan验证，外部holdout在规则冻结后才评价；平均筛选评分为马修斯相关系数、精确率和 F1 分数的平均值。不能只报“CV AS”缩写。精确条件、原始 SMILES 和全部未满足条件保留。

用户：WRAcc 最多用 10 条条件。

传入明确上限，保留实际规则长度和设置。用户说“不限制 WRAcc 条件数”时移除长度上限；beam 搜索范围和最小支持要求仍生效，不承诺更长一定更好。已有冻结规则不因该请求被修改；要比较长度，需要重新学习。

## 从现成规则开始

用户：用已有规则筛选这份候选表。

目标尚不明确时，简短列出论文、RadonPy、ADEPT、GAS、OpenPoly 及当前可读的已保存规则，按性质和可用百分比让用户选择。不要倾倒全部规则条件。若请求已明确来源、目标和档位，直接读取所选条件执行。

用户：使用作者 STCA 论文中的高 Tg Top 20% 规则。

执行冻结规则，报告原始 SMILES、逐条判断、未满足条件和入选表。交付后继续对话，不声称返回了平台不存在的菜单。

## 预览和调整后生成

用户：使用作者 STCA 论文中的高 Tg Top 20% 规则，先给我看生成 10 个重复单元的 prompt。

读取完整冻结 prompt，保留全部条件，展示后等待确认。

用户：改成 5 个，优先不含氟。

更新并展示完整 prompt，继续等待确认。

用户：确认，开始生成。

当前 LLM 读取批准后的完整 prompt，实际生成候选并保存全部提案，再执行同一冻结规则的计算核验。交付生成数量、实际完成核验的数量、通过表及未满足条件。不能用 prompt 渲染或确认状态替代 LLM 生成。

## 直接生成

同一ADEPT案例可说：“用刚才选定的高单体能隙 Top30% STCA规则直接生成5个聚合物重复单元并核验。”生成前读取该精确条目的完整prompt，不因推荐方法而替换当前选择。随包静态五条生成示例明确使用 STCA，只供展示，不当作新提案复制。

用户：用刚才选定的规则直接生成 20 个聚合物重复单元并核验。

复用明确选择，读取完整 prompt，连续生成和核验，不增加预览确认。若仍有多个性质或档位，只补问未明确的目标。生成的是带两个末端单键连接点的聚合物重复单元，H-cap 只用于计算副本，原始星号结构保持。

## 状态必须与计算一致

- Python/RDKit 因签名、导入或执行权限失败时，继续尝试兼容环境；仍失败则保留提案并标为待核验。未运行解析不等于 SMILES 无效，也不是零入选。
- 分别统计实际生成、完成解析、结构有效和规则匹配的数量，说明真正阻塞的步骤。
- 规则匹配不等于实测物性达标，不编造物性值或保证生成通过率。
- 用户可以说“接下来可以做什么”，也可直接继续筛选、生成或载入规则包。数字只有在当前对话确实给过编号时才作为指代。

## English requests

- **Learn:** “Learn high-monomer-gap Top30% rules from this ADEPT dataset. Use `SMILES` for structures and `BANDGAP` for the target, in eV. Return both methods and screening results, then save the rules.” State the actual binding before learning; resolve ambiguous columns with the user first. Return independent methods and numerical cutoffs.
- **Reuse:** “Use the recommended Top 20% rule just saved to screen this new candidate table.” Read the actual files, apply the selected rule and retain all original inputs.
- **Preview:** “Use the STCA-paper high-Tg Top 20% rule. Show the prompt for five repeat units first.” Display the complete prompt and wait for explicit confirmation.
- **Direct:** “Generate and verify 20 polymer repeat units directly with the selected rule.” The current LLM generates; the calculation verifies. Preserve proposals as pending if verification cannot run.
- **Continue elsewhere:** “Load this saved rule bundle and continue.” Import it, then resolve the intended saved target from the conversation.

同一保存模型重新载入后应用同表必须逐行一致；当前默认冻结规则与重新归纳采用相同原始数据、source-first距离划分、逐档准备、H-cap、算法和设置；同一档位单独或批量请求时应一致。保留不同原始连接图，不按H-cap结果相同强行合并。
