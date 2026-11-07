# STCA · Mac 发布、安装与调用指南

**GitHub · ChatGPT / Codex · DeepSeek Harness · WorkBuddy**  
软件版本：0.1.0　｜　Mac 指南修订：2026-11-07

> **先区分两类文件：** GitHub 仓库保存源码，不在 `main` 文件树中存放平台 ZIP；ChatGPT、DeepSeek 和 WorkBuddy 的 ZIP 由维护者在 Mac 本地构建，再上传到对应平台或作为 GitHub Release 附件。

## 目录

- [0. 文件结构与发布顺序](#0-文件结构与发布顺序)
- [1. GitHub：提交源码文件夹](#1-github提交源码文件夹)
- [2. ChatGPT / Codex：构建并提交插件](#2-chatgpt--codex构建并提交插件)
- [3. DeepSeek Harness：从源码安装与调用](#3-deepseek-harness从源码安装与调用)
- [4. WorkBuddy：本机导入与开放平台发布](#4-workbuddy本机导入与开放平台发布)
- [5. 四个平台如何调用 STCA](#5-四个平台如何调用-stca)
- [6. 修改后重新生成平台包](#6-修改后重新生成平台包)
- [7. 发布前检查清单](#7-发布前检查清单)

## 0. 文件结构与发布顺序

### 0.1 GitHub 源码目录

本地源码目录根层应直接包含：

```text
README.md                 # 英文主 README
README.zh-CN.md           # 中文完整翻译
assets/stca-logo.png      # logo
skills/stca/SKILL.md      # skill 入口
skills/stca/scripts/      # 执行脚本
skills/stca/references/   # 算法、命令与平台说明
plugin.json               # OpenAI 插件元数据
PUBLISH_STEPS.zh-CN.md    # 本指南
```

**不要把平台 ZIP 提交进源码树。** GitHub 仓库用于浏览、版本管理和 `skills.sh` 安装；平台 ZIP 属于构建产物。

### 0.2 平台 ZIP 从哪里来

在源码根目录执行：

```zsh
python3 tools/build_packages.py \
  --output-dir "$HOME/Desktop/STCA-release-0.1.0"
```

生成：

```text
~/Desktop/STCA-release-0.1.0/
├── stca-github-release-0.1.0.zip
├── stca-openai-plugin-0.1.0.zip
├── stca-deepseek-harness-0.1.0.zip
├── stca-workbuddy-0.1.0.zip
├── STCA_logo.png
└── SHA256SUMS.txt
```

用途：

| 文件 | 用途 |
| --- | --- |
| `stca-github-release-0.1.0.zip` | 可选的 GitHub Release 源码归档附件 |
| `stca-openai-plugin-0.1.0.zip` | 上传到 OpenAI 插件发布门户 |
| `stca-deepseek-harness-0.1.0.zip` | 可选的 DeepSeek Harness 下载包 |
| `stca-workbuddy-0.1.0.zip` | WorkBuddy 本机导入与开放平台提交 |
| `STCA_logo.png` | 各平台品牌图标与 Release 附件 |

### 0.3 推荐顺序

1. 修改并核对英文 `README.md`、中文 `README.zh-CN.md`、版本、许可和作者信息。
2. 用 GitHub Desktop 提交并推送**源码目录**。
3. 在 Mac 本地运行构建命令，生成平台 ZIP。
4. 提交 ChatGPT 插件；安装并测试 DeepSeek；导入并提交 WorkBuddy。
5. 建立 GitHub Release 时，可把四份 ZIP 和 logo 作为附件上传，但不要把它们加入 `main` 源码树。

## 1. GitHub：提交源码文件夹

### 1.1 安装 GitHub Desktop

1. 点击苹果菜单 → **关于本机**，确认是 Apple M 系列还是 Intel。
2. 打开 [GitHub Desktop 下载页](https://desktop.github.com/download/)，安装对应 Mac 版本。
3. 打开应用并登录 GitHub。

### 1.2 已经有远程仓库

1. 在浏览器打开 `https://github.com/foukusa/stca-agent-skill`。
2. GitHub Desktop 顶部菜单选择 **File → Clone Repository… → URL**。
3. 粘贴仓库地址。
4. Local Path 可选择：

```text
~/Documents/GitHub/stca-agent-skill
```

5. 点击 **Clone**。

### 1.3 把修正版源码复制进本地仓库

1. Finder 打开修正版 `stca-agent-skill` 源码文件夹。
2. 进入文件夹内部，确认能直接看到 `README.md`、`README.zh-CN.md`、`skills`、`assets`。
3. 按 `⌘⇧.` 显示 `.gitignore`。
4. 在来源目录按 `⌘A`、`⌘C`。
5. Finder 按 `⌘⇧G`，进入 GitHub Desktop 克隆出的本地仓库路径。
6. 按 `⌘V` 覆盖同名发布文件。

目标目录应是：

```text
stca-agent-skill/
├── README.md
├── README.zh-CN.md
├── skills/
└── assets/
```

不能出现：

```text
stca-agent-skill/stca-agent-skill/README.md
```

### 1.4 提交与推送

1. 回到 GitHub Desktop。
2. 在 Changes 中检查：
   - `README.md` 为英文；
   - 新增 `README.zh-CN.md`；
   - logo 仍位于 `assets/stca-logo.png`。
3. Summary 填：

```text
Clarify installation and usage; add bilingual README
```

4. 点击 **Commit to main**。
5. 点击 **Push origin**。

### 1.5 检查 GitHub 页面

刷新仓库网页：

- 首页默认显示英文 `README.md`；
- 顶部可以点击 **简体中文** 进入 `README.zh-CN.md`；
- README 开始部分有可点击目录；
- logo 正常显示；
- “Quick start / How to invoke” 清楚说明输入、调用词和输出；
- README 不再要求使用者从 GitHub 源码树寻找 ZIP。

### 1.6 使用者如何从 GitHub 安装

使用者直接运行：

```zsh
npx skills add foukusa/stca-agent-skill --skill stca
```

或：

```zsh
git clone https://github.com/foukusa/stca-agent-skill.git
cp -R stca-agent-skill/skills/stca /目标技能目录/stca
```

这两种路线都读取仓库源码，**不需要 ZIP**。

### 1.7 可选：创建 GitHub Release

源码推送完成后，仓库网页进入 **Releases → Draft a new release**：

- Tag：`v0.1.0`
- Title：`STCA Agent Skill v0.1.0`
- Release notes：复制 `CHANGELOG.md` 中 0.1.0 的内容
- Attach binaries：上传本地构建目录中的四份 ZIP、`STCA_logo.png` 和 `SHA256SUMS.txt`

Release 附件用于下载；它们不是 `main` 分支源码文件。

## 2. ChatGPT / Codex：构建并提交插件

### 2.1 普通使用者怎么安装和调用

STCA 插件公开后：

1. 打开 ChatGPT 的 **Plugins** 目录。
2. 搜索 **STCA** 并安装。
3. 新建对话。
4. 输入 `@STCA`，选择 STCA。
5. 附上 CSV，并发出明确请求，例如：

```text
@STCA Screen candidates.csv for high Tg and bottom-5% EC.
Use CandidateKey as an arbitrary identifier column. Keep the original star-containing SMILES in the final results,
use H-cap only for MACCS calculation, and report row-level pass/fail results with failed rule conditions.
```

### 2.2 维护者提交哪个文件

先在源码根目录构建：

```zsh
python3 tools/build_packages.py \
  --output-dir "$HOME/Desktop/STCA-release-0.1.0"
```

上传：

```text
~/Desktop/STCA-release-0.1.0/stca-openai-plugin-0.1.0.zip
```

不要上传：

- GitHub 源码文件夹；
- `stca-github-release-0.1.0.zip`；
- 整个 Mac 发布总包。

### 2.3 Mac 提交步骤

1. Safari 或 Chrome 打开 [OpenAI 插件发布门户](https://platform.openai.com/plugins)。
2. 选择正确的组织和项目，使用已验证的开发者身份。
3. 点击上传插件。
4. Mac 文件选择器按 `⌘⇧G`，输入：

```text
~/Desktop/STCA-release-0.1.0
```

5. 选择 `stca-openai-plugin-0.1.0.zip`。
6. 检查：
   - Display name：STCA
   - Version：0.1.0
   - Skill：`stca`
   - Logo：STCA logo
   - 三个 starter prompts
7. 自动检查失败时，修改源码，换一个新的输出目录重新构建，再上传完整 ZIP。
8. 提交审核；批准后由你点击发布。

### 2.4 ChatGPT 验收请求

发布或私测安装后，至少运行三条：

```text
@STCA Apply the paper low-EC 5% rule to the attached candidates.
Use H-cap only for calculation and return the original star-containing SMILES.
```

```text
@STCA Extract and freeze STCA rules from the attached measured Tg data,
then evaluate the independent holdout.
```

```text
@STCA Export high-Tg and low-EC constraints, propose 20 candidates,
and verify every candidate against each frozen rule.
```

检查它是否真的运行脚本并产生结果文件，而不是只复述算法。

## 3. DeepSeek Harness：从源码安装与调用

### 3.1 安装 Node 与启动 Harness

在终端检查：

```zsh
node --version
```

若尚未安装符合 Harness 要求的 Node，先从 [Node.js 下载页](https://nodejs.org/en/download) 安装对应 Mac 芯片版本。

参考 [DeepSeek Harness 官方仓库](https://github.com/deepseek-ai/deepseek-harness)，在工作目录启动：

```zsh
mkdir -p "$HOME/Documents/STCA-work"
cd "$HOME/Documents/STCA-work"
npx @deepseek-ai/dsh web
```

在 Web UI 中配置 DeepSeek API Key，并选择工作区。

### 3.2 推荐：直接从 GitHub 源码安装

```zsh
cd "$HOME/Downloads"
git clone https://github.com/foukusa/stca-agent-skill.git
mkdir -p "$HOME/.dsh/skills"
rm -rf "$HOME/.dsh/skills/stca"
cp -R stca-agent-skill/skills/stca "$HOME/.dsh/skills/stca"
```

检查：

```zsh
test -f "$HOME/.dsh/skills/stca/SKILL.md" && echo "STCA installed"
```

### 3.3 另一种方式：Release ZIP

维护者在 GitHub Release 提供 `stca-deepseek-harness-0.1.0.zip` 后：

1. Finder 双击 ZIP。
2. 得到顶层 `stca` 文件夹。
3. 终端执行：

```zsh
mkdir -p "$HOME/.dsh/skills"
open "$HOME/.dsh/skills"
```

4. 把 `stca` 文件夹复制进去。

### 3.4 调用方式

在 Harness 输入：

```text
/stca Screen candidates.csv with the paper low-EC 5% rule.
Use H-cap only for MACCS calculation, restore the original repeat-unit SMILES in the final results,
and report every failed condition.
```

提取规则：

```text
/stca Audit measured_td.csv, extract the full rule family on the source data,
freeze the representative rule, and evaluate the holdout.
```

设计候选：

```text
/stca Export constraints for high thermal stability and low EC,
propose 20 repeat units, retain every proposal, and verify every frozen rule.
```

## 4. WorkBuddy：本机导入与开放平台发布

### 4.1 安装 Mac 客户端

1. 从 [WorkBuddy Mac 下载与安装说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Installation-Mac-Guide) 下载适合 Mac 芯片的版本。
2. 打开 `.dmg`。
3. 把 WorkBuddy 拖到“应用程序”。
4. 从“应用程序”打开并登录。

### 4.2 本机导入

先构建平台包：

```zsh
python3 tools/build_packages.py \
  --output-dir "$HOME/Desktop/STCA-release-0.1.0"
```

WorkBuddy 中进入：

```text
专家·技能·连接器 → 技能 → 添加技能 → 上传技能
```

选择：

```text
~/Desktop/STCA-release-0.1.0/stca-workbuddy-0.1.0.zip
```

导入后确认 STCA 出现在“已安装”中。

### 4.3 WorkBuddy 调用方式

创建任务并选择工作目录，然后输入：

```text
使用 STCA skill 筛选工作目录中的 candidates.csv。
目标是高 Tg 和低 EC；分别选择档位。H-cap 只用于计算，
最终结果保留原始带星号 SMILES，再输出各目标结果、失败条件和同候选交集。
```

规则提取：

```text
使用 STCA skill 分析 measured_ec.csv。
先审计数据，在源数据上冻结规则，再评价独立留出集，
保存完整规则家族和指标文件。
```

### 4.4 提交到 WorkBuddy 开放平台

1. 打开 [WorkBuddy 开放平台](https://open.workbuddy.cn/)，完成开发者认证。
2. 创建“技能”资产。
3. 上传 `stca-workbuddy-0.1.0.zip`。
4. 核对：名称、中文／英文显示名、版本、作者、简介、示例和 logo。
5. 预览无误后提交审核。
6. 审核通过后发布。

## 5. 四个平台如何调用 STCA

| 平台 | 调用方式 | 最小示例 |
| --- | --- | --- |
| GitHub / skills.sh 安装后的兼容 agent | 在请求中明确写“Use STCA” | `Use STCA to screen candidates.csv for low EC.` |
| ChatGPT | `@STCA` | `@STCA Apply the paper EC 5% rule.` |
| Codex | 选择或提及 `$stca` | `Use $stca to audit and screen this dataset.` |
| DeepSeek Harness | `/stca` | `/stca Extract rules from measured Tg data.` |
| WorkBuddy | 启用后在任务中写“使用 STCA skill” | `使用 STCA skill 核验这些候选。` |

调用时至少写清：

1. 输入文件；
2. 原始 SMILES 列、可选的任意标识列，以及性能列；
3. 目标性质与方向；
4. tier／strictness；
5. 使用 paper 规则还是从数据提取规则；
6. 输出目录。

## 6. 修改后重新生成平台包

在源码根目录执行：

```zsh
python3 tools/build_packages.py \
  --output-dir "$HOME/Desktop/STCA-release-0.1.0-r2"
```

输出目录必须是新目录。构建脚本会统一生成四个平台 ZIP、logo 和 SHA256 清单。

以下内容修改后必须重新构建：

- `README.md` / `README.zh-CN.md`；
- `SKILL.md`；
- 脚本或参考文件；
- `plugin.json`；
- logo；
- 版本号、许可或作者信息。

重新构建后：

- GitHub 源码变化通过 GitHub Desktop 提交；
- ChatGPT、DeepSeek Release 附件和 WorkBuddy 使用新输出目录中的 ZIP；
- 不要继续上传旧 ZIP。

## 7. 发布前检查清单

### GitHub

- [ ] `README.md` 是英文主文档。
- [ ] `README.zh-CN.md` 是完整中文翻译。
- [ ] README 顶部有语言切换和可点击目录。
- [ ] logo 正常显示。
- [ ] Quick start 明确说明如何调用。
- [ ] 源码树不包含平台 ZIP。

### ChatGPT / Codex

- [ ] 上传的是 `stca-openai-plugin-0.1.0.zip`。
- [ ] `plugin.json` 位于 ZIP 根层。
- [ ] 图标、版本和 starter prompts 正确。
- [ ] 安装后能通过 `@STCA` 调用。

### DeepSeek Harness

- [ ] 最终路径是 `~/.dsh/skills/stca/SKILL.md`。
- [ ] `/stca` 能发现技能。
- [ ] 实际执行 H-cap 与筛选脚本，主结果显示原始带 `*` 的 SMILES。

### WorkBuddy

- [ ] 上传的是 `stca-workbuddy-0.1.0.zip`。
- [ ] 技能能导入并启用。
- [ ] 对话中“使用 STCA skill”能触发实际工作流。
- [ ] 开放平台信息和 logo 正确。

### 科学功能

- [ ] H-cap 只作为计算副本，最终主结果恢复显示原始重复单元 SMILES。
- [ ] paper 与 source_locked 协议分开报告。
- [ ] EC 5% 规则可实际筛选候选。
- [ ] 输出逐候选失败条件。
- [ ] 规则通过不表述为实验性能确认。
