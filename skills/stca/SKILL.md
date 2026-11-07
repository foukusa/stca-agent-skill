---
name: stca
description: "Use Weihao Wang's original Sliding Threshold Correlation Analysis (STCA) to screen polymer repeat units, mine readable presence/absence substructure rules from measured data, evaluate frozen rules, combine property constraints, or export prompt-ready rules. Trigger on STCA、滑动阈值相关分析、子结构筛选、STCA规则提取/复现/生成约束. Call the pinned author implementation; distinguish published-rule screening from source-only fitting. C-STCA composites, SC-SHAP intervals, Auto-Select, GSP, BO and PolymerLLM are separate methods, not implicit replacements."
---

# STCA 聚合物筛选

把用户的数据和目标转为可执行的 STCA 工作流。调用作者的原始实现，输出实际运行得到的结构规则、候选表和评价证据。默认用中文说明输入、输出、目的和结果。

## 先决定任务与协议

| 用户任务 | 执行方式 |
|---|---|
| 给新 SMILES，按已发表 STCA 筛选 | 加载冻结的 `paper` profile；不需要原始训练数据 |
| 给新测量数据，要求只用源标签提取并冻结规则 | 显式 `source_locked`；只用源数据选代表，然后评价留出集；不称为论文代表规则的原样复现 |
| 要复现论文选优过程 | 显式 `paper`、原始数据角色及 selection 数据；这些标签参与选优，不能称为最终盲测 |
| 给自定义二值特征或其他性能 | 显式 `generic`，记录特征含义、方向、单位、步长；标注为该协议的应用 |
| 要多性能结构筛选 | 在同一候选表逐项应用冻结模型，取 AND 交集；逐项保留规则来源和 tier |
| 要规则引导的候选生成或生成约束 | 导出全部家族、代表规则、精确 bit 条件和 prompt；外层 agent 提出候选，再用 RDKit/冻结规则检查 |

已知上下文足够时直接执行。未给筛选档位的预置模型应用可采用 `tier=0.20`，在结果明确注明该默认；这不是新候选的选中比例。新数据拟合优先按用户的目标选择协议；没有指定步长的任意性质不要从 EC/Tg 抄一个量纲不符的数值。

用户要求按给出的原代码、原结果或原论文筛选时，优先恢复相同数据划分和 `paper` 协议，不能把 `source_locked` 的不同代表规则当成复现结果。特别是原 EC 5% 的 paper 规则在已核对的 691/172 原划分上选中 328/61 条；source_locked 代表在同一 extra 集选中 0 条，这是不同规则的覆盖差异，不是原流程筛不出。新数据比较或 source-only 分析另列。

先读 [algorithm.md](references/algorithm.md)。需要安装、出处或复现边界时读 [provenance.md](references/provenance.md)。实际命令、数据格式和结果交付见 [commands.md](references/commands.md)。询问已验证能力、科学效果或发布范围时读 [validation.md](references/validation.md)。

## 1. 准备可重复运行环境

令 `SKILL_DIR` 为当前这个 `SKILL.md` 的目录；不要硬编码已安装目录名称。已有锁定安装输出的 `python` 和 `source` 时，直接复用该解释器，并设置 `STCA_SOURCE` 或传 `--source`；不要再次运行 convenience bootstrap 切换环境。

公开发行版的首次安装优先使用 CPython 3.12 锁定入口，`STCA_ENV_DIR` 必须是用户可写的全新目录：

```bash
python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" --env-dir "$STCA_ENV_DIR"
```

从输出 JSON 读取 `python` 作为 `STCA_PY`，读取 `source` 并设置 `STCA_SOURCE`。Linux x86_64 使用精确版本和 wheel SHA256，其他系统使用精确版本表；macOS/Windows 尚需各自验收。安装失败不得静默放宽依赖或替换版本。具体操作见 [commands.md](references/commands.md)。

已有兼容工作环境可继续使用原便利安装入口；它复用系统依赖、采用较宽版本条件，不等同于上述锁定发行环境：

```bash
python3 "$SKILL_DIR/scripts/stca_runtime.py" bootstrap --chem
```

从输出 JSON 读取实际 `python` 路径作为 `STCA_PY`，后续脚本都用它。该命令取得锁定的 STCA 1.0 源码并准备运行环境；不把算法、预置模型或用户训练数据复制到 skill 包。已经准备完成则复用。离线时可通过脚本的全局 `--source /absolute/clean-checkout` 使用同一版本的干净源码及已准备依赖。

先运行 `doctor` 确认源码与环境。源码缺失、依赖失败或输入不足时完成能够完成的检查并明确缺少什么；不要用临时自写相关性算法冒充 STCA。

## 2. 明确数据合同并检查

- 从文件或已有上下文确认样本标识、重复单元 SMILES、目标列、原始单位、测量条件、数据划分和任务方向。候选筛选不需要目标列。
- 原 STCA 的作者已明确输入预处理为 **H-cap：连接点换为氢后计算 MACCS**。对带末端单键 `*` 的原始候选，先用 `prepare_hcap.py` 显式生成新列，保留原 SMILES，再把 H-cap 列交给锁定核心。无星号的已处理表原样保留；已有 MACCS 矩阵不再转换。不得把低层 `as_provided` 接口误解为完整流程无需 H-cap，也不得直接把带星号候选的 MACCS 与原规则比较。具体自定义模型使用其训练时表示；表示未知时先核对。
- SMILES 路径仍针对原论文的线性均聚物研究范围。两个末端 `*` 只是候选连接格式，不足以证明架构或合成性；H-cap 后相同图可能来自连接点不同的聚合物，不自动合并或删除。不要额外去盐、互变异构归一或构造低聚物。
- 用 `audit_dataset.py` 检查输入；涉及 source/selection/test 时一起检查 canonical 结构和标识交叉。保持同一结构的重复测量可追溯，不自动去重、平均或删冲突样本。
- 二值特征必须显式列出；不得把 ID、分组、split 或目标列纳入特征。若输入为 MACCS，保留 167 个位置与 K0 空位；普通二值列不自动视为 MACCS。
- 对 EC 明确 `S/m`、`S/cm`、`log10(S/m)` 或 `log10(S/cm)`，调用上游转换。对 Tg 明确 degC/K。不要猜单位，不把电导率与电阻率混用。
- 保留训练数据与候选数据的原始文件。转换或划分另存文件并记录决定。未经定义的分组不可声称化学外推；PCA 只能展示已有划分。

## 3. 执行原算法

用 `stca_runtime.py run -- <上游命令>` 调用核心。`profiles`、`train-profile` 及使用 `--profile` 的 `inspect`/`screen`/`evaluate` 显式传协议；`import-family` 只导入家族模板，没有 `--protocol` 参数。筛选和评价显式传 tier。先按既定协议完成，不因结果差而临时改家族、指标或阈值。

保留以下算法约定：

1. 计算滑动阈值与阈值子集中子结构出现频率之间的 Pearson 相关性。
2. 分别排序正、负关联；按排名前缀构造纯正、纯负和混合 AND 条件。
3. 保留相应规则家族及各成员的覆盖取舍，按明确的协议选代表。EC 的原家族使用上游模板；不得换成任意子集、beam、短 AND、决策树或 Auto-Select。
4. 低 EC 使用反向扫描，高 EC 交换正负榜一次。直接执行模型保存的 bit 条件，不再翻转第二次。
5. 保留无有效规则、排名深度不足、未支持 tier 等实际状态及原因；不填入旧赢家、不悄悄放松条件。继续报告已完成的分析和能够执行的其他目标。

若用户显式要求改算法，先保留原始结果并将修改标为新变体；不要覆盖这个 skill 的原始 STCA 含义。

## 4. 冻结后筛选与评价

先冻结 `model.json`，再处理候选或独立评价数据。默认使用保存的数值训练阈值 `fixed_train`。如果按 `dataset_relative` 评价，明确这改变真实目标定义而没有重新选规则。

记录 TP、FP、TN、FN、Precision、Recall、F1、MCC、coverage、富集倍数、样本数、实际正例数和数值阈值。没有真实标签就不计算真实性能指标。`selected=True` 只表示结构规则通过，不是预测值、成功概率或性能实测达标。

预置模型保存 PID 身份时使用同一身份口径检查重叠。只有用户请求历史数据重评时才启用 `allow_overlap` 并明确结果角色。不同 ID 下相同结构也不能作为独立留出。

绝对目标例如 `Tg≥250 °C` 与 top20% 不是同一任务。读取实际训练 cutoff；可用上游 `evaluate --cutoff` 检验固定规则在给定数值目标下的表现，明确这没有重新训练该绝对阈值的规则。不要声称本 skill 已实现 SC-SHAP 固定区间优化。

## 5. 多性能与生成约束

用 `stca_tools.py joint-screen` 在**同一 CSV 的相同候选行**应用多个模型。用配置逐一写出 profile/model、协议、tier 和名称，输出每一项的状态与联合交集。不得凭不同数据表的行号、相似名称或不同条件的观测拼成联合标签。

区分四种证据：单性能规则验证、结构条件交集、同条件配对标签下的联合评价、后续实验验证。联合结构交集不自动具有前三项之外的证据，不相乘各模型 Precision。检查不同规则对同一 bit 的冲突；不要为了得到非空交集自动删规则。

用 `stca_tools.py export-rules` 输出 JSON 与 prompt。精确保留必须出现/必须缺失的特征及 AND 关系。K 编号没有经过核对时就保留编号，禁止编造化学名称；MACCS 可能有计数和特殊逻辑，不能全部替换成一次 SMARTS 匹配。

用户要求实际生成时，外层 agent 根据冻结约束提出候选，保留每轮全部原始提案、生成预算与规则版本。先审计原始连接点格式，再按 H-cap 契约生成并审计计算列；对同一 CSV 的 H-cap 列执行联合筛选。记录解析有效性、每项 bit 失败原因、原候选 canonical 重复及 H-cap 表示碰撞；候选去重和重复测量处理分开。若数量不足，在用户预算内再提出一批或如实交付不足，不删除失败记录或改变规则。最终报告提出数、有效数、不同结构数及规则通过数。没有调用外部性质模型、数据库或实验时，明确相应证据未取得。脚本只负责约束与核验；候选提议依赖宿主 LLM，并非内置独立生成器。

## 6. 交付实际结果

按任务交付数据审计、冻结模型/规则家族、候选筛选表、评价指标、可用于生成的结构约束和运行记录。结果文件包含输入哈希、代码版本、软件版本、单位、tier、数值 cutoff、协议及数据角色。按宿主环境的文件保存规则持久化用户结果；不要把结果或测量表写回 skill 目录。

最终先说明选出多少候选、主要规则是什么、在什么数据/目标下有效，再说明关键原因和限制。明确本次运行了哪些流程；不要把合成例、静态规则检查或上游已有的验证报告说成此次重新验证论文性能。

## 包内资源

- `scripts/stca_runtime.py`：锁定上游、环境检查、调用原始 CLI、记录运行依据。
- `scripts/setup_locked_environment.py`：创建 CPython 3.12 全新隔离发行环境，读取包内精确依赖文件并核对原源码；保留已有环境。
- `scripts/stca_io.py`：严格检查 CSV 行宽/表头，按文本保留 ID 和结构，仅由上游显式转换特征与目标。
- `scripts/prepare_hcap.py`：按已确认的 H-cap 契约将末端单键连接原子替换为氢，另存计算列与处理记录，保留原始结构。
- `scripts/audit_dataset.py`：数据、重复观测、表示范围和跨集重叠检查。
- `scripts/stca_tools.py`：精确规则/prompt 导出及同候选多模型交集。
- `references/algorithm.md`：数学流程、协议、单位与输出含义。
- `references/provenance.md`：作者、论文、源码版本与证据范围。
- `references/commands.md`：可执行命令和输入输出示例。
- `references/validation.md`：实际验证范围、真实数据结果与已知限制。
- `assets/candidates_demo.csv`、`assets/joint_example.json`：结构接口示例，不含实测性能或新材料发现结论。
