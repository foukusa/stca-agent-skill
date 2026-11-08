---
name: stca
description: "Use STCA (Sliding Threshold Correlation Analysis) for polymer repeat units through three agent workflows: apply bundled frozen paper/open-dataset rules, derive rules automatically from an uploaded CSV, or provide self-contained rule-guided prompts for the host or another LLM and verify its candidates. Trigger for STCA、滑动阈值相关分析、聚合物性质筛选、开源数据集规则、规则归纳、多性能交集、生成prompt、气体渗透率. Preserve Weihao Wang’s pinned implementation, original star-containing SMILES and source-only selection for new data."
---

# STCA skill

[规则库](assets/rule_library/index.md) · [三种使用路径](references/agent_workflows.md) · [后台运行](references/platform-runtime.md) · [方法](references/algorithm.md) · [案例](references/case_studies.md)

将用户的自然语言请求完成为下面三种路径。版本保持 `0.1.0`。全部功能由自然语言请求触发。agent 读取规则、复用或自动准备兼容后台、运行计算并交付文件；普通用户只需说明目标或上传 CSV，不承担命令、Python 版本、文件路径或模型部署操作。STCA 计算使用 CPU，生成沿用当前宿主 LLM，无需 GPU。

| 用户目标 | 默认路径 | 交付 |
|---|---|---|
| 直接采用现成结论筛选或查看规则 | 读取内置规则库，选择性质、方向、档位和来源 | 完整条件、来源、候选结果或现成 prompt |
| 从自己的数据得到规则 | 对上传 CSV 执行自动清理、ECFP4 划分、source 内归纳与冻结评价 | 新模型、各档规则、实际阈值、完整生成 prompt、评价和审计 |
| 让 LLM 按规则生成候选 | 取现成 prompt，或将一个/多个新规则组合为自包含 prompt | 可直接使用/复制的 prompt，及生成后可计算的核验结果 |

## 1. 直接使用内置规则

先读 [规则索引](assets/rule_library/index.md) 与 `assets/rule_library/catalog.json`。从真实目录选择条目；用 `scripts/rule_library.py list` 查找，用 `show ID` 读取精确条件。不要凭评估表、旧对话或规则名称推测条件。

规则库包含 13 项开源数据集性质任务各 Top 10%、15%、20%、25%、30% 条目、11 条论文 Tg/EC 条目及作者归档 gap 规则；每项的可用状态、数值阈值、出处和版本以目录为准。保持论文规则、归档规则和自动归纳规则的来源标签。目录中无有效规则时如实说明，并可转到上传数据路径。

按用户指定的性质、方向和档位选择规则；未指定档位时展示可用选择及对应物理阈值。`high/low` 表示目标方向，百分位表示源数据目标尾部，不是候选入选比例。各性质可独立选档，不默认绑定 5%。

查看条件、读取/复制已存 prompt 无需科学计算依赖。筛选候选时由 agent 通过后台执行 `rule_library.py screen ID [ID ...]`，将多个规则作用于同一批原始结构并保留各项失败条件与 AND 交集。已有规则直接应用，不重新划分候选或重新拟合。

## 2. 上传自己的 CSV 自动归纳

读取表头和样例，确定结构列、目标列、单位、方向及实测/计算来源。标识列可任意命名或省略；沿用原值。优先从文件和上下文读取信息，只询问无法可靠确定且会影响计算的事项。

通过 `scripts/agent_runtime.py run --script auto_screen.py -- ARGS` 完成后台计算。默认自动生成缺少的角色、采用 `--transform auto --scan-policy nested`，比较用户指定档位；用户未指定探索范围时提供并计算 10%、15%、20%、25%、30%。保留已有明确角色与用户规定的绝对目标。

自动清理不能计算的结构、无效目标和可确认的重复导出行，逐行保存原因与映射。保留有效极端值、条件及重复观测；处理历史、邻居偏离和重复冲突先标记。详细策略见 [custom_data.md](references/custom_data.md)。

ECFP4 使用 Morgan radius=2、2048 位，只用于数据划分及相关结构诊断；规则使用 H-cap 后的 MACCS167。在 source 内构造 inner validation，完成尺度、步长和扫描配置选择，再冻结模型评价 holdout。档位建议依据 source 内证据，不使用 holdout 得分挑选配置或改动切分。

学习后由 agent 对各有效档位自动导出完整中英文生成 prompt，与模型和规则一并交付；无需用户另行请求导出或指定脚本路径。交付每档实际物理阈值、完整规则、计数、评价状态及源内推荐。正例少是证据限制，不是禁止归纳或筛选的门槛；区分无规则、零覆盖、零正例、计算错误与 undefined 指标。需要精确保留既有参数/角色时采用 `custom_fit.py`。

## 3. 取 prompt、生成并核验

现成规则直接执行 `rule_library.py prompt ID --language zh-CN`，或读取条目指向的 prompt 文件，完整交付可复制文本。用户只要 prompt 时，到此完成，不强制安装计算依赖。

自定义数量、偏好、多目标或新归纳规则时，将精确约束传给 `scripts/generation_prompt.py --constraints FILE [FILE ...] --count 20 --language zh-CN --output FILE`。新模型先通过 `stca_tools.py export-rules` 导出所选档位约束。prompt 必须自包含来源、目标、阈值、全部 AND 条件、MACCS 语义、原始星号 SMILES 输出格式和生成后核验要求。

用户一句话要求生成并核验时，连续完成规则选择、prompt 准备、当前宿主 LLM 提案与计算核验，不拆成用户需要手动衔接的命令步骤；用户要求其他 LLM 使用时，交付可复制 prompt。无需 STCA 专用生成模型或外部 API。保留所有原始提案、生成预算与失败记录，再用同一组冻结规则计算核验；明确区分“已提出”和“已通过核验”。

多目标逐项显示结果与最终交集，保留冲突条件。规则匹配表示候选满足结构条件，性质是否达到目标仍需实验或相应物性计算。详见 [agent_workflows.md](references/agent_workflows.md) 和 [generation.md](references/generation.md)。

## 共同约定

- 始终保留原始带 `*` 的重复单元 SMILES；H-cap 仅为计算副本，最终候选结果返回原结构。MACCS 保持 167 位原编号、K0 位置及特殊计数语义。
- ID 只用于记录对应，不是特征或材料身份。分组保护同时检查原始 canonical 重复单元、H-cap 碰撞及显式材料分组；保留连接点和测量条件。
- 保持作者实现固定提交 `5951b0ef23d63edc8f7e803aaaffa5e4168288f6`；把论文复现、开源数据归纳和跨性质迁移分别记录。迁移需明确 source/target 性质及假设。
- 输入只读，输出另存；保存来源、规则版本、哈希、角色、变换及参数。用户数据和逐材料结果不写回 skill。
- 默认复用 Python 3.10 及以上的兼容环境，并通过所需功能检查；固定依赖快照仅用于用户明确要求的历史环境复现，不作为普通任务门槛。将计算准备交给 `scripts/agent_runtime.py`；不要要求普通用户写脚本、设置 Python 路径或在终端安装依赖。宿主能力边界见 [platform-runtime.md](references/platform-runtime.md)。

## 按需读取

- [agent_workflows.md](references/agent_workflows.md)：三路径内部步骤、命令和交付。
- [platform-runtime.md](references/platform-runtime.md)：agent 自动发现/准备后台，及纯对话宿主的使用方式。
- [algorithm.md](references/algorithm.md)、[custom_data.md](references/custom_data.md)：原算法、角色、源内适配和评价细节。
- [commands.md](references/commands.md)：低层命令；[provenance.md](references/provenance.md)：来源与版本。
- [case_studies.md](references/case_studies.md)、[validation.md](references/validation.md)：数据集案例与实际验证；[generation.md](references/generation.md)：生成约束语义。
