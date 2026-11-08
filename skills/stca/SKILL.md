---
name: stca
description: "Apply Weihao Wang’s original Sliding Threshold Correlation Analysis (STCA) to polymer repeat units: screen with frozen published rules, derive readable prefix rule families from measured data with explicit targets and source-only preprocessing, and verify agent-proposed candidates. Use for STCA、滑动阈值相关分析、子结构筛选、规则提取、气体渗透率、聚合物性质筛选、多性能规则交集、生成约束. Preserve the pinned author implementation; distinguish paper reproduction, custom adaptive analysis and transfer hypotheses. C-STCA, SC-SHAP, Auto-Select, GSP and PolymerLLM are separate methods."
---

# STCA 聚合物筛选

用固定作者实现执行计算，把结构规则、数值目标与证据角色一起交付。不要把说明、旧结果或合成样例当成本次运行结果。版本保持 `0.1.0`。

## 先选择工作流

| 任务 | 执行路径 |
|---|---|
| 对新候选应用论文结论 | `stca_tools.py screen-candidates` 或 `joint-screen`；显式 paper profile 与 tier，不重划分候选 |
| 用自己的实测/计算数据自动提取规则 | 默认 `auto_screen.py`：自动清理不可用行、ECFP4 分角色、源内变换/步长/配置选择、冻结评价；已有精确角色/设置可用 `custom_fit.py` |
| 规则指导候选生成 | `export-rules` → 宿主 LLM 提案 → 保留所有原始提案 → H-cap/MACCS/冻结规则核验 |
| 严格重建论文 | 原始数据角色、原参数与 `paper` 协议；不能用自定义适配冒称原文复现 |

每个目标分别确定性质、方向、单位和显式百分位 tier。`high/low` 是方向；tier 是尾部范围。Tg 预置只有 high，EC high/low 分别对应导电/绝缘。不要默认 5%、不要把所有目标绑定同一档位。缺少 tier 时列出支持档位；不要隐藏选择。

用户允许寻找可用尾部范围时，提供多个百分位选项，例如 Top 10%、15%、20%、25%、30%，按源内规则有效性、支持量和 inner validation 检查，不能在 10% 不可用时直接停止。预先记录探索范围；输出每档实际 cutoff 和原因；15% 必须重新归纳该档规则，不能插值或沿用 10% 结果。`nested` 自动选择扫描配置，不自动选择 tier。若用户规定了不可放宽的绝对目标，保持该目标；若根据已看过的外评改档，标明探索性并完整保留原结果。

论文化学空间划分采用 2048 位、Morgan radius=2（ECFP4-like），与学习规则用的 MACCS167 是两种表示。应用已有规则不重做划分。自定义数据上的同类 t-SNE 外围划分是新分割，不能把“二维外围”直接等同于有保障的化学外推。精确成员、表示和软件参数必须记录。

读 [algorithm.md](references/algorithm.md) 确认算法与协议。新性质、长尾目标、重复测量或有限支持时读 [custom_data.md](references/custom_data.md)。多数据集案例和 CO2 多档位检查见 [case_studies.md](references/case_studies.md)。命令见 [commands.md](references/commands.md)，出处见 [provenance.md](references/provenance.md)，试用证据与限制见 [validation.md](references/validation.md)。平台运行见 [platform-runtime.md](references/platform-runtime.md) 和 [platforms.md](references/platforms.md)。

## 1. 准备锁定环境

以当前 `SKILL.md` 所在目录为 `SKILL_DIR`；不要硬编码安装目录。首次安装用 `scripts/setup_locked_environment.py --env-dir <new-directory>`，读取返回的 `python` 和 `source`，使用该解释器及 `STCA_SOURCE`。源码固定提交为 `5951b0ef23d63edc8f7e803aaaffa5e4168288f6`。已有兼容环境直接复用。运行 `stca_runtime.py doctor`；环境失败时报告原错误，不放宽依赖或自写替代 STCA。便利 bootstrap 与锁定安装的证据分开。

## 2. 审计输入并保留表示

- 原输入只读，输出另存。标识列可任意命名或省略；文本值原样透传，不是特征，不自动定义材料分组或数据角色。
- 原始带 `*` 的重复单元 SMILES 从始至终保留。对支持的末端单键 `*` 建立 H-cap 计算副本，MACCS 用副本，最终结果返回原始结构，不反推连接点。
- 不将 H-cap 图相同自动视为同一聚合物；连接点位置与测量条件仍可能不同。原始 canonical 重复、H-cap 碰撞、条件和多次观测分别记录。
- 无效结构在候选筛选中保留为 error/unknown，不用全零指纹替代。拟合中的无效目标、单位或结构明确报告并要求可追溯输入，不能无声删除。
- 处理历史、异常测量、邻居偏离、重复冲突默认只标记。不要按正则无声删除处理过的材料，不按邻居标签删除“反常”样本，不自动对 H-cap 相同的测量取中位数。确需排除/聚合时要求用户定义策略，保存原行映射、条件及理由。
- MACCS 用 167 位原编号并保留 K0；普通二值列显式指定，不纳入 ID、role、group 或目标列。自定义二值输入不自动解释为 MACCS。
- 明确性质、单位、温度、频率、测试方法和数据来源；区分实测与计算。EC 电导率与电阻率不能混用；已经 logarithmic 的值不得重复取对数。

## 3. 新数据的源内适配

默认执行 `auto_screen.py --input ... --target ... --unit ... --direction high|low --tiers ... --output-dir ...`。自动排除无效/不支持计算的结构、缺失/非数值/非有限目标及同一显式ID的完全相同导出行，保存 `excluded_rows.csv` 与原行映射；声明质量列或物理范围时自动执行相应排除。有效极端值或单凭处理关键词不自动判作无意义。

未给 `--role-column` 时，以 H-cap 的 2048位 Morgan radius=2 指纹作 t-SNE，固定seed42，质心距离最外围20%为holdout，再在source内部重复构造inner validation。原结构、H-cap碰撞和显式分组保护在同侧，不合并观察或改变原星号。已给角色则保留；新生成的成员是自定义新数据实验，不是论文精确成员复现。没有ECFP2默认或替代分割。

自动模式默认 `--transform auto --scan-policy nested`；仅source/inner-train决定目标尺度和有界步长，inner validation选择扫描支持配置，再在全部source重拟合。`tier_recommendations.json` 根据所选inner候选的非空覆盖、正MCC且Precision高于目标率给出合格档位及最严格建议。无合格档位仍交付全部规则、计数和原因，不改outer来制造成功。显式 `--scan-policy fixed` 可保留固定设置，不能冒称具有inner验证建议。

`custom_fit.py` 调用作者 generic STCA，不改相关性、正负排序、前缀 AND 家族和 source AS 代表选择。它不是 paper/Tg/EC 命名配方的原样复现。

- 变换、网格和超参数选择只使用 source。evaluation 标签仅用于冻结后的评价与支持量报告。低层 `custom_fit.py` 要求明确角色；自动入口负责生成或保留角色。
- `data_readiness.py` 检查目标有限性、变化范围、并列值和扫描资源。长尾且严格正的目标可以建议 log10；这是有记录的适配层启发式，可显式选择 none/log10，不能称为新物理规律。
- 步长按目标尺度生成有界 value 网格，不照抄 Tg/EC 的固定步长。恒定目标、有效点不足或网格超限保留原因，不悄悄切成 unique/quantile。
- `fixed` 扫描策略保留显式最小子集数（默认 1）；`nested` 比较最小子集 1 与预先规定的较大支持量，选定配置后在全 source 重拟合。自动入口生成缺少的inner角色，低层入口要求已有inner角色。不能用 evaluation MCC 选配置。
- 较大最小子集或源内对数变换改变扫描配方：标记 custom adaptive。试用中某些失败后形成的改法不是所有新领域均有效的结论。
- 分位目标必须同时输出源训练尺度 cutoff 与原始物理单位 cutoff；低方向反号和 log 逆变换明确记录。evaluation 不重估 fixed_train 阈值。

## 4. 冻结后评价与支持量

保存模型、输入哈希、单位、transform、源内扫描设置、家族和所选规则。逐 tier 输出 TP/FP/TN/FN、Precision、Recall、F1、MCC、coverage、enrichment、源/评价目标数及实际 cutoff。

少量目标样本意味着指标证据弱，不意味着禁止生成规则或筛选。默认正例 20 的支持量检查是可配置诊断阈值，不是新的算法筛选门槛。评价集零正例时，不把不可解释的 Recall/MCC 填 0 后称性能失败；保持 undefined/error 状态和原计数。预测一个都不选也要分别报告“规则无覆盖”和“无规则/错误”。不能用宽泛 `except` 把异常伪装为 0 分。

已有论文规则与自定义 source-only 规则分开。历史 paper 低 EC 5% 原 extra 172 条选中 61 条，不能用不同 source_locked 代表的零覆盖替代原流程。paper selection 标签参与代表选择，不是最终盲测。

尾部影响大时，可开展源内敏感性分析，记录删去观测后规则文字变化；这是诊断，不据此删除 evaluation 记录。有限样本可另做用户定义的重复分组交叉验证，仍须每折内拟合变换和规则；它不是原论文划分的替代复现。

## 5. 多目标、迁移与生成

每个模型要求显式来源、目标性质、方向、tier 与 cutoff。优先使用该性质实测数据得到的规则。Tg→TC、EC→介电常数等跨性质应用必须明确标为 transfer hypothesis；论文报告某个数据上的关系，不保证对所有新来源有效。不得把 Tg cutoff 写成 TC 单位，或把 EC 模型当成介电常数模型。不能静默路由未知性质。

同性质跨来源评价需检查同结构/原始材料重叠与条件；`fixed_train` 与 `dataset_relative` 分开。后者只改变评价标签，不重新学习规则，必须标注实际阈值。原始结构相同但 H-cap 不同、或相反，都不能靠随机 ID 证明无重叠。

对同一候选逐条应用多个冻结模型，保留每项状态、失败条件和 AND 交集。无配对标签不计算真实性能联合指标，不相乘 Precision；冲突 bit 原样报告，不能为了非空交集删规则。

导出约束时保留全部家族、代表规则、精确 bit 和 AND 关系。MACCS 特殊计数/逻辑不可随意改成单 SMARTS 或编造化学名称。宿主 LLM 负责提案，不是内置生成模型。保留生成预算、全部原提案与失败记录，再 H-cap、MACCS、规则核验。最终 `results.csv` 使用原始星号结构；审计副本可含 H-cap。

## 6. 交付

输出应回答输入、目的、实际执行、选中数、规则、物理数值阈值和证据限制。交付冻结模型、规则家族、候选结果、审计、tier cutoff 表、评价状态、运行记录及可执行约束。试用档案可作为历史证据，不能写成每次重新完成；用户测量表和逐材料数据不写入 skill。保存结果到用户指定位置。

## 资源

- `scripts/stca_runtime.py`：锁定作者核心与运行记录。
- `scripts/setup_locked_environment.py`：独立环境；原依赖锁表。
- `scripts/prepare_hcap.py`、`scripts/stca_io.py`、`scripts/audit_dataset.py`：结构及 CSV 边界。
- `scripts/data_readiness.py`：源内目标尺度、扫描网格与评价支持量诊断。
- `scripts/data_cleaning.py`：自动排除不可用观察，保留原行、原因及映射。
- `scripts/auto_screen.py`：自动清理、ECFP4角色、源内变换/步长/配置与档位建议、冻结评价和可选候选筛选。
- `scripts/custom_fit.py`：自定义性质拟合、冻结与评价。
- `scripts/evaluate_custom.py`：同性质有标签新来源的冻结评价，复用变换与单位。
- `scripts/stca_tools.py`：论文/自定义模型筛选、精确约束、同候选交集。
