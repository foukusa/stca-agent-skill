# STCA 安装与调用

**版本 0.1.0** · [English](INSTALL.md) · [返回首页](../README.zh-CN.md)

## 目录

- [选择安装包](#选择安装包)
- [更新已有安装](#更新已有安装)
- [Codex](#codex)
- [DeepSeek Harness](#deepseek-harness)
- [WorkBuddy](#workbuddy)
- [ChatGPT 桌面端](#chatgpt-桌面端)
- [计算环境](#计算环境)
- [WorkBuddy 文件权限](#workbuddy-文件权限)
- [保存与继续使用](#保存与继续使用)
- [自然语言使用案例](USAGE.zh-CN.md)

## 选择安装包

按所用平台选择下方步骤。所有安装包链接都打开本 GitHub 仓库 [downloads 目录](https://github.com/foukusa/stca-agent-skill/tree/main/downloads)中的文件页。在文件页点击 **Download raw file**（下载按钮），将 ZIP 或 TGZ 保存到本地；也可在[仓库首页](https://github.com/foukusa/stca-agent-skill)选择 **Code → Download ZIP**，解压后从 `downloads` 找到对应发行文件。WorkBuddy 商店链接将在发布后补充。

| 平台 | 下载 |
|---|---|
| Codex | [stca-codex-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-codex-0.1.0.zip) |
| DeepSeek Harness：本地 skill | [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) |
| DeepSeek Harness：图形界面插件 | [dsh-plugin-stca-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.zip) |
| DeepSeek Harness：CLI 插件 | [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz) |
| WorkBuddy | [stca-workbuddy-0.1.5.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.5.zip) |
| ChatGPT 桌面端 | [stca-openai-skill-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-openai-skill-0.1.0.zip) |

所有 STCA 功能均可用自然语言调用。AI 助手会查找计算环境，安装时不需要填写 Python 路径。

## 更新已有安装

STCA 核心版本仍为 **0.1.0**，需要替换或重新导入更新后的文件才能使用修正；仅看版本号不能确认已经更新。操作前先保存导出的规则包和任务结果。

- **Codex 文件夹安装：** 用新版完整 `stca` 文件夹替换原安装目录，将 `SKILL.md`、`scripts`、`references` 和 `assets` 一起更新。已保存的规则与结果保留在安装目录外的任务文件夹中。
- **DeepSeek Harness：** 在插件管理中检查 STCA 的安装来源，使用当前可用的更新或替换操作。若仍保留旧副本，仅移除 STCA 插件，再用 `github:foukusa/stca-agent-skill` 添加。DSH 的 profile、配置、数据和保存的规则均保留。
- **WorkBuddy：** 导入 `stca-workbuddy-0.1.5.zip`，启用更新后的 STCA 条目。
- **ChatGPT：** 当前客户端支持本地 skill 导入时，通过已有 skill 管理入口重新导入新版 OpenAI skill ZIP。

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

当前推荐在 **插件 → 添加插件** 中直接填写下方 GitHub 安装地址。**GitHub 安装不需要先发布 npm 包**；DSH 从仓库根目录读取 `package.json`、插件入口和完整 skill。插件中心链接：—（上架后补充）。

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

### 从 GitHub 安装

1. 在 DSH 打开 **插件 → 添加插件**。
2. 填写下面的 GitHub 安装地址，点击安装：

```text
github:foukusa/stca-agent-skill
```

3. 安装并在当前 profile 启用 STCA，然后输入 `/stca` 或“开始使用 STCA”。

在此输入框使用上面的 `github:` 地址。`/tree/main` 浏览页面和终端命令都不是安装地址。尚未发布 npm 时继续使用这个 GitHub 入口；只有直接填写 npm 包名 `dsh-plugin-stca` 才要求该包已在 npm 发布。

### 可选：下载插件 ZIP 后按本地目录安装

1. 下载 [dsh-plugin-stca-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.zip)，在仓库文件页点击 **Download raw file**，然后解压。
2. 在 **插件 → 添加插件** 中填写解压后插件文件夹的完整路径，例如：

```text
/Users/你的用户名/Downloads/dsh-plugin-stca-0.1.0
```

3. 该目录应直接包含 `package.json`、`dsh` 和 `skills`。安装并启用后输入 `/stca`。

也可在[源码仓库](https://github.com/foukusa/stca-agent-skill)选择 **Code → Download ZIP**，解压后填写直接包含 `package.json` 的仓库根目录路径。使用实际用户名和解压位置。

### 可选：CLI 从 GitHub 安装

使用终端中的 DSH CLI 时，可以明确指定包名与 GitHub 来源：

```bash
dsh plugin --profile web add 'dsh-plugin-stca@github:foukusa/stca-agent-skill'
```

**这条命令仍从 GitHub 安装，不需要 npm 发布。** `plugin` 是 DSH 的命令名称，`@github:...` 指定 GitHub 来源。`web` 换成实际 profile。这是终端命令，不放进图形界面的输入框；图形界面填写上面的 `github:` 地址。

### npm 包名：发布后可用

只有 npm 发布成功后，才在 **插件 → 添加插件** 中填写：

```text
dsh-plugin-stca
```

对应的 CLI 命令是 `dsh plugin --profile web add dsh-plugin-stca`。插件中心链接取得后再补充，不将 npm 未发布误写成 GitHub 无法安装。

### 下载独立 skill ZIP

1. 下载 [stca-deepseek-harness-0.1.0.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) 并解压。
2. 将完整 `stca` 文件夹复制到 DSH 用户 skill 根目录。默认 DSH home 下为 `~/.dsh/skills/stca/SKILL.md`；仅供项目使用时，可放入项目根目录的 `.dsh/skills/stca`。自定义路径时以实际配置为准。
3. 保留 `SKILL.md` 旁的 `scripts`、`references` 和 `assets`，在当前 profile 启用 filesystem skill provider，再输入 `/stca`。

这个 ZIP 是手动放置的 skill 文件夹。上面的插件 ZIP 则包含供“添加插件”读取的 `package.json`；按各自方式安装。

### 可选：CLI 安装本地 TGZ

下载 [dsh-plugin-stca-0.1.0.tgz](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz)；它是已打好的插件包，无需解压或重新打包，也不需要先发布 npm。终端命令填写实际文件绝对路径：

```bash
dsh plugin --profile web add 'dsh-plugin-stca@file:/Users/你的用户名/Downloads/dsh-plugin-stca-0.1.0.tgz'
```

这个命名文件参数仅用于 CLI；图形界面使用仓库地址或解压后的插件目录。

### “无法从依赖变更中确定安装了哪一个包”

这是 DSH 插件管理器在加载 STCA 之前，未能从安装前后的依赖变化中识别唯一目标包。它不表示必须先发布 npm，也与 Python、RDKit 或 STCA 计算无关。

先检查插件列表：已有 STCA 时直接启用，不反复添加；需要替换旧版时，只通过插件管理处理旧 STCA，保留自己的数据、结果和规则包。

pnpm 显示 `Packages: +1` 和 `Done` 说明包安装已完成，但不代表 DSH 已识别到唯一的插件名称。在“添加插件”中使用上面的 `github:foukusa/stca-agent-skill`。早先用 HTTPS 地址安装时遇到此报错，可改用这一地址；列表中已有 STCA 时先启用。仍失败时使用本地插件目录备选方式，并保留完整日志与 DSH 版本。自己的数据、结果和规则包保留。

参见 [DSH 官方插件安装说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.zh.md)与[本地 skill 说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)。

## WorkBuddy

1. 打开 [WorkBuddy](https://www.workbuddy.cn/)，进入 skill 管理界面。
2. 选择添加和上传本地 skill 包。
3. 打开仓库中的 [stca-workbuddy-0.1.5.zip](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.5.zip) 文件页，点击 **Download raw file**。在 WorkBuddy 中选择下载好的 ZIP，完成导入并启用 **STCA 聚合物规则与设计**；保持 ZIP 原样上传。
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

包内包含未修改的作者实现，并按可信文件清单在本地校验。普通计算不再克隆 Git 仓库，也不要求 Git 可执行程序。准备缺失的 Python 依赖时仍可能需要获准访问 PyPI。

正常使用无需填写 Python 路径。希望固定使用某个环境时，直接说“使用这个路径的 Python”，并提供解释器路径；系统会检查并保留这一明确选择，失败时说明原因，不静默换用别处。自动发现和准备均无法完成时，才会说明具体缺少的条件。

读取现成规则和 prompt 不需要 RDKit。结构筛选与精确核验需要 RDKit，总结规则还需数值分析依赖。生成使用当前 AI 助手，无需另外配置 LLM API。计算环境无法运行时，生成提案保留为待核验；环境错误不等于 SMILES 解析失败，也不等于零条规则匹配。

### WorkBuddy 文件权限

为本次任务准备独立文件夹，并将它作为当前工作区。STCA 默认将 WorkBuddy 运行缓存、新保存的规则和输出文件放在任务工作区，并返回实际位置。程序直接校验包内作者源码；执行计算时不应反复 `git clone`、创建伪造的 `.git`，或修改源码验证逻辑。

AI 助手会报告第一条失败操作、涉及路径及实际报错。WorkBuddy 出现权限确认时，核对这一个操作和路径；通过**查看拦截规则**或安全审计记录确认是否存在明确拒绝。仅凭残留的 Git 锁文件，不能确定是哪条平台规则导致失败。不要为继续任务而全局关闭安全保护。

计算完成后，后续保存仍可能被拒绝。此时 STCA 会保留已经产生的模型和筛选文件，并单独说明规则库的保存状态，不把整个任务说成已成功保存。新条目只有在必要文件及其哈希校验完成后才标为可用；不完整条目不能当作已保存规则复用。解决具体权限问题后，再从返回的结果继续。 界面与审计入口见 [WorkBuddy 默认权限与安全沙箱](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes)。

## 保存与继续使用

STCA 通过 LLM 对话工作，可以直接提出规则归纳、筛选或生成任务。目标不明确时，AI 助手再介绍这些用法并补问必要选择。

- **总结规则：** 分别返回 STCA、WRAcc 规则与筛选结果，各档的具体物理阈值、比较符、单位及推荐方法。默认 Top 或 Bottom 10%、20%、30%，也支持自定义百分比。AI 助手保存可复用规则文件，并返回实际保存位置。
- **已有规则筛选：** 请 AI 助手显示相关内置规则，或直接引用刚保存的规则文件。需要选择时，再查看来源与目标。
- **已有规则生成：** 在对话中选定规则，再要求先预览确认 prompt，或直接生成。当前 LLM 提出候选，由计算工具核验结构与规则条件。

在对话中接着说 **“用刚保存的规则筛选这些候选”** 或 **“用这些规则生成”** 即可。换会话或平台时，下载规则包并在新会话上传。完整对话见[自然语言使用案例](USAGE.zh-CN.md)。
