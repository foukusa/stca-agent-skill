# STCA: examples after installation

When a user asks how to use STCA, show the three choices and short examples in their language. The exchanges below describe interaction and deliverables, not precomputed results. Fill result counts only after actual execution. Let the assistant identify columns and prepare the backend.

可用 [内置结构示例 CSV](../assets/examples/candidates.csv) 试用筛选；该文件仅含结构，没有性质标签，不能拿来归纳物性规则。

## 内置快速试用

收到“用内置含氟候选示例试用筛选”等请求时，使用[五条候选](../assets/examples/quick_start_candidates.csv)。按用户明确指定的RadonPy高密度Top30% STCA方法，读取`latest-pi-rho-stca-high-30`，直接screen并交付全部5行及未满足的规则条件。该结构演示表的PVDF/PTFE/PVF匹配K42=1，PE/PEO不匹配；实际计数仍以运行输出为准。此表没有性质标签，不能用来训练或评价密度预测。

第二种简短试用是用户上传公开GAS原表，明确实测CO₂渗透率/Barrer/high及所需档位。读取`CO2`原始观测列，注册性质使用`permeability_CO2`，不使用Bayesian/Etree插补列作为实测目标。默认inrange流程自动决定变换、步长并回筛原表、保存规则，供下一次直接筛选。

## 中文范例

### 1. 上传自己的数据，总结规则并查看筛选结果

用户：开始使用 STCA。

STCA：1 上传自己的文件总结规则；2 根据已有规则直接筛选；3 根据已有规则直接生成。

用户：1。这是我的热导率数据，单位 W/(m K)，是计算值，我想筛高值。

STCA：读取上传文件；只补问尚不明确的信息。用户未指定档位时直接使用默认10%、20%、30%；用户给出15%、25%等合法百分比时按其请求归纳，不再补问。每档同时给STCA与WRAcc的独立结果、实际物理阈值/比较符/单位及主推理由。交付各档完整规则、阈值、原表的完整筛选结果和入选子表，每条保留原始 SMILES、判断和未满足的规则条件；标明归纳/留出/未用于拟合的记录。保存规则、完整双语 prompt 和下载包后返回主菜单。

用户：2，使用刚保存的规则筛选这份新候选。

STCA：读取保存模型，直接筛选新候选，不要求重新上传训练数据。

### 2. 直接使用现成规则筛选

用户：用已有规则筛选这份候选表。

STCA：展示规则目录：我的规则、论文、GAS、RadonPy、ADEPT；简洁列出性质、方向和可用百分比；选中后再显示该项实际阈值。

用户：选 GAS 的高 CO₂ 渗透率，Top 10%。

STCA：应用所选精确冻结规则，交付原始星号结构、逐条判断、所有未满足的规则条件及入选表，随后返回主菜单。

### 3. 先选规则，再生成新结构

用户：3。

STCA：先展示相同规则目录，询问使用哪一项；保留“我的规则”的友好名称，不自行选默认项。

用户：选作者STCA论文中的高 Tg Top 20%。

STCA：选择生成方式：1 先查看并调整 prompt，确认后生成；2 直接生成并核验。

用户：1，先给我看 prompt，生成 10 个。

STCA：展示完整 prompt，保留全部冻结条件，等待确认。

用户：改成 5 个，优先不含氟的结构。

STCA：更新并展示完整 prompt，等待确认。

用户：确认，开始生成。

STCA：使用确认后的完整 prompt 调用当前 LLM，实际生成候选并逐条核验，交付全部提案、通过表和未满足的规则条件，返回主菜单。

**直接方式：**“使用我选定的规则，直接生成 10 个候选并核验。”读取完整 prompt 后连续生成与核验。

### 其他简短请求

- “使用刚才选定的规则，直接生成 20 个候选并核验。”——复用明确的规则与直接方式。
- “把这条规则的完整中文生成 prompt 给我。”——交付可复制的完整文本。
- “返回主菜单。”——保留当前文件与保存规则。
- “载入这个规则包，继续生成。”——导入旧规则并展示可选档位。
- “用我选定的高热导率和低密度规则共同筛选。”——在同一候选表逐项核验并返回交集；有多个候选规则时先选择。

## English examples

- **Learn and screen:** “Learn high thermal-conductivity rules from this uploaded computed dataset, in W/(m K).” Return each requested tier's rules, cutoffs, full screening results, selected records and failed conditions. Save the rules and prompts, deliver a portable rule bundle and return to the menu.
- **Screen with existing rules:** “Screen this candidate table with existing rules.” Offer the rule directory first. “Choose measured GAS CO₂, high, Top 10%.” Apply the selected frozen rule and return original SMILES, decisions and failed conditions.
- **Generate:** “3.” Offer My rules and the bundled source/property/tier directory and wait for selection. “Choose the STCA-paper high-Tg Top 20% rule.” Offer two modes: preview and edit the complete prompt, then generate after explicit confirmation; or generate and verify immediately. “Show me the prompt for 10 candidates first.” Show the full text and wait. “Make it 5, preferably fluorine-free.” Update the prompt and wait again. “Confirmed, generate now.” Invoke the current LLM with the approved prompt, generate the structures, and verify every proposal.
- **Reuse:** “Use my selected saved rule to directly generate and verify 20 candidates.” Reuse the explicit selection and run the direct mode without extra confirmation.
- **Continue elsewhere:** “Load this saved rule bundle and continue.” Import it, then let the user choose the relevant saved rule and tier.

Rule matching and property attainment are distinct. Report proposed structures as pending verification if the platform cannot run the exact calculation. Never invent measured properties or guaranteed generation yields for examples.

当前开源目录提供12任务的Top10/20/30两方法主推与备选。新归纳默认按结构分组5折×3次比较STCA与WRAcc，分别回筛原表、保存模型/完整prompt并返回菜单；15/25等自定义档位可用自己的数据学习，不能冒称已有新版内置规则。
