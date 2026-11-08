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

现在可按下列方式直接安装。各平台完成审核并发布后，再补充对应商店的安装链接。

| 平台 | 下载 |
|---|---|
| Codex | [stca-codex-0.1.0.zip](../downloads/stca-codex-0.1.0.zip?raw=true) |
| DeepSeek Harness：本地 skill | [stca-deepseek-harness-0.1.0.zip](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true) |
| DeepSeek Harness：插件 | [dsh-plugin-stca-0.1.0.tgz](../downloads/dsh-plugin-stca-0.1.0.tgz?raw=true) |
| WorkBuddy | [stca-workbuddy-0.1.0.zip](../downloads/stca-workbuddy-0.1.0.zip?raw=true) |
| ChatGPT 桌面端 | [stca-openai-skill-0.1.0.zip](../downloads/stca-openai-skill-0.1.0.zip?raw=true) |

所有 STCA 功能均可用自然语言调用。AI 助手会查找计算环境，安装时不需要填写 Python 路径。

## Codex

**通过 GitHub 安装。** 在 Codex 对话中发送：

```text
使用 $skill-installer 安装 https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

**或使用 ZIP。** 下载并解压 `stca-codex-0.1.0.zip`，将其中完整的 `stca` 文件夹放到个人 skill 目录，最终应有：

```text
~/.agents/skills/stca/SKILL.md
```

只在某个项目中使用时，可放在该项目的 `.agents/skills/stca`。Windows 的个人目录为 `%USERPROFILE%\.agents\skills\stca`。保留 `SKILL.md` 旁的 `scripts`、`references` 和 `assets`，不要只复制 Markdown 文件。

在 Codex 中打开 `/skills`，或输入 `$stca` 选择 STCA，然后发送：

```text
使用 $stca，开始使用 STCA。
```

这是 Codex 本地 skill 安装，无需先向 OpenAI 目录提交审核。将来公开插件目录的上架属于另一条发布流程。参见 [OpenAI 官方 skill 说明](https://learn.chatgpt.com/docs/build-skills)。

## DeepSeek Harness

在 **插件 → 添加插件** 中可填写 GitHub 仓库地址，或在 npm 发布后填写包名 `dsh-plugin-stca`。插件中心链接：—（上架后补充）。也可下载 skill ZIP 手动安装，安装后均通过 `/stca` 调用。

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

### Git 安装

在 **插件 → 添加插件** 中填写以下仓库地址，安装并启用 STCA：

```text
https://github.com/foukusa/stca-agent-skill.git
```

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

1. 下载 [stca-deepseek-harness-0.1.0.zip](../downloads/stca-deepseek-harness-0.1.0.zip?raw=true) 并解压。
2. 将完整 `stca` 文件夹复制到 DSH 用户 skill 根目录。使用默认 DSH home 时，最终路径为 `~/.dsh/skills/stca/SKILL.md`；仅供项目使用时，可放入项目根目录的 `.dsh/skills/stca`。自定义 DSH home 或 skill 目录时，以实际配置为准。
3. 保留 `SKILL.md` 旁的 `scripts`、`references` 和 `assets`；当前 DSH profile 需启用本地文件 skill 提供器。
4. 输入 `/stca` 或“开始使用 STCA”。

skill ZIP 采用解压后放置文件夹的方式安装，不应将 ZIP 填进“添加插件”地址框。

### 下载插件 TGZ

希望通过“添加插件”安装、又不使用 Git 时，可下载 [dsh-plugin-stca-0.1.0.tgz](../downloads/dsh-plugin-stca-0.1.0.tgz?raw=true)，在“添加插件”中填写该文件的完整本地路径。使用 CLI 时，在下载文件所在目录执行：

```bash
dsh plugin --profile web add ./dsh-plugin-stca-0.1.0.tgz
```

TGZ 已经是插件包，无需解压或重新打包。

参见 [DSH 官方插件安装说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.zh.md)与[本地 skill 说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)。

## WorkBuddy

1. 打开 [WorkBuddy](https://www.workbuddy.cn/)，进入 skill 管理界面。
2. 选择添加和上传本地 skill 包。
3. 直接选择 [stca-workbuddy-0.1.0.zip](../downloads/stca-workbuddy-0.1.0.zip?raw=true)，完成导入并启用 **STCA 聚合物规则与设计**；上传前无需解压，也不要套入其他文件夹。
4. 输入“开始使用 STCA”。

包内按上传目录要求提供所引用的启动资源和 logo。公开商店安装链接将在审核通过并发布后补充。

具体界面见 [WorkBuddy 官方说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。

## ChatGPT 桌面端

[OpenAI skill ZIP](../downloads/stca-openai-skill-0.1.0.zip?raw=true) 与 Codex skill ZIP 包含相同的 STCA 工作流程。按桌面客户端开放的 skill 创建或导入方式加载，再选择 STCA。将来发布公开插件后，也可从受支持的插件安装入口加载。参见 [OpenAI 官方 skill 说明](https://learn.chatgpt.com/docs/build-skills)和[插件说明](https://learn.chatgpt.com/docs/plugins)。

## 计算环境

首次计算时，AI 助手会自动查找合适的本地 Python，检查本次任务需要的依赖。可以复用已有 RDKit 环境，包括发现的 Conda 环境，并记住成功的选择。缺少依赖且平台允许准备时，会创建独立环境，不修改已有环境。

正常使用无需填写 Python 路径。希望固定使用某个环境时，直接说“使用这个路径的 Python”，并提供解释器路径；系统会检查并保留这一明确选择，失败时说明原因，不静默换用别处。自动发现和准备均无法完成时，才会说明具体缺少的条件。

读取现成规则和 prompt 不需要 RDKit。结构筛选与精确核验需要 RDKit，总结规则还需数值分析依赖。计算使用 CPU，生成使用当前 AI 助手，无需另外配置 LLM API。

## 保存与继续使用

主菜单依次为 **1 上传数据总结规则、2 已有规则筛选、3 已有规则生成**。

- 选 1：分别返回 STCA 与 WRAcc 的规则、每档具体物理阈值、比较符、单位、筛选结果及推荐方法。未定义百分比时使用 Top 或 Bottom 10%、20%、30%，也可自定 15%、25% 等档位。结果保留原表、聚合物 SMILES、未满足的规则条件及无法计算记录，保存规则后返回菜单。
- 选 2：使用内置规则或“我的规则”筛选候选，两种方法的结果分别返回，并明确推荐方法。
- 选 3：先显示可选规则目录。选定后，可选择**先预览，确认后生成**，查看并调整完整 prompt，回复“确认，开始生成”后执行；或选择**直接生成**，让当前 LLM 立即生成并核验。两种方式都保留全部提案和未满足的规则条件，完成后返回菜单。

可直接复制[自然语言使用案例](USAGE.zh-CN.md)中的短请求。输入“返回主菜单”或“上一级”会保留已保存规则。换会话或平台时，下载规则包并在新会话上传，让 AI 助手载入后继续使用。
