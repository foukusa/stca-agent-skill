# STCA：DeepSeek Harness 使用说明

版本 **0.1.0**。本包用于能够加载本地 skill 的 **DeepSeek Harness** agent 宿主。用户安装 STCA、提供 CSV 并发出自然语言请求；依赖准备、计算和模型管理由宿主 agent 按 STCA 指令完成。

## 安装与文件层级

解压 DeepSeek Harness 对应包，保留完整 `stca` 目录。其中 `SKILL.md` 与 `scripts/`、`references/`、`assets/` 同级。

官方本地 skill 提供方支持在其扫描根目录下放置 `<name>/SKILL.md`。Mac 的默认用户位置为 `~/.dsh/skills/stca/SKILL.md`，项目位置为 `<项目>/.dsh/skills/stca/SKILL.md`；自定义 skill 目录按宿主配置使用。Mac 可在 Finder 中选择“前往文件夹”打开对应位置，再复制完整 `stca` 文件夹。保留一层 `stca/SKILL.md`，让 Harness 能在当前会话发现 `stca`。

加载后用 `/stca` 发起任务。宿主负责自动检查和准备计算后端，并复用可用环境；用户直接描述材料目标和上传输入。若宿主权限阻止准备，agent 应报告具体阻碍与可执行的下一步。

## 三种自然语言调用

**使用内置规则：**

```text
/stca 列出内置规则及百分比。我选择 gas-co2-high-15。
按 SMILES 列筛选上传的 candidates.csv，保留原始星号结构，返回匹配候选和每条失败条件。
```

**从 CSV 学习规则：**

```text
/stca 从上传的 materials.csv 自动学习规则。结构列为 SMILES，目标列为 Permeability，
单位 Barrer，来自实验，方向 high。探索 Top 10%、15%、20%、25%、30%。
返回规则、物理阈值、可复用模型和完整生成 prompt。
```

**直接取得生成 prompt：**

```text
/stca 将 gas-co2-high-15 转成可复制到其他 LLM 的完整生成 prompt，
要求 20 个具有两个末端 * 连接点的重复单元，按 CandidateKey、SMILES 两列 CSV 返回。
我回传生成结果后，再按同一规则核验。
```

随包有 **77 条冻结规则和 154 份中英文 prompt**，其中全部 13 项公开数据性质任务已有现成规则。直接选择 [skill 内规则目录](../assets/rule_library/index.md)，或让 `/stca` 列出可用项。每个性质独立选择方向和百分比；ID 可选，原始星号 SMILES 保留。

导出的文字 prompt 可以在任意 LLM 中使用；自动学习和结构核验由已加载 STCA 的 Harness 完成。

## 官方依据

- [DeepSeek Harness 本地 skill 格式与扫描目录](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)
- [DeepSeek Harness skill 加载与 `/name` 调用](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md)
