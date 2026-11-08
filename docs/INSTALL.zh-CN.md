# STCA 安装与调用：Mac

**版本 0.1.0** · [English](INSTALL.md) · [返回首页](../README.zh-CN.md)

## 目录

- [选择安装包](#选择安装包)
- [ChatGPT](#chatgpt)
- [Codex](#codex)
- [DeepSeek Harness](#deepseek-harness)
- [WorkBuddy](#workbuddy)
- [保存与继续使用](#保存与继续使用)
- [自然语言使用案例](USAGE.zh-CN.md)

## 选择安装包

| 使用平台 | 下载 |
|---|---|
| ChatGPT 或 Codex | [stca-openai-skill-0.1.0.zip](../downloads/stca-openai-skill-0.1.0.zip?raw=true) |
| DeepSeek Harness | [stca-deepseek-harness-0.1.0.zip](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true) |
| WorkBuddy | [stca-workbuddy-0.1.0.zip](../downloads/stca-workbuddy-0.1.0.zip?raw=true) |

ChatGPT 和 Codex 的独立 skill 文件内容相同；上面的 OpenAI ZIP 可用于两端，按各自客户端的安装方式加载。所有功能都可用自然语言调用；计算使用 CPU，AI 助手会复用兼容的 Python 3.10 及以上环境并准备所需依赖，无需用户执行命令。

## ChatGPT

1. 打开 [ChatGPT](https://chatgpt.com/)，进入 **Plugins → Skills**。
2. 选择 **Create → Upload from your computer**。
3. 在 Mac 文件窗口选择 `stca-openai-skill-0.1.0.zip`，点击“打开”，按页面提示完成创建。
4. 选择 STCA，输入“开始使用 STCA”。

创建和上传入口依账号与工作区权限开放，见 [ChatGPT 官方帮助](https://help.openai.com/en/articles/20001066-skills-in-chatgpt/)。已从公开目录安装 STCA 时，选择它即可开始。

## Codex

可直接在 Codex 对话中请求安装：

```text
使用 $skill-installer 安装 https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

安装后输入“使用 $stca”。若采用本地文件：

1. 在 Finder 双击同一份 `stca-openai-skill-0.1.0.zip`，得到完整 `stca` 文件夹。
2. 用 Finder 的“前往 → 前往文件夹”打开已有的 `~/.agents/skills`。
3. 复制完整 `stca` 文件夹，保留 `stca/SKILL.md` 及同级配套目录。
4. 回到 Codex，选择 STCA 或输入“使用 $stca”。没有本地 skill 目录时，可采用上面的自动安装请求。

参见 [OpenAI 官方 skill 说明](https://learn.chatgpt.com/docs/build-skills)。

## DeepSeek Harness

1. 使用已配置的 [DeepSeek Harness](https://www.deepseek.com/harness/)。
2. Finder 双击 DeepSeek ZIP，得到完整 `stca` 文件夹。
3. 在 Finder 按 **Command＋Shift＋G**（“前往文件夹”），输入已配置的 skill 根目录，默认是 `~/.dsh/skills`，按 Return 打开。
4. 若 Finder 提示路径不存在，先在 Harness 中请 AI 助手创建默认用户 skill 目录或确认实际扫描目录，再用 Finder 打开该位置。
5. 将完整 `stca` 文件夹复制进去，形成 `stca/SKILL.md`，保留同级的 `scripts`、`references`、`assets`。
6. 在 Harness 对话中输入 `/stca`。

目录配置见 [DeepSeek 官方说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)。完整生成 prompt 可复制到普通 DeepSeek 对话中使用。

## WorkBuddy

1. 打开 [WorkBuddy](https://www.workbuddy.cn/)，进入 skill 管理界面。
2. 选择 **添加 → 上传** 本地 skill 包。
3. 在 Mac 文件窗口选择 WorkBuddy ZIP，点击“打开”，完成导入并启用 STCA。
4. 输入“开始使用 STCA”。

具体界面见 [WorkBuddy 官方说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。

## 保存与继续使用

主菜单依次为 **1 上传数据总结规则、2 已有规则筛选、3 已有规则生成**。

- 选 1：默认在你的数据范围内比较 STCA 与 WRAcc，逐档返回主推／备选、物理阈值及两种方法的原表筛选结果；独立候选表结果另列。保留原始 SMILES、每条失败条件和不可计算记录，自动保存规则并返回主菜单。
- 选 2：从内置规则或“我的规则”中选择，筛选上传的候选表。
- 选 3：先显示可选规则目录及方法、主推／备选。选定规则后，选择**先预览，确认后生成**，查看并调整完整 prompt，回复“确认，开始生成”后执行；或选择**直接生成**，让当前 LLM 立即生成并核验。两种方式都保留全部提案和失败条件，完成后返回菜单。无需另外配置 LLM API。

内置开源任务提供 Top 10%、20%、30%；自己的数据可学习 15%、25% 等其他档位。

可直接复制[自然语言使用案例](USAGE.zh-CN.md)中的短请求。

输入“返回主菜单”或“上一级”不会删除已保存规则。需要换会话或平台时，下载规则包并在新会话上传；让 AI 助手载入后继续使用。
