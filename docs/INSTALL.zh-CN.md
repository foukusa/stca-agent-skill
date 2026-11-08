# STCA 安装与调用

**版本 0.1.0** · [English](INSTALL.md) · [返回首页](../README.zh-CN.md)

## 目录

- [选择安装包](#选择安装包)
- [Codex](#codex)
- [DeepSeek Harness](#deepseek-harness)
- [WorkBuddy](#workbuddy)
- [ChatGPT 桌面端](#chatgpt-桌面端)
- [计算环境](#计算环境)
- [保存与继续使用](#保存与继续使用)
- [自然语言使用案例](USAGE.zh-CN.md)

## 选择安装包

按所用平台选择下方步骤。所有安装包链接都打开本 GitHub 仓库 [downloads 目录](https://github.com/foukusa/stca-agent-skill/tree/main/downloads)中的文件页。在文件页点击 **Download raw file**（下载按钮），将 ZIP 或 TGZ 保存到本地；也可在[仓库首页](https://github.com/foukusa/stca-agent-skill)选择 **Code → Download ZIP**，解压后从 `downloads` 找到对应发行文件。WorkBuddy 商店链接将在发布后补充。

| 平台 | 下载 |
|---|---|
| Codex | [stca-codex-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-codex-0.1.0.zip) |
| DeepSeek Harness：本地 skill | [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) |
| DeepSeek Harness：插件 | [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz) |
| WorkBuddy | [stca-workbuddy-0.1.1.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.1.zip) |
| ChatGPT 桌面端 | [stca-openai-skill-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-openai-skill-0.1.0.zip) |

所有 STCA 功能均可用自然语言调用。AI 助手会查找计算环境，安装时不需要填写 Python 路径。

## Codex

1. 打开 Codex 对话。
2. 通过 GitHub 安装时，发送：

```text
使用 $skill-installer 安装 https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

3. 也可下载并解压 `stca-codex-0.1.0.zip`，将其中完整的 `stca` 文件夹放到个人 skill 目录，最终应有：

```text
~/.agents/skills/stca/SKILL.md
```

在 Finder 中选择 **前往 → 前往文件夹…**，输入 `~/.agents/skills`；目录不存在时先创建，再放入完整 `stca` 文件夹。只在某个项目中使用时，可放在该项目的 `.agents/skills/stca`。保留 `SKILL.md` 旁的 `scripts`、`references` 和 `assets`。

4. 在 Codex 中打开 `/skills`，或输入 `$stca` 选择 STCA，然后发送：

```text
使用 $stca，开始使用 STCA。
```

Codex 如何发现和调用 skill，参见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。

## DeepSeek Harness

在 **插件 → 添加插件** 中可填写 GitHub 仓库地址，或在 npm 发布后填写包名 `dsh-plugin-stca`。插件中心链接：—（上架后补充）。也可下载 skill ZIP 手动安装，安装后均通过 `/stca` 调用。

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

### Git 安装

1. 打开 **插件 → 添加插件**。
2. 填写以下仓库地址，完成安装：

```text
https://github.com/foukusa/stca-agent-skill.git
```

3. 在当前使用的 profile 中启用 STCA，输入 `/stca`。

使用 DSH CLI 和 `web` profile 时，对应的源码安装命令为：

```bash
dsh plugin --profile web add github:foukusa/stca-agent-skill
```

使用其他 profile 时，将 `web` 换成实际名称。GitHub 的 `/tree/main` 是浏览网页地址；“添加插件”中应使用上面的仓库地址。

### npm 包名安装

npm 发布完成后，在 **插件 → 添加插件** 的同一输入框填写：

```text
dsh-plugin-stca
```

CLI 对应命令为：

```bash
dsh plugin --profile web add dsh-plugin-stca
```

插件中心入口暂留空，取得实际公开链接后补充。

### 下载 skill ZIP

1. 下载 [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) 并解压。
2. 将完整 `stca` 文件夹复制到 DSH 用户 skill 根目录。使用默认 DSH home 时，最终路径为 `~/.dsh/skills/stca/SKILL.md`；仅供项目使用时，可放入项目根目录的 `.dsh/skills/stca`。自定义 DSH home 或 skill 目录时，以实际配置为准。
3. 保留 `SKILL.md` 旁的 `scripts`、`references` 和 `assets`；当前 DSH profile 需启用本地文件 skill 提供器。
4. 输入 `/stca` 或“开始使用 STCA”。

skill ZIP 采用解压后放置文件夹的方式安装，不应将 ZIP 填进“添加插件”地址框。

### 下载插件 TGZ

希望通过“添加插件”安装、又不使用 Git 时，可下载 [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz)，在“添加插件”中填写该文件的完整本地路径。使用 CLI 时，在下载文件所在目录执行：

```bash
dsh plugin --profile web add ./dsh-plugin-stca-0.1.0.tgz
```

TGZ 已经是插件包，无需解压或重新打包。

参见 [DSH 官方插件安装说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.zh.md)与[本地 skill 说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)。

## WorkBuddy

1. 打开 [WorkBuddy](https://www.workbuddy.cn/)，进入 skill 管理界面。
2. 选择添加和上传本地 skill 包。
3. 打开仓库中的 [stca-workbuddy-0.1.1.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.1.zip) 文件页，点击 **Download raw file**。在 WorkBuddy 中选择下载好的 ZIP，完成导入并启用 **STCA 聚合物规则与设计**；保持 ZIP 原样上传。
4. 输入“开始使用 STCA”。

包内按上传目录要求提供所引用的启动资源和 logo。公开商店安装链接将在审核通过并发布后补充。

具体界面见 [WorkBuddy 官方说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。

## ChatGPT 桌面端

1. 打开本仓库的 [OpenAI skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-openai-skill-0.1.0.zip) 文件页，点击 **Download raw file**。
2. 若当前 ChatGPT 桌面客户端提供本地 skill 创建／导入入口，在该入口导入 ZIP 并启用 STCA；是否开放取决于客户端及账号。
3. 选择 STCA 并说明任务。计算需要文件访问与命令执行环境；普通文件附件本身不会完成 skill 的安装或运行。

OpenAI skill ZIP 与 Codex skill ZIP 包含相同的 STCA 工作流程。当前客户端没有本地 skill 导入入口时，可按上面的 Codex 步骤安装。参见 [OpenAI 官方 skill 说明](https://learn.chatgpt.com/docs/build-skills)。

## 计算环境

计算支持 CPU 与 Python 3.10 及以上环境，不要求 Conda。首次计算时，AI 助手会自动查找合适的本地 Python，检查本次任务需要的依赖。可以复用已有 RDKit 环境，包括发现的 Conda 环境，并记住成功的选择。缺少依赖且平台允许准备时，会创建独立环境，不修改已有环境。

正常使用无需填写 Python 路径。希望固定使用某个环境时，直接说“使用这个路径的 Python”，并提供解释器路径；系统会检查并保留这一明确选择，失败时说明原因，不静默换用别处。自动发现和准备均无法完成时，才会说明具体缺少的条件。

读取现成规则和 prompt 不需要 RDKit。结构筛选与精确核验需要 RDKit，总结规则还需数值分析依赖。生成使用当前 AI 助手，无需另外配置 LLM API。计算环境无法运行时，生成提案保留为待核验；环境错误不等于 SMILES 解析失败，也不等于零条规则匹配。

## 保存与继续使用

STCA 通过 LLM 对话工作，可以直接提出规则归纳、筛选或生成任务。目标不明确时，AI 助手再介绍这些用法并补问必要选择。

- **总结规则：** 分别返回 STCA、WRAcc 规则与筛选结果，各档的具体物理阈值、比较符、单位及推荐方法。默认 Top 或 Bottom 10%、20%、30%，也支持自定义百分比。AI 助手保存可复用规则文件，并返回实际保存位置。
- **已有规则筛选：** 请 AI 助手显示相关内置规则，或直接引用刚保存的规则文件。需要选择时，再查看来源与目标。
- **已有规则生成：** 在对话中选定规则，再要求先预览确认 prompt，或直接生成。当前 LLM 提出候选，由计算工具核验结构与规则条件。

在对话中接着说 **“用刚保存的规则筛选这些候选”** 或 **“用这些规则生成”** 即可。换会话或平台时，下载规则包并在新会话上传。完整对话见[自然语言使用案例](USAGE.zh-CN.md)。
