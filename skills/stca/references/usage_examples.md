# STCA: natural-language examples after installation

STCA is used by the current LLM in the conversation. It does not create a fixed numbered application menu or a separate saved-rules page. Follow a complete request directly. When the goal is missing, briefly offer learning, screening or generation in the user's language. Use actual output files and execution receipts; fill counts only after running the requested calculation.

## 同一份 RadonPy 数据试用筛选

读取 [案例配置](../assets/examples/radonpy_density_case.json)。用户上传完整 PI1070.csv，说明：使用现成 RadonPy 高密度 Top 30% STCA 规则筛选这份数据。

按列名读取全部1077条输入：可选标识monomer_ID、结构smiles、目标density（g/cm³，MD计算），不让用户逐格选取集成表。当前精选条目为`latest-pi-rho-stca-high-30`，条件K42=1，物理目标边界≥1.222343047g/cm³。实际筛选应得到137条匹配、940条未匹配、0未知；读取真实输出才报数字。不要静默选用同名旧兼容条目，也不从候选表重算冻结阈值。

## 从公开数据总结规则后继续筛选

用户上传 RadonPy 的 PI1070.csv，说明：从这份 RadonPy 数据总结高密度规则，返回筛选结果并保存规则。

读取 `smiles` 与 `density` 列，目标单位 g/cm³，标签为分子动力学计算值。默认执行 Top 10%、20%、30%，用户明确给出的其他合法百分比按请求计算。自动准备数据、选择变换和步长；WRAcc 条件数上限仅在当前训练部分内部选择，也接受用户指定上限或不限制。不能按外部测试分数挑选长度。同时返回 STCA 与 WRAcc 在各档位的规则、原始物理阈值、比较符、单位、完整原表筛选和主推理由。读取实际文件后说明采用的设置，不能凭预期声称已自适应。

检查run_manifest.json、fingerprint_contract.json、真实交叉验证分组和折外预测，再执行fingerprint_contract.py --run-dir输出目录。只有表示核对通过后才交付成功状态。保存成功后交付真实文件名、位置及便携规则包。用户可以接着说：

> 用刚才保存的高密度 Top 20% 推荐规则筛选这份新候选表。

读取实际保存的精确模型与档位，直接筛选，不重新要求训练数据。跨会话时让用户上传保存的规则包，不承诺临时文件自动保留。

## 从自己的数据总结规则

用户：这是我的聚合物热导率数据，单位 W/(m K)，计算值。我想总结高值规则，考虑 Top 15% 和 25%。

只询问缺失的科学信息，使用用户的百分比，不替换为默认值。交付两方法独立结果和推荐理由。首次解释评分时，说明交叉验证用未参与本折训练的数据评价规则；平均筛选评分为马修斯相关系数、精确率和 F1 分数的平均值。不能只报“CV AS”缩写。精确条件、原始 SMILES 和全部未满足条件保留。

用户：WRAcc 最多用 10 条条件。

传入明确上限，保留实际规则长度和设置。用户说“不限制 WRAcc 条件数”时移除长度上限；beam 搜索范围和最小支持要求仍生效，不承诺更长一定更好。已有冻结规则不因该请求被修改；要比较长度，需要重新学习。

## 从现成规则开始

用户：用已有规则筛选这份候选表。

目标尚不明确时，简短列出论文、RadonPy、ADEPT、GAS 及当前可读的已保存规则，按性质和可用百分比让用户选择。不要倾倒全部规则条件。若请求已明确来源、目标和档位，直接读取所选条件执行。

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

同一RadonPy案例可说：“用刚才选定的高密度 Top 30% STCA 规则直接生成5个聚合物重复单元并核验。”生成前读取该精确条目的完整prompt；静态示例只供展示，不当作新提案复制。

用户：用刚才选定的规则直接生成 20 个聚合物重复单元并核验。

复用明确选择，读取完整 prompt，连续生成和核验，不增加预览确认。若仍有多个性质或档位，只补问未明确的目标。生成的是带两个末端单键连接点的聚合物重复单元，H-cap 只用于计算副本，原始星号结构保持。

## 状态必须与计算一致

- Python/RDKit 因签名、导入或执行权限失败时，继续尝试兼容环境；仍失败则保留提案并标为待核验。未运行解析不等于 SMILES 无效，也不是零入选。
- 分别统计实际生成、完成解析、结构有效和规则匹配的数量，说明真正阻塞的步骤。
- 规则匹配不等于实测物性达标，不编造物性值或保证生成通过率。
- 用户可以说“接下来可以做什么”，也可直接继续筛选、生成或载入规则包。数字只有在当前对话确实给过编号时才作为指代。

## English requests

- **Learn:** “Learn high-density rules from this RadonPy dataset, return screening results and save the rules.” Use the `smiles` and `density` columns, g/cm³ and computed-label meaning; return independent methods and numerical cutoffs.
- **Reuse:** “Use the recommended Top 20% rule just saved to screen this new candidate table.” Read the actual files, apply the selected rule and retain all original inputs.
- **Preview:** “Use the STCA-paper high-Tg Top 20% rule. Show the prompt for five repeat units first.” Display the complete prompt and wait for explicit confirmation.
- **Direct:** “Generate and verify 20 polymer repeat units directly with the selected rule.” The current LLM generates; the calculation verifies. Preserve proposals as pending if verification cannot run.
- **Continue elsewhere:** “Load this saved rule bundle and continue.” Import it, then resolve the intended saved target from the conversation.

同一保存模型重新载入后应用同表必须逐行一致；自适应重学与旧冻结规则只有在原始数据、准备方法、H-cap、算法及全部设置相同时才应一致。保留不同原始连接图，不按H-cap结果相同强行合并。
