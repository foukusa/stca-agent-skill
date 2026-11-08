# STCA skill 三种使用路径

[现成规则](#路径一直接调用内置规则) · [上传数据](#路径二上传-csv-自动归纳) · [生成与核验](#路径三取-prompt生成并核验) · [共同交付](#共同交付)

所有查询、筛选、重新归纳、prompt 导出、生成与核验均由自然语言请求触发，agent 连续完成后台操作。用户不需写命令、配置环境或部署模型。STCA 使用 CPU，生成使用当前宿主 LLM。以下命令仅供 agent 内部执行；`PY` 表示宿主已有解释器，`SKILL_DIR` 表示实际 skill 目录，`RULE_ID` 必须从目录读取。版本为 `0.1.0`。

## 路径一：直接调用内置规则

### 选择规则

1. 读取 `assets/rule_library/index.md` 和 `catalog.json`，按性质、方向、档位和来源定位条目。
2. 读取条目对应的完整条件、阈值、单位、表示和出处。论文 Tg/EC、作者归档数据集规则、新自动归纳规则保留各自来源标签。
3. 用户已明确选择时直接使用；未指定档位时展示可用档位及物理阈值。不同目标可独立选档。
4. 条目状态必须允许实际应用。只有结果汇总、缺失条件或明确无有效规则的记录不能代替冻结规则。

```text
PY SKILL_DIR/scripts/rule_library.py list
PY SKILL_DIR/scripts/rule_library.py list --property PROPERTY --direction high
PY SKILL_DIR/scripts/rule_library.py show RULE_ID
```

读取目录和这些查询不需要 RDKit 或训练环境。目录包含的数值 cutoff 描述源训练数据目标；百分位不是筛选候选数量的配额。不得为了选够指定数量改动规则。

### 筛选上传候选

识别结构列和可选 ID 列。对同一输入批次应用一个或多个规则，逐条计算精确 MACCS AND 条件，再交付各项状态、失败条件及交集。

```text
PY SKILL_DIR/scripts/agent_runtime.py run --script rule_library.py -- screen RULE_ID [RULE_ID ...] --input candidates.csv --smiles-column SMILES --id-column CandidateKey --output-dir out/screening
```

`--id-column` 可省略或替换为用户列名。原始 `*` 保留；H-cap 仅用于 MACCS167。遇到无效/不支持结构时保留错误状态和原行，不能以全零指纹伪装有效输入。筛选无需重新训练，也无需下载作者训练源码。

多目标结果是同一候选满足多个结构条件的交集。保留 bit 冲突和空交集原因；不要删去不方便的条件。跨性质调用应明确源性质、目标性质与迁移假设。

## 路径二：上传 CSV 自动归纳

### 确定输入含义

从表头、样例与上下文确定结构、目标、单位、方向、条件及实测/计算来源。ID 原样透传；没有 ID 时生成行级对应记录，不把随机 ID 当作材料分组。已取对数的列记录原尺度，避免重复取对数。

用户未指定探索范围时，计算 10%、15%、20%、25%、30% 各档，展示实际阈值及 source 内建议；明确档位或绝对目标时按用户要求执行。不能对 15% 结果作插值。source 内配置选择和档位建议分别记录。

### 自动执行

```text
PY SKILL_DIR/scripts/agent_runtime.py run --script auto_screen.py -- --input observations.csv --target TARGET_COLUMN --target-name PROPERTY --unit UNIT --direction high --tiers 0.10,0.15,0.20,0.25,0.30 --smiles-column SMILES --data-kind experimental --output-dir out/analysis
```

根据真实文件替换参数；计算数据使用 `--data-kind computed`，低方向使用 `--direction low`。有 ID 时增加 `--id-column`，有测量条件时增加 `--condition-columns`。已有明确 source/holdout 角色时传入 `--role-column` 及角色值；已有 inner 角色也保留。

自动入口完成以下工作：

- 审计 CSV，排除缺失/非数值/非有限目标、无法计算的结构与可确认的完全重复导出行，保存排除原因和原行映射；按用户声明的质量列或物理范围执行额外排除。
- 保留有效极端值、观测条件和重复测量。处理历史、邻居偏离和重复冲突先标记；不自动将 H-cap 相同结构聚合为同一材料。
- 需要生成角色时，使用 H-cap 上 Morgan radius=2、2048 位 ECFP4 作 t-SNE 外围划分，seed42；在 source 内重复构造 inner validation。原始 canonical 重复、H-cap 碰撞及显式材料分组保护在同侧。
- 仅 source/inner-train 决定目标变换、扫描步长和候选配置；inner validation 选择扫描配置，在全 source 重拟合，冻结后才评价 holdout。
- 使用作者 generic STCA 生成 MACCS167 正负排序、前缀 AND 家族和代表规则；保存全部档位阈值、模型与计数。

这种 ECFP4 划分是新数据上的明确实验角色；不会凭二维外围位置保证物理外推。精确论文复现另用原始成员与原参数。源内变换、步长、支持配置及评价语义详见 [custom_data.md](custom_data.md) 和 [algorithm.md](algorithm.md)。

### 阅读输出

读取 `fit/model.json`、`fit/source_settings.json`、`fit/tier_cutoffs.csv`、`fit/evaluation_metrics.json`、`tier_recommendations.json` 及运行审计，确认实际执行状态。对各有效档位由 agent 自动执行 `stca_tools.py export-rules`，交付其完整 `prompt.en.md`、`prompt.zh-CN.md` 和约束；不能让用户自行运行导出。给用户各档规则、物理 cutoff、支持数和清晰的源内建议，再连续完成其已要求的筛选或生成任务。

正例支持量阈值是报告诊断，不是禁止生成规则的门槛。区分无规则、规则选中零条、评价集零正例、计算异常及 MCC/Precision/Recall 未定义。不能把异常捕获为 0 分；不依赖 holdout 分数重新挑配置、档位或切分。

需要保留原角色及固定参数时，通过同一后台运行 `custom_fit.py`；严格论文命名配方和自定义 adaptive 分析各自保留出处。

## 路径三：取 prompt、生成并核验

### 直接取现成 prompt

从所选条目读取现成 prompt，或用下面的标准库查询复制到新文件。完整交付可复制文本，无需用户了解 MACCS 或安装科学计算依赖。

```text
PY SKILL_DIR/scripts/rule_library.py prompt RULE_ID --language zh-CN --output out/prompt.md
```

用户只索要 prompt 时，交付即完成。用户要求“生成并核验”时，读取或渲染 prompt 后立即由当前宿主 LLM 提案，再运行同一冻结规则核验，最后一次性交付结果。用户要在其他 LLM 生成时交付完整原文和简单使用说明。

### 组合规则或采用新归纳规则

从目录取得精确 constraints 文件路径。新模型先导出所选档位：

```text
PY SKILL_DIR/scripts/agent_runtime.py run --script stca_tools.py -- export-rules --model out/analysis/fit/model.json --tier 0.15 --output-dir out/exported_rule
PY SKILL_DIR/scripts/generation_prompt.py --constraints out/exported_rule/constraints.json --count 20 --language zh-CN --output out/prompt.md
```

多个目标在 `--constraints` 后依次传入多个文件，其条件以 AND 相交；可用 `--preferences` 传用户化学偏好。生成器只渲染 prompt，不会调用外部 LLM。输出路径使用新文件，提前建立父目录。

prompt 应包含每项目标来源、方向、档位、实际物理/模型尺度阈值、全部条件、MACCS 激活/计数语义、H-cap 计算约定、原始星号 SMILES 输出格式和核验要求。拒绝占位性质/单位；多目标 bit 冲突先显示给用户。不能把“bit=0”一律解释为完全不含相应子结构。

### 生成后核验

保留完整原始提案表、生成数量、prompt 和失败记录。先检查 SMILES，再 H-cap/MACCS 计算和精确冻结规则核验。内置规则用路径一的 `rule_library.py screen`；新模型用：

```text
PY SKILL_DIR/scripts/agent_runtime.py run --script stca_tools.py -- screen-candidates --model out/analysis/fit/model.json --tier 0.15 --input proposals.csv --smiles-column SMILES --output-dir out/verified
```

新模型多目标核验用 `stca_tools.py joint-screen`，按 [commands.md](commands.md) 配置同一批候选。生成建议、结构条件通过及物性达到目标分别报告。仅有规则匹配不能证明可合成性、实验性能或新颖性；这些结论需要对应证据。

## 共同交付

回答本次使用的规则来源/版本、目标与实际阈值、输入/提案数、选中数及每条失败条件。提供用户所需的 prompt、候选表、完整规则和审计文件；分析任务另提供模型、角色、源内参数、评价状态及来源哈希。

原始带星号 SMILES 是候选主结果，H-cap 放入审计副本。输入保持只读，结果保存在用户指定目录；不将用户观测表或逐材料结果写回 skill。后台操作见 [platform-runtime.md](platform-runtime.md)。
