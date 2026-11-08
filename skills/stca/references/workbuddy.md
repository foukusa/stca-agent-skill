# STCA：WorkBuddy 使用说明

版本 **0.1.0**。本包将 STCA 的内置规则、自动规则学习和生成 prompt 流程交给 WorkBuddy agent 执行。用户启用 skill、提供 CSV 并提出目标，宿主负责计算依赖和后端准备。

## 加载 STCA

在 WorkBuddy 的 skill 管理入口安装或启用 STCA。已有市场条目时按平台的安装流程使用；加载本地包时，采用当前客户端提供的导入方式。开放平台的 ZIP 提交流程用于发布者，不作为所有客户端统一的本地安装入口。

本地包保留一个完整 `stca/` 目录：`SKILL.md` 与 `scripts/`、`references/`、`assets/` 同级。需要文件夹导入的宿主使用该目录；需要包文件的入口使用对应的 `stca-workbuddy-0.1.0.zip`。启用后在任务中写“使用 STCA skill”。

首次计算由 WorkBuddy agent 按 skill 指令自动检查并准备后端，之后复用可用环境。用户提供输入文件和目标即可；准备受权限限制时，agent 应说明具体阻碍与下一步。

## 三种自然语言调用

**应用内置规则：**

```text
使用 STCA skill，先列出内置规则及其百分比。
选择 paper-tg-high-20 和 paper-ec-low-10，筛选上传的 candidates.csv。
结构列为 SMILES，保留原始星号，返回单项判断、同时匹配的候选和每条失败条件。
```

**上传 CSV 自动归纳：**

```text
使用 STCA skill，从 materials.csv 学习高热导率规则。
结构列为 SMILES，目标列为 ThermalConductivity，单位 W/(m K)，来自计算。
探索 Top 10%、15%、20%、25%、30%，自动准备数据和选择设置。
返回可复用规则、模型、物理阈值，以及完整生成 prompt。
```

**直接提供生成 prompt：**

```text
使用 STCA skill，将 gas-co2-high-15 的条件写成可直接复制到其他 LLM 的完整 prompt。
要求生成 20 个有两个末端 * 连接点的重复单元，按 CandidateKey、SMILES 两列 CSV 返回。
收到生成结果后，按相同规则逐条核验并返回失败条件。
```

随包有 **77 条冻结规则、154 份中英文 prompt**，包括全部 13 项公开数据性质任务的规则。可直接查看 [skill 内规则目录](../assets/rule_library/index.md)。标识列可选、名称任意；每个目标独立指定方向和百分比，保留原始带星号 SMILES。

当前 LLM 或其他 LLM 都可以使用导出的文字 prompt；自动学习与结构核验在启用 STCA 的宿主中完成。

## 官方依据

- [WorkBuddy skill 查看、安装与已安装管理](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)
- [WorkBuddy 开放平台包结构与发布提交格式](https://open.workbuddy.cn/docs/skill)
