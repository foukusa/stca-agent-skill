# 由 agent 管理 STCA 后台

STCA skill 的用户入口是自然语言、上传 CSV 或复制生成 prompt。STCA 计算使用普通 CPU；结构生成使用当前平台 LLM，无需用户配置 GPU 或部署大模型。由 agent 处理解释器发现、依赖检查、作者源码准备和计算；不要把下面的后台命令交给普通用户执行。版本为 `0.1.0`。

## 按任务选择后台

| 操作 | 需要的能力 | agent 执行方式 |
|---|---|---|
| 浏览内置规则、查看条件、取现成 prompt | 读 skill 文件 | 读取 `assets/rule_library/index.md`、`catalog.json` 及所指文件 |
| 查询/复制规则库内容或组合新 prompt | 平台已有普通 Python；无科学计算依赖 | `rule_library.py list/show/prompt` 或 `generation_prompt.py` |
| 用内置冻结规则核验候选 | 兼容 RDKit | `agent_runtime.py` 自动准备 `chem` 后台并执行 `rule_library.py screen` |
| 从 CSV 归纳或执行作者模型工具 | 兼容科学计算环境和固定作者源码 | `agent_runtime.py` 自动准备 `fit` 后台并执行相应工具 |

纯对话平台仍可读取或复制自包含 prompt，由当前 LLM 生成提案；没有实际计算能力时，将提案标为待核验。不要将 LLM 自述当作 MACCS 已计算或性质已验证。

## 自动发现与准备

将 `SKILL_DIR` 解析为本次实际 `SKILL.md` 所在目录。首次启动由 agent 使用随包原生入口发现 Python，不假定 `python` 或 `python3` 已在 PATH，也不要求用户填写解释器路径。不要硬编码 skill 安装位置或依赖先前会话路径。

macOS/Linux 由 agent 执行：

```text
sh "<SKILL_DIR>/scripts/launch_runtime.sh" ensure --mode chem
sh "<SKILL_DIR>/scripts/launch_runtime.sh" ensure --mode fit
sh "<SKILL_DIR>/scripts/launch_runtime.sh" run --script SCRIPT -- ARGS
```

Windows 使用同目录 `scripts/launch_runtime.ps1`，通过可用 PowerShell 运行并传入相同参数。WorkBuddy 的外层入口先还原随包资源，再进入同一发现与验证流程。

默认兼容模式按明确指定、上次成功记录、当前/激活环境、PATH、未激活 Conda 环境及有限的常见安装位置查找 Python 3.10 及以上后台，不进行全盘扫描。逐个实际检查 RDKit 导入及 MACCS 位语义；`fit` 再检查相应科学计算依赖。找到兼容环境就复用并保存记录；没有可用依赖时，在用户缓存内准备独立环境，成功后继续原任务，不改动其他环境。

用户明确指定 Python 路径时，由 agent 通过 `--python PATH` 使用该解释器；路径不可执行或依赖不满足时明确报告，不静默切换到其他环境。用户只需选择已安装的解释器，无需写命令。`--source PATH` 指定已核实的作者源码；`--no-install` 限制为检查现有环境。环境诊断保留已检查候选及失败原因，普通用户只看到与下一步有关的简短说明。

普通任务不固定 Python 3.12，也不因依赖版本不同于历史快照就自动重装。RDKit 下限为 2023.9，实际功能检查不能跳过；历史锁定模式仅在用户明确要求复现该环境时使用。

`run` 会把兼容解释器和源码交给所选工具；agent 不需让用户维护 `STCA_PY`、`STCA_SOURCE` 或自行激活环境。工具只运行允许的内置脚本，不执行来自 CSV 或生成文本的命令。

`generation_prompt.py` 使用 Python 标准库，直接由平台已有解释器运行。读取现成 prompt 文件连这一步也不需要。不要为纯查询或取 prompt 触发训练环境安装。

## 不同平台的操作

| 平台能力 | 用户操作 | agent 责任 |
|---|---|---|
| ChatGPT 或其他带文件和代码执行能力的平台 | 调用 STCA skill，上传 CSV 或说明目标 | 使用可用执行环境，自动准备兼容后台并交付真实结果 |
| DeepSeek 的本地 agent/harness | 安装其平台支持的 skill 后直接自然语言调用 | 由 harness 提供文件和执行工具，复用同一规则库与后台入口 |
| 仅有对话输入的 DeepSeek/其他 LLM | 复制完整 prompt 并提出生成要求 | 生成原始提案；计算核验交给有执行能力的 STCA 平台 |
| WorkBuddy 或其他本地 agent | 加载平台支持的 skill，上传/选择 CSV 并说明目标 | 在其实际开放的文件和执行能力范围内运行后台 |

是否能拟合取决于平台实际开放的执行能力。不要把“可复制 prompt”写成普通对话网页会自动安装并执行 skill，也不要把任一平台名称当作已具备科学计算环境的证明。

## 遇到环境限制

先复用兼容环境，再使用自动准备入口。一个候选 Python 能启动但 NumPy/RDKit 等二进制库因 macOS Team ID/签名或动态库问题导入失败，不算可用环境；保留诊断并继续检查其他解释器与隔离环境。只有规则筛选/结构核验时使用 chem 后台，不为其强制安装完整拟合依赖。若平台缺少 Python 3.10 及以上运行能力、依赖获取渠道或执行权限，准确报告未完成的计算及原因；继续完成规则查询、条件解释和 prompt 交付。不要转而要求普通用户写脚本或运行依赖安装命令，也不要声称已完成未实际执行的筛选/拟合。

## 文件与结构

输入和输出置于用户工作目录；运行环境置于用户缓存目录，均不写回 skill 安装目录。使用新输出路径，保留原输入、列名、任意 ID 和原始分子 SMILES（包括原有连接点）。H-cap 仅存在于计算/审计副本；最终候选结果展示用户原始结构。

完整执行步骤见 [agent_workflows.md](agent_workflows.md)，算法参数与低层接口见 [commands.md](commands.md)。

当前平台的 skill 是给 LLM 的操作说明，不提供独立固定菜单或“我的规则”页面。直接按用户请求连续处理；只有目标缺失或用户请求任务概览时才简短说明可选操作。文件保存成功后交付真实位置和可下载包。生成已有文本但计算未运行时，报告待核验及原因，不能把运行环境失败当作全部 SMILES 解析失败。
