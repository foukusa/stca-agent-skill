# 由 agent 管理 STCA 后台

STCA skill 的用户入口是自然语言、上传 CSV 或复制生成 prompt。STCA 计算使用普通 CPU；结构生成使用当前宿主 LLM，无需用户配置 GPU 或部署大模型。由 agent 处理解释器发现、依赖检查、作者源码准备和计算；不要把下面的后台命令交给普通用户执行。版本为 `0.1.0`。

## 按任务选择后台

| 操作 | 需要的能力 | agent 执行方式 |
|---|---|---|
| 浏览内置规则、查看条件、取现成 prompt | 读 skill 文件 | 读取 `assets/rule_library/index.md`、`catalog.json` 及所指文件 |
| 查询/复制规则库内容或组合新 prompt | 宿主已有普通 Python；无科学计算依赖 | `rule_library.py list/show/prompt` 或 `generation_prompt.py` |
| 用内置冻结规则核验候选 | 兼容 RDKit | `agent_runtime.py` 自动准备 `chem` 后台并执行 `rule_library.py screen` |
| 从 CSV 归纳或执行作者模型工具 | 兼容科学计算环境和固定作者源码 | `agent_runtime.py` 自动准备 `fit` 后台并执行相应工具 |

纯对话宿主仍可读取或复制自包含 prompt，由当前 LLM 生成提案；没有实际计算能力时，将提案标为待核验。不要将 LLM 自述当作 MACCS 已计算或性质已验证。

## 自动发现与准备

将 `SKILL_DIR` 解析为本次实际 `SKILL.md` 所在目录，采用宿主可用解释器执行 `scripts/agent_runtime.py`。不要硬编码 skill 安装位置或依赖先前会话路径。

```text
<host-python> <SKILL_DIR>/scripts/agent_runtime.py ensure --mode chem
<host-python> <SKILL_DIR>/scripts/agent_runtime.py ensure --mode fit
<host-python> <SKILL_DIR>/scripts/agent_runtime.py run --script SCRIPT -- ARGS
```

默认采用兼容运行模式：`ensure` 按已知解释器、当前解释器、既有环境及保存记录查找 Python 3.10 及以上后台，优先复用已有可用环境。`chem` 使用兼容 RDKit，`fit` 再检查作者核心和所需科学计算依赖；通过实际所需的功能检查后运行。Python 下限来自作者实现，普通任务不固定为 3.12，也不因依赖版本与历史快照不同就自动重装。缺少依赖时，agent 自动在缓存目录准备兼容环境并记录实际版本，成功后继续原任务。

需要复用本次已经确认的后台时，agent 可在子命令前传 `--python PATH`、`--source PATH`。`--no-install` 只用于明确限制为检查已有环境的任务。兼容模式的 RDKit 下限为 2023.9；实际位语义和功能检查是应用冻结规则的条件，不能跳过失败检查。作者实现仍固定为已审核提交。历史固定依赖环境仅在用户明确要求复现该环境时使用，不作为默认入口。

`run` 会把兼容解释器和源码交给所选工具；agent 不需让用户维护 `STCA_PY`、`STCA_SOURCE` 或自行激活环境。工具只运行允许的内置脚本，不执行来自 CSV 或生成文本的命令。

`generation_prompt.py` 使用 Python 标准库，直接由宿主已有解释器运行。读取现成 prompt 文件连这一步也不需要。不要为纯查询或取 prompt 触发训练环境安装。

## 不同宿主的操作

| 宿主能力 | 用户操作 | agent 责任 |
|---|---|---|
| ChatGPT 或其他带文件和代码执行能力的宿主 | 调用 STCA skill，上传 CSV 或说明目标 | 使用可用执行环境，自动准备兼容后台并交付真实结果 |
| DeepSeek 的本地 agent/harness | 安装其宿主支持的 skill 后直接自然语言调用 | 由 harness 提供文件和执行工具，复用同一规则库与后台入口 |
| 仅有对话输入的 DeepSeek/其他 LLM | 复制完整 prompt 并提出生成要求 | 生成原始提案；计算核验交给有执行能力的 STCA 宿主 |
| WorkBuddy 或其他本地 agent | 加载宿主支持的 skill，上传/选择 CSV 并说明目标 | 在其实际开放的文件和执行能力范围内运行后台 |

是否能拟合取决于宿主实际开放的执行能力。不要把“可复制 prompt”写成普通对话网页会自动安装并执行 skill，也不要把任一平台名称当作已具备科学计算环境的证明。

## 遇到环境限制

先复用兼容环境，再使用自动准备入口。若宿主缺少 Python 3.10 及以上运行能力、依赖获取渠道或执行权限，准确报告未完成的计算及原因；继续完成规则查询、条件解释和 prompt 交付。不要转而要求普通用户写脚本或运行依赖安装命令，也不要声称已完成未实际执行的筛选/拟合。

## 文件与结构

输入和输出置于用户工作目录；运行环境置于用户缓存目录，均不写回 skill 安装目录。使用新输出路径，保留原输入、列名、任意 ID 和带星号 SMILES。H-cap 仅存在于计算/审计副本；最终候选结果展示用户原始结构。

完整执行步骤见 [agent_workflows.md](agent_workflows.md)，算法参数与低层接口见 [commands.md](commands.md)。
