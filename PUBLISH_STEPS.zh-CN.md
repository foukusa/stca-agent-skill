# STCA · Mac 发布与安装指南

**GitHub · ChatGPT · DeepSeek · WorkBuddy · Zenodo**  
软件版本：0.1.1　｜　Mac 指南修订：2026-11-07

这份指南从下载文件开始，按 Mac 的 Finder、应用程序、浏览器和终端操作编写。GitHub 使用 GitHub Desktop 提交完整项目目录；其他平台在需要时选择已经准备好的 ZIP。所有平台共用同一张 STCA logo。

## 0. 先打开总包

下载 `STCA_Mac_Publish_Kit_0.1.1.zip`，在 Finder 的“下载”中双击，得到 **STCA_Mac** 文件夹。先双击里面的 **START_HERE.html**，用 Safari 或 Chrome 阅读。若 Safari 已经自动解压，直接打开得到的文件夹。内部平台 ZIP 先保留压缩状态，安装章节会说明何时需要解压。

本指南默认总包在 `~/Downloads/STCA_Mac`；如果你把它移到桌面，按实际位置操作。`~` 表示当前 Mac 用户文件夹；`⌘` 是 Command，`⇧` 是 Shift。Finder 按 `⌘⇧G` 可输入目录路径；按 `⌘⇧.` 可显示或隐藏点号开头的文件。

| 总包内的位置 | 里面是什么 | 用到的平台 |
| --- | --- | --- |
| `01_GitHub/stca-agent-skill/` | 完整源码目录，含 README、技能、代码、样例、引用、许可和 logo | GitHub 仓库 |
| `01_GitHub/stca-github-release-0.1.1.zip` | 同一源码的归档包 | GitHub Release、Zenodo |
| `02_ChatGPT/stca-openai-plugin-0.1.1.zip` | 根目录有 plugin.json 的完整插件包 | OpenAI 插件发布门户 |
| `03_DeepSeek/stca-deepseek-harness-0.1.1.zip` | 顶层是 stca 文件夹的 Harness 技能包 | DeepSeek Harness |
| `04_WorkBuddy/stca-workbuddy-0.1.1.zip` | 含 WorkBuddy 元数据的技能包 | WorkBuddy 导入与市场提交 |
| `04_WorkBuddy/WORKBUDDY_LISTING.txt` | 可复制的技能上架文案与示例 | WorkBuddy 开放平台 |
| `05_Zenodo/` | 当前四份归档 ZIP、logo、引用与说明材料 | Zenodo 手动上传 |
| `06_Logo/STCA_logo.png` | 独立透明 logo，512 × 512 PNG | 五个平台的品牌展示 |
| `07_Metadata/` | 填写说明、发布文案、验证说明和 SHA256 清单 | 发布核对 |

**只进行上传和分发，不需要先安装 RDKit。** 第 1–5 章说明发布和导入；第 7 章专门说明实际运行 STCA 的 Mac 环境。上架前建议确认所在宿主能发现 STCA，并能对实际输入执行脚本。

### 先填好属于你的发布信息

已提供名称 STCA、作者 Weihao Wang、版本 0.1.1、三种工作流说明与原论文引用。你的 GitHub 仓库地址、联系方式、ORCID、软件 DOI 和开发者认证资料不能预先编造，按实际填写。

当前 `LICENSE` 仍标注为发布者审阅稿，保留了原作者实现的许可原文；新增集成代码、文档和 logo 的适用条款需要由你定稿。具体待定范围已写在 `PUBLISHER_LICENSE_NOTES.md`。这里没有替你选择 MIT、Apache 或 CC BY，也没有假定你缺少已有授权。

建议在 `01_GitHub/stca-agent-skill/` 中统一编辑：

| 文件 | 发布前核对的内容 |
| --- | --- |
| `LICENSE`、`PUBLISHER_LICENSE_NOTES.md` | 写明你确认的许可及组件范围，保留第三方声明；准备说明可改成实际已确认的情况 |
| `CITATION.cff` | 作者、版本、真实仓库 URL；ORCID 有则填写；软件 DOI 尚未取得时留空 |
| `plugin.json` | 对外名称、作者、描述与版本；现有 logo 路径已经设置好 |
| `skills/stca/assets/platforms/workbuddy.json` | WorkBuddy 的作者、显示名称及中英文说明 |
| `README.md`、`LISTING_TEXT.txt`、`ZENODO_METADATA.txt` | 真实发布地址、最终许可和准备对外展示的文字 |

编辑这些文本文件可用现有代码编辑器，或用 Mac“文本编辑”以纯文本方式打开，保留原来的文件名和扩展名。不要保存成 `.rtf`，也不要把 JSON 中的直引号改成弯引号。**修改后按第 8 章重新生成 ZIP，再上传新生成的文件。**

建议发布顺序：先把最终源码提交到 GitHub 并创建 Release，再完成各宿主的导入与公开提交，最后把该版本归档到 Zenodo。平台审核可以并行进行；审核通过前不写成已上架。

## 1. GitHub：在 Mac 上传完整项目

### 1.1 安装 GitHub Desktop

点苹果菜单 →“关于本机”：Apple M 系列选择 Apple silicon，Intel 处理器选择 Intel 版本。打开 [GitHub Desktop 下载页](https://desktop.github.com/download/)，下载对应 Mac 应用，双击下载文件，打开并登录自己的 GitHub 账号。当前 Desktop 要求 macOS 12 或更新版本。登录后确认提交使用的姓名和邮箱。[安装依据](https://docs.github.com/en/desktop/installing-and-authenticating-to-github-desktop/installing-github-desktop)

### 1.2 已经建过仓库：用 Clone

如果你已经在 GitHub 网页建了 `stca-agent-skill`，即使它还是空的，也按这条走：

1. 在网页打开自己的仓库，复制真实地址，例如 `https://github.com/你的账号/stca-agent-skill`。
2. Mac 顶部菜单 **File → Clone Repository… → URL**，粘贴地址。
3. 核对 **Local Path** 最终指向的本地仓库位置，例如 `~/Documents/GitHub/stca-agent-skill`，点击 Clone。
4. 如果仓库已经在 Desktop 的仓库列表里，直接选中现有仓库，使用其本地目录。

这里只需要克隆一次，不要为已存在的仓库再建一个同名远端。[官方克隆步骤](https://docs.github.com/en/desktop/adding-and-cloning-repositories/cloning-and-forking-repositories-from-github-desktop?platform=mac)

### 1.3 还没建仓库：用 New Repository

1. Desktop 菜单 **File → New Repository…**。
2. Name 填 `stca-agent-skill`；Description 可填 `Sliding Threshold Correlation Analysis workflows for polymers`。
3. Local path 选 `~/Documents/GitHub`。这是**父目录**，Desktop 会在里面创建 `stca-agent-skill`。
4. 本包已提供 README、gitignore 和许可文件，所以不再生成 README，Git ignore 与 License 选 None。创建仓库。

本节完成后，本地仓库例如位于 `~/Documents/GitHub/stca-agent-skill`。界面实际路径不同，就使用自己的实际路径。[官方新建仓库说明](https://docs.github.com/en/desktop/overview/creating-your-first-repository-using-github-desktop)

### 1.4 用 Finder 复制目录里的内容

1. 在 Finder 打开总包的 `01_GitHub/stca-agent-skill/`。这一层应直接看到 `README.md`、`assets`、`skills`、`tools` 等。
2. 按 **⌘⇧.**，让 `.gitignore` 也可见。只在这个发布包来源目录内按 **⌘A → ⌘C**。
3. 新开 Finder 窗口，按 **⌘⇧G**，进入上一步创建或克隆的本地仓库目录，然后 **⌘V**。
4. 目标仓库应直接出现 `README.md` 和 `skills`，不要套成 `stca-agent-skill/stca-agent-skill/`。
5. 保留 Desktop 创建的 `.git`。如果仓库已有自己的文件，核对同名文件后合并；不要先全选删除目标仓库。

**这一步复制的是源文件夹里面的内容。** GitHub Desktop 会处理目录结构。网页文件选择器不能选中整个文件夹，也不影响这套流程。

### 1.5 提交并推送

回到 Desktop，确认当前仓库正确，在 Changes 检查文件。填写提交摘要，例如 `Prepare STCA Agent Skill v0.1.1`，点击 **Commit to main**（实际分支名可能不同）。

已有远端仓库：点 **Push origin**。新建本地仓库：点 **Publish repository**，核对账号、仓库名和公开状态；正式公开时取消“Keep this code private”，再发布。后续更新都是提交后推送。若远端已有新提交，先按提示拉取并检查合并结果。[推送说明](https://docs.github.com/en/desktop/making-changes-in-a-branch/pushing-changes-to-github-from-github-desktop)

刷新 GitHub 网页，确认根目录能看到源码，README 顶部能显示 logo。只完成 Commit 表示已保存在本机，完成 Push 或 Publish 才会到达 GitHub。

### 1.6 创建 Release，提供安装 ZIP

浏览器打开仓库 → Releases → 新建版本草稿。标签设为 `v0.1.1`，目标指向包含最终文件的分支；标题 `STCA Agent Skill v0.1.1`。说明可从 `07_Metadata/RELEASE_NOTES.txt` 复制。

附件上传四份平台 ZIP 和 `STCA_logo.png`；也可附本 Mac 指南和校验清单。Mac 文件选择器内按住 **⌘** 多选文件，或从 Finder 拖入。确认无误后发布 Release。若已修改源码，附件必须使用第 8 章重新生成的 ZIP。[官方 Release 操作](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)

**完成标志：** 仓库能浏览源码；Release 能下载四份 ZIP；README 和独立 PNG 都能看到 logo。

## 2. ChatGPT：提交完整插件包

### 2.1 入口与所用文件

用 Mac 浏览器打开 [OpenAI 插件发布门户](https://platform.openai.com/plugins)。选对组织与项目，完成开发者身份验证；组织 Owner 或具备 Apps Management Write 权限的成员可以提交。使用 `02_ChatGPT/stca-openai-plugin-0.1.1.zip`。

这个 ZIP 的根目录已经有 `plugin.json`，同时带 `skills/stca/` 和 `assets/stca-logo.png`。普通聊天附件上传只代表发送了文件；需要走实际插件安装或发布流程，才算安装。[官方包结构](https://developers.openai.com/plugins/build/plugins)

### 2.2 Mac 上传与修正

1. 在门户创建或上传插件，选择已验证的开发者身份，点 **Upload plugin**。
2. Mac 文件窗口左侧点“下载”，进入总包的 `02_ChatGPT`，单击 ZIP，再点“打开”。
3. 上传后核对 **Metadata & Skills**：名称 STCA、版本 0.1.1、技能内容和图标。
4. 包详情区域是只读的。若提示问题，复制问题说明，修改本地源码，然后按第 8 章重新打包、重新上传完整 ZIP。
5. 若缺少图标，先检查包内 logo 引用，也可以使用门户提供的图标选择控件，上传 `06_Logo/STCA_logo.png`。

包中 `logo` 与 `composerIcon` 已引用同一 PNG。当前图片是方形、512 × 512、约 95 KiB，位于官方 48–4096 像素、5 MiB 以内的图标范围。实际门户显示与接受结果仍以提交时为准。[上传、图标与校验依据](https://developers.openai.com/plugins/deploy/submission)

### 2.3 审核、发布和安装验收

把准备好的草稿提交审核，跟踪状态与反馈；获批后再点 **Publish plugin**。上传草稿、送审和公开发布是不同阶段。

发布后，在 Mac 的 ChatGPT 网页或桌面应用打开 Plugins 目录，搜索 STCA，核对作者和 logo，进入详情点加号安装。新建对话，输入 `@` 选择 STCA，发送第 7 章的实际任务请求。[用户安装与调用](https://learn.chatgpt.com/docs/plugins)

实际计算需要宿主具备 Python/RDKit 执行环境，并能取得固定版本的作者源码。先在具备执行能力的 Work/Codex 会话中验收；插件能出现在目录里，本身不等于计算依赖已就绪。

公开前私测可使用官方提供的个人或本地 marketplace 路线；如果账号可用 Plugin Creator，可让它将现有 STCA 插件目录接入个人测试入口，再安装并新建会话测试。受管理工作区的入口与权限由管理员配置。[本地测试说明](https://developers.openai.com/plugins/build/plugins) · [工作区权限](https://learn.chatgpt.com/docs/enterprise/apps-and-connectors)

**完成标志：** 发布状态已公开；目录中可安装；实际任务运行脚本并生成结果文件。

## 3. DeepSeek：Harness 技能安装与分发

本版本使用官方 **DeepSeek Harness** 的文件技能机制。把 ZIP 上传到普通 DeepSeek 聊天，不会自动成为 Harness 的本地技能。

### 3.1 安装 Node 与启动工具

Harness 要求 Node **≥24.9.0**。到 [Node 官网](https://nodejs.org/en/download)选择 **24 LTS 最新修订版**、macOS、对应芯片的 `.pkg` 安装器，双击安装，重新打开终端。Node 24 官方支持矩阵列出 macOS **13.5+**，另要求系统仍在厂商支持期内。[Harness 要求](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/package.json) · [Node 系统支持](https://github.com/nodejs/node/blob/v24.x/BUILDING.md)

按 `⌘空格`，输入“终端”打开，运行：

```zsh
node --version
npm --version
```

### 3.2 安装 STCA 文件夹

在 Finder 打开 `03_DeepSeek`，双击里面的 ZIP，得到 `stca` 文件夹。终端运行：

```zsh
mkdir -p "$HOME/.dsh/skills"
open "$HOME/.dsh/skills"
mkdir -p "$HOME/Documents/STCA-work"
```

将整个 `stca` 文件夹复制进刚打开的 `skills` 窗口。最终必须是 `~/.dsh/skills/stca/SKILL.md`，不是多套一层 `stca/stca/`。Finder 按 `⌘⇧G` 输入这个目录可再次打开。包内 `assets/stca-logo.png` 是 logo。

这是默认全局路径，适合多个工作区复用。自定义了 `DSH_HOME` 时位置会变化。更新旧版时，先把旧版移到技能目录以外备份，再放新文件夹。[官方技能发现规则](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)

### 3.3 配置模型并调用

```zsh
cd "$HOME/Documents/STCA-work"
npx @deepseek-ai/dsh web
```

首次出现下载询问时，确认包名为官方 `@deepseek-ai/dsh`。按终端显示的本地地址打开浏览器，通常为 `http://127.0.0.1:3080`。保持终端运行；退出时按 Control+C。[官方快速开始](https://github.com/deepseek-ai/deepseek-harness/blob/master/README.zh.md)

在“设置 → 模型”填自己的 [DeepSeek API Key](https://platform.deepseek.com/)，选择可用模型；添加并选中工作区 `~/Documents/STCA-work`。输入 `/stca` 调用。API Key 属于个人运行配置，不放入分发包。[模型和工作区](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/index.zh.md) · [显式技能调用](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md)

科学计算环境按第 7 章准备；也可以让 Harness 读取技能中的 `references/platform-runtime.md`，按该章安装后直接运行实际任务。

### 3.4 对外发布

将 DeepSeek ZIP 放到你的 GitHub Release，并在 README 写出上述目录、Node 和 Python 要求。接收者下载后按相同步骤安装。当前采用的是可核实的文件分发路线；没有为这个包确认独立的 DeepSeek 公共技能投稿按钮。

Logo 已在 ZIP、README 与独立素材中提供；没有把某个未核实的 Harness 图标上传控件写成必需步骤。

**完成标志：** Harness 能发现 `/stca`；真实运行实际任务；GitHub Release 中提供可下载的 DeepSeek ZIP。

## 4. WorkBuddy：Mac 导入与市场发布

### 4.1 安装客户端

打开 [WorkBuddy 下载页](https://www.workbuddy.cn/work/)，按 Mac 芯片选 ARM64 或 X64。官方客户端要求 macOS **12+**。双击 `.dmg`，将应用拖入“应用程序”，安装后从那里打开；在浏览器完成登录，再返回客户端。[官方 Mac 安装指南](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Installation-Mac-Guide)

### 4.2 本机导入 ZIP

客户端左侧 **专家·技能·连接器 → 技能 → 添加技能 → 上传技能**。在 Mac 文件窗口选 `04_WorkBuddy/stca-workbuddy-0.1.1.zip`，完成导入。在“已安装”确认技能可用。[官方技能导入](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)

新建任务，以 `~/Documents/STCA-work` 作为工作位置。请它“使用已安装的 STCA 技能”，读取 `references/platform-runtime.md`，准备环境，并直接执行你的候选筛选或规则提取任务。按客户端实际提示授权访问所选工作目录及执行必要命令。本技能不要求你为 WorkBuddy 另填 DeepSeek API Key。

### 4.3 公开上架

用 Safari 或 Chrome 打开 [WorkBuddy 开放平台](https://open.workbuddy.cn/)，完成开发者入驻和主体认证。创建“技能”类型资产，上传 WorkBuddy ZIP，填写说明、示例和平台要求的资料，检查预览后送审；通过后发布。[官方发布流程](https://open.workbuddy.cn/docs) · [入驻材料](https://open.workbuddy.cn/docs/onboarding)

可复制文案在 `04_WorkBuddy/WORKBUDDY_LISTING.txt`。包内已准备 `name`、`display_name`、`display_name_en`、`description`、`description_zh`、`description_en`、`version`、`author` 八个字段。作者与实际发布主体请自行核对。[官方技能结构](https://open.workbuddy.cn/docs/skill)

### 4.4 Logo 与开发者头像

技能提交表单需要图标时，选择 `06_Logo/STCA_logo.png`，按该表单当前显示的规格检查预览。

“设置 → 开发者信息”里的**开发者头像**是另一项。官方自定义头像要求 **512 × 512、JPG/PNG、≤5000KB**，也可保留系统默认头像；昵称 2–20 字符，简介 20–120 字符，至少填写一项对外联系方式。[开发者资料要求](https://open.workbuddy.cn/docs/developer-profile)

本包 logo 已是 512 × 512，可直接用于符合该尺寸要求的头像或图标字段。

**完成标志：** 本机能使用；公开发布状态已上线；市场详情页的署名、logo、描述和安装内容一致。本机导入成功不等于已经上架市场。

## 5. Zenodo：在 Mac 归档并取得 DOI

### 5.1 建立上传草稿

浏览器打开 [Zenodo](https://zenodo.org/)，登录，点击顶部加号 → New upload。首次采用手动上传即可，便于核对每个安装包和 logo。[官方上传指南](https://help.zenodo.org/docs/deposit/create-new-upload/)

点击上传文件，进入总包 `05_Zenodo`。按住 ⌘ 多选四份 ZIP、`STCA_logo.png`、说明和引用文件；也可以从 Finder 拖入文件。该目录的 README 会列明上传清单。若你已重新打包，先用最新文件替换这里的旧 ZIP，或直接从新输出目录选择；不要在同一个版本里混用前后两批文件。

### 5.2 填写元数据

| 页面字段 | 建议填写 |
| --- | --- |
| Resource type | Software |
| Title | STCA Agent Skill |
| Version | 0.1.1；以后与实际发布包版本同步 |
| Creators | 真实软件作者；Weihao Wang 的姓名拼写已提供，机构和 ORCID 按实际补充 |
| Publication date | 这一软件版本首次公开的日期 |
| Description | 复制 ZENODO_METADATA.txt 中的描述，注明三种工作流、H-cap 与运行依赖 |
| Keywords | STCA、polymers、agent skills、interpretable screening、molecular design |
| Related works | 真实 GitHub Release 地址；原论文作为相关研究另填 |
| License | 与最终 LICENSE、第三方声明和 logo 使用范围一致 |

本软件尚未有 DOI 时，对“是否已有 DOI”选择 No，由 Zenodo 为该软件生成 DOI；不要把原论文 DOI 填成软件 DOI。可以先预留，但 DOI 要在发布后才正式注册。[DOI 与元数据说明](https://help.zenodo.org/docs/deposit/create-new-upload/)

Zenodo 默认 CC BY 4.0，需要按实际许可调整。标准许可可搜索选择；非标准条款用自定义许可，写实际名称、范围和许可链接。多组件可以分别声明适用许可。[Zenodo 许可说明](https://help.zenodo.org/docs/deposit/describe-records/licenses/)

### 5.3 检查、发布与回填 DOI

保存草稿，预览文件列表、作者、版本和许可；准备好后点击发布并完成确认。发布后打开真实 DOI 链接，确认能访问记录。

首次最省步骤的顺序是：**先归档最终版本 → 得到正式 DOI → 更新 GitHub 的 README、CITATION.cff 和 Release 描述。** `CITATION.cff` 的软件 DOI 放在顶层，与 `version` 同级；原论文 DOI 保留在 `references` 中。使用 Desktop 提交推送该引用信息更新。此时已发布的归档仍代表此前那个确定快照；下一软件版本重新打包时纳入更新后的引用信息。

如果你希望首次归档内部也已经印上自己的 DOI，可先在该草稿预留 DOI，回填源码，再按第 8 章重新打包并上传，最后发布。预留后继续使用同一草稿，避免删除后丢失预留号。

Logo PNG 是 Zenodo 的可下载附件；它也包含在源码与平台包中。上传 PNG 不会自动变成 Zenodo 站点头像。

### 5.4 更新后续版本

软件或文件有新版本时，在原记录点 New version，上传新版本，保持版本之间的关联；描述、作者等元数据的更正可用编辑记录功能。[官方版本管理](https://help.zenodo.org/docs/deposit/manage-versions/)

**完成标志：** DOI 可解析，记录中可下载相应版本源码、平台包和 logo，许可与作者准确。

## 6. Logo：五个平台分别怎么用

这次沿用同一张 STCA 标志：深蓝与青色 S 图形、金色滑动阈值切口、STCA 字标；原始交付是透明 PNG，没有声称提供可编辑矢量源文件。

| 平台 | 已放好的位置 | 需要你的操作 |
| --- | --- | --- |
| GitHub | `assets/stca-logo.png`，README 已引用 | 提交目录后刷新 README；Release 可另附 PNG |
| ChatGPT | manifest 的 logo、composerIcon 已引用 PNG | 上传完整插件；若门户提示补图标，选择独立 PNG |
| DeepSeek | `stca/assets/stca-logo.png` | 随技能包和下载页分发 |
| WorkBuddy | 技能 assets 和独立 PNG | 技能表单按显示规格上传；512 头像另做副本 |
| Zenodo | 独立 PNG 及每份归档内部 | 上传 PNG 作为附件 |

### 在 Mac 制作 512 像素副本

1. 用“预览”打开 `06_Logo/STCA_logo.png`。
2. 菜单“文件 → 复制”，在副本上操作。
3. “工具 → 调整大小”，单位选像素，保留按比例缩放，勾选重新采样，宽高设为 512。
4. “文件 → 导出”，选 PNG，另存为 `STCA_logo_512.png`；出现 Alpha 选项时保留透明度。
5. Finder 选中副本按 `⌘I`，查看文件信息后上传。

[Apple 调整尺寸说明](https://support.apple.com/en-gb/guide/preview/prvw2015/11.0/mac/27) · [Apple 导出说明](https://support.apple.com/guide/preview/export-pdfs-and-images-prvw0e8da223/mac)

## 7. 实际运行 STCA：Mac 环境与验收

这一章用于运行科学计算。仅上传现成发布包可以跳过；提交公开市场前建议在对应宿主完成验收。

### 7.1 准备 CPython 3.12 与 Git

已安装并正常使用 Homebrew 时：

```zsh
brew install python@3.12 git
python3.12 --version
git --version
```

首次安装按 [Homebrew 官网](https://docs.brew.sh/Installation)操作，并执行安装结束给出的 Next steps。当前官方支持配置为 Apple Silicon、macOS 15+；Intel 属于较低支持级别，不把“适用于 Mac”写成对所有老系统的保证。

Intel 或较旧 Mac 可选择 [MacPorts 官方安装路径](https://www.macports.org/install.php)：先执行下列命令完成 Apple 命令行开发工具安装，然后下载与系统版本匹配的 MacPorts `.pkg`，双击安装，重开终端。

```zsh
xcode-select --install
```

```zsh
sudo port install python312 git
python3.12 --version
git --version
```

`sudo` 需要 Mac 登录密码，输入时终端不显示字符。选择一个适合自己的安装渠道即可。[MacPorts Python 3.12](https://ports.macports.org/port/python312/) · [MacPorts Git](https://ports.macports.org/port/git/)

Python 输出应为 **3.12.x**。当前 Python 3.12 的新安全版本只提供源码，3.12.10 是最后有官方二进制安装器的版本；因此不要把“官网最新 Python 安装器”当作本项目 3.12 环境。[Python 官方说明](https://www.python.org/downloads/release/python-31216/)

### 7.2 从真实技能目录建立运行环境

以下命令以已安装的 DeepSeek 位置为例。GitHub 源码用户可把首行改为本地仓库下 `skills/stca` 的实际绝对路径。WorkBuddy 用户可以解压其 ZIP，选择含 `SKILL.md` 的 `stca` 文件夹；也可以让宿主定位自己的安装目录。

```zsh
STCA_SKILL_DIR="$HOME/.dsh/skills/stca"
STCA_ENV_DIR="$HOME/.venvs/stca-0.1.1"
export PYTHONUTF8=1
python3.12 "$STCA_SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR"
```

环境目录必须尚不存在。安装会获取固定版本的 STCA 代码和 Python 依赖，需要访问 PyPI 与 GitHub。成功后读取实际解释器和源码路径：

```zsh
STCA_PY="$(python3.12 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["python"])' "$STCA_ENV_DIR/stca-environment.json")"
export STCA_SOURCE="$(python3.12 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["source"])' "$STCA_ENV_DIR/stca-environment.json")"
"$STCA_PY" "$STCA_SKILL_DIR/scripts/stca_runtime.py" doctor
```

`doctor` 成功后即可处理用户数据；不需要先运行固定的演示筛选。已经建好的环境可复用，不重复创建。

### 7.3 在宿主中直接执行实际任务

可发送：

> 请使用 STCA 读取当前候选表。目标是高 Tg、低 EC 和高 TC；每个目标独立选择档位，生成 objective plan，再逐项筛选并给出同候选交集、失败条件和结果文件。缺少运行环境时请先按平台说明准备。

DeepSeek 在前面加 `/stca`；WorkBuddy 写“使用已安装的 STCA”；ChatGPT 用 `@` 选中相应插件。

用户只给一个目标时，直接执行该性能的规则；给多个目标时，分别确定性质、方向和档位，再作用于同一候选。Tm、Td、TC 使用 Tg-derived thermal transfer；ε-AC 使用相应方向的 EC-derived electrical transfer。

## 8. 修改之后，在 Mac 重新打包

提供的 ZIP 对应总包里的当前源码。你修改许可、作者、仓库地址、引用信息或代码后，应重新生成安装包。根目录工具 `tools/build_packages.py` 会统一生成 GitHub、ChatGPT、DeepSeek 和 WorkBuddy 四份 ZIP，并同步重复的出版元数据；计算代码保持从同一源码取用。

这一步只使用 Python 标准库，不需要 RDKit。使用 Python 3.9 或更新版本；科学计算环境仍按第 7 章使用 3.12。若没有 `python3`，可用已安装的 `python3.12` 替换命令名。

1. 按 `⌘空格` 打开终端。
2. 输入 `cd `，注意后面有一个空格；把 **实际编辑后的本地仓库文件夹**从 Finder 拖入终端，再回车。这样路径含空格也能处理。
3. 执行以下命令；输出目录不能已存在。再次打包时改用 `STCA-release-002` 等新名称。

```zsh
python3 tools/build_packages.py \
  --output-dir "$HOME/Desktop/STCA-release-001"
open "$HOME/Desktop/STCA-release-001"
```

输出目录包含四个 ZIP、独立 logo 和 SHA256 清单。用这些新文件上传对应平台；它们取代总包中的旧 ZIP。把本地仓库中的同步元数据更改也通过 Desktop 提交推送。新正式版本需要相应调整 `plugin.json`、`CITATION.cff`、变更说明和上架文案中的版本；工具会同步两个平台元数据中的版本字段，但不会替你改写发布说明的正文。

可在输出目录验证文件传输是否完整：

```zsh
cd "$HOME/Desktop/STCA-release-001"
shasum -a 256 -c SHA256SUMS.txt
```

不要用 Finder 随意把整个总包再压缩成 ChatGPT 或 WorkBuddy 的上传包；这些平台要求的 ZIP 内部根层不同，现有工具会分别处理。

## 9. 常见卡点与下一步

| 看到的情况 | 处理方法 |
| --- | --- |
| GitHub 网页窗口选不了文件夹 | 使用第 1 章 Desktop 流程；源码进仓库，ZIP 附件进 Release |
| GitHub 网页没有刚改的文件 | 确认不是只 Commit；还需 Push，且分支和仓库正确 |
| README 出现图片占位或无法加载 | 核对 assets/stca-logo.png 已提交，README 路径大小写一致 |
| 平台提示缺少 SKILL.md 或 manifest | 核对选择的是该平台 ZIP，未多套一层目录；修改后用打包工具重建 |
| Python 安装的是 3.13/3.14/3.15 | 打包可用；科学运行另准备 CPython 3.12 |
| DeepSeek 找不到 /stca | 核对默认目录下 stca/SKILL.md，检查 DSH_HOME 和是否加载了新技能 |
| WorkBuddy 已导入，但市场搜索不到 | 本地导入与公开审核是不同流程，继续开放平台上架步骤 |
| 聊天模型说筛选完成，但没有结果文件和失败条件 | 要求真实执行脚本，并检查工作目录中的输出 CSV/JSON |
| Zenodo 默认为 CC BY 4.0 | 按实际软件与品牌条款改成适用许可 |
| 本地许可改了，平台 ZIP 仍旧 | 按第 8 章重新构建，再上传新输出目录中的文件 |

本指南依据各章链接的官方文档编写，官方文档核查日期为 2026-11-07。菜单翻译可能因客户端语言不同略有变化；已核实的入口和文件对应关系以各章为准。
