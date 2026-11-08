# STCA 安装与调用

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

选择使用的 AI 平台，按相应客户端支持的方式安装。

| 使用平台 | 下载 |
|---|---|
| ChatGPT 或 Codex | [stca-openai-skill-0.1.0.zip](../downloads/stca-openai-skill-0.1.0.zip?raw=true) |
| DeepSeek Harness | [stca-deepseek-harness-0.1.0.zip](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true) |
| WorkBuddy | [stca-workbuddy-0.1.0.zip](../downloads/stca-workbuddy-0.1.0.zip?raw=true) |

ChatGPT 和 Codex 使用同一份独立 skill 包。所有功能均可用自然语言调用，AI 助手会准备所需的 CPU 计算环境，无需用户执行安装命令。

## ChatGPT

1. 打开 [ChatGPT](https://chatgpt.com/)，进入 **Plugins → Skills**。
2. 选择 **Create → Upload from your computer**。
3. 选择 `stca-openai-skill-0.1.0.zip`，按页面提示完成创建。
4. 选择 STCA，输入“开始使用 STCA”。

创建和上传入口依账号与工作区权限开放，见 [ChatGPT 官方帮助](https://help.openai.com/en/articles/20001066-skills-in-chatgpt/)。已从公开目录安装 STCA 时，选择它即可开始。

## Codex

可直接在 Codex 对话中请求安装：

```text
使用 $skill-installer 安装 https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

安装后输入“使用 $stca”。若采用本地文件：

1. 用文件管理器解压 `stca-openai-skill-0.1.0.zip`。
2. 将完整 `stca` 文件夹复制到 Codex 配置的 skill 目录。不清楚位置时，让 Codex 确认，或采用上面的自动安装请求。
3. 保留 `SKILL.md`、`scripts`、`references`、`assets` 的完整目录结构。
4. 回到 Codex，选择 STCA 或输入“使用 $stca”。

参见 [OpenAI 官方 skill 说明](https://learn.chatgpt.com/docs/build-skills)。

## DeepSeek Harness

1. 打开 [DeepSeek Harness](https://www.deepseek.com/harness/)，进入 **插件 → 添加插件**。
2. 在地址框粘贴以下 Git 仓库地址，再点安装并启用 STCA：

   ```text
   https://github.com/foukusa/stca-agent-skill.git
   ```

3. 在对话中输入 `/stca` 或“开始使用 STCA”。

也可下载 [DSH 插件 TGZ](../downloads/dsh-plugin-stca-0.1.0.tgz?raw=true)，在同一地址框填写该文件的完整本地路径。该文件已经是可安装插件，无需重新打包。不要在“添加插件”中填写 GitHub 的 `/tree/main` 网页地址或 skill ZIP。

只需要手动放置 skill 时，使用 [本地 skill ZIP](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true)，解压后将完整 `stca` 文件夹复制到 `~/.dsh/skills`，或已配置的项目 skill 根目录。此方式不经过“添加插件”。

参见 [DSH 官方插件安装说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.zh.md)与[本地 skill 说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)。

## WorkBuddy

1. 打开 [WorkBuddy](https://www.workbuddy.cn/)，进入 skill 管理界面。
2. 选择 **添加 → 上传** 本地 skill 包。
3. 直接选择 `stca-workbuddy-0.1.0.zip`，完成导入并启用 STCA；无需解压或套入其他文件夹。
4. 输入“开始使用 STCA”。

具体界面见 [WorkBuddy 官方说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。

## 保存与继续使用

主菜单依次为 **1 上传数据总结规则、2 已有规则筛选、3 已有规则生成**。

- 选 1：分别返回 STCA 与 WRAcc 的规则、每档具体物理阈值、比较符、单位、筛选结果及推荐方法。未定义百分比时使用 Top 或 Bottom 10%、20%、30%，也可自定 15%、25% 等档位。结果保留原表、SMILES、未满足的规则条件及无法计算记录，保存规则后返回菜单。
- 选 2：使用内置规则或“我的规则”筛选候选，两种方法的结果分别返回，并明确推荐方法。
- 选 3：先显示可选规则目录。选定后，可选择**先预览，确认后生成**，查看并调整完整 prompt，回复“确认，开始生成”后执行；或选择**直接生成**，让当前 LLM 立即生成并核验。两种方式都保留全部提案和未满足的规则条件，完成后返回菜单，无需另外配置 LLM API。

可直接复制[自然语言使用案例](USAGE.zh-CN.md)中的短请求。

输入“返回主菜单”或“上一级”会保留已保存规则。需要换会话或平台时，下载规则包并在新会话上传，让 AI 助手载入后继续使用。
