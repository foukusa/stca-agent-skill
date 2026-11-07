# STCA 0.1.0 发布操作

核对日期：2026-11-07。适用于本次提供的 GitHub、skills.sh、OpenAI 和 Zenodo 发行文件。下列公开仓库地址以拟使用的 `foukusa/stca-agent-skill` 为例；仓库、公共目录条目和新软件 DOI 均需按下列步骤实际创建。

## 1. 每个文件交到哪里

| 交付文件 | 用途 | 具体处理 |
| --- | --- | --- |
| `STCA_publish_kit_0.1.0.zip` | 全套文件备份 | 先解压，在其中取出各平台专用文件 |
| `stca-github-release-0.1.0.zip` | GitHub 仓库内容 | 解压后进入 `stca-agent-skill/`，上传其中的文件和子目录 |
| `stca-openai-plugin-0.1.0.zip` | OpenAI 公共插件提交 | 将这个 ZIP 直接上传到插件提交入口 |
| `STCA_logo.png` | 独立 logo | 用于介绍页、软件记录及图标上传；发行包中对应 `assets/stca-logo.png` |
| `PUBLISH_STEPS.zh-CN.md` | 本操作说明 | 阅读使用；可保留在项目仓库 |

GitHub 源码包的外层 `stca-agent-skill/` 用于解压归档，仓库根页面应直接看见 `README.md`、`LICENSE`、`CITATION.cff`、`skills/`、`assets/`、`examples/`、`tools/` 和 `validation/`。上传一个未解压的 ZIP 会把仓库变成压缩包下载页，不能代替标准 skill 的目录。

OpenAI 专用 ZIP 打开后应直接看到 `plugin.json`、`skills/`、`assets/` 及随附发行文件。保留该结构；全套备份 ZIP 不作为插件提交包。

## 2. 发布前只需核对的项目资料

| 项目 | 本次文件采用的内容 | 你要核对什么 |
| --- | --- | --- |
| 包版本 | `0.1.0` | 首次发行；以后每次内容更新递增版本 |
| 作者 | Weihao Wang | 软件作者与平台显示的发布身份分别核对 |
| GitHub 归属 | 示例使用 `foukusa` | 创建仓库时选择实际拥有发布权的账户或组织 |
| 仓库名 | `stca-agent-skill` | 若改名，统一更新安装命令和后来补入的仓库 URL |
| 许可证 | `LICENSE` 保留上游原条款，并标明新包装的许可范围待发布者确认 | 公开前确定新脚本、文档、logo 和样例的许可，并保留适用的上游条款；随后同步引用及 Zenodo 元数据 |
| OpenAI 身份 | 使用你自己的已验证 Developer identity | 实际显示名若与包内 `developerName` 不同，应在提交前对应更新 |
| 软件 DOI | 尚未取得 | 等 Zenodo 产生真实记录后再补入软件 DOI；不填占位 DOI |

包中不需要编造发布者邮箱、ORCID、隐私政策 URL 或支持网站。若后续填入这些可选信息，应使用你实际拥有并维护的资料。

### 本机验收

本机先准备 CPython 3.12 和 Git。进入解压后的 `stca-agent-skill/`，用随附脚本创建新的锁定环境；安装进度写到终端，最终环境信息保存为 JSON：

```bash
python3.12 skills/stca/scripts/setup_locked_environment.py \
  --env-dir "$HOME/.venvs/stca-0.1.0" > stca-setup.json
```

读取刚生成的实际 Python 和源码路径，再执行样例验收：

```bash
STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"
"$STCA_PY" tools/smoke_test.py \
  --skill-dir skills/stca \
  --source "$STCA_SOURCE" \
  --output-dir "$PWD/stca-publish-smoke-01"
```

安装脚本要求环境目录尚不存在；已有环境可复用其保存的 JSON，或另取新目录安装。此流程完成后不再调用旧 `bootstrap`。本次锁定环境已在 Linux CPython 3.12 上完成干净安装与检查；Mac 采用精确版本依赖，须以上述本机验收确认，尚未声称在 Mac 实测通过。

验收使用 `examples/candidates_10.csv` 的 10 个公开提案，预期 H-cap 后原 `paper` 低 EC 5% 规则通过 9 个；P10 因 K124 不符合要求而未入选。`examples/expected_screening.json` 保存逐条依据。再次验收时换一个新的输出目录，保留上次记录。

这一小型验收验证输入、H-cap、冻结筛选、规则导出和联合筛选。原 172 条 extra 数据中的 61 条结果属于另一个历史复现基准；测量原表没有打包到这些公开样例中。

## 3. GitHub：建立发行主仓库

入口：[新建 GitHub 仓库](https://github.com/new)。

1. 登录 GitHub，选择 **New repository**。
2. **Owner** 选择实际发布账户；**Repository name** 填 `stca-agent-skill`。
3. **Description** 可填：`Agent skill for original STCA polymer screening, rule extraction and rule-guided candidate design.`
4. 确认分发授权后选择 **Public**。本包已带 README 和许可文件，新建页面不必额外生成同名文件。
5. 点击 **Create repository**。[1]
6. 空仓库点击 **uploading an existing file**；已有文件的仓库选择 **Add file > Upload files**。
7. 在 Mac 上解压 `stca-github-release-0.1.0.zip`，打开其中的 `stca-agent-skill/`，把里面的文件和子目录拖入上传区域。若包含 `.gitignore` 等隐藏文件，Finder 可用 `⌘⇧.` 显示它们。
8. 提交说明填写 `Release STCA agent skill 0.1.0`，完成页面的 **Commit changes / Propose changes**。若创建的是分支，按页面提示合并到默认分支。[2]
9. 在仓库根页面核对：能打开 `skills/stca/SKILL.md`；README 正常显示 logo；样例和脚本可浏览。

以 `foukusa` 作为 Owner 时，新创建的仓库应对应 `https://github.com/foukusa/stca-agent-skill`。这是拟使用的地址，完成创建后以浏览器显示的真实地址为准，再补入项目元数据。

### 建立 0.1.0 Release

1. 仓库右侧选择 **Releases > Draft a new release**。
2. **Choose a tag** 输入 `v0.1.0` 并创建该 tag，**Target** 选择包含最终发行文件的默认分支。
3. **Release title** 填 `STCA Agent Skill v0.1.0`，说明使用 `CHANGELOG.md` 的本版内容。
4. 附上 `stca-openai-plugin-0.1.0.zip`、`stca-github-release-0.1.0.zip` 和 `STCA_logo.png`，方便下载。
5. 核对内容后点击 **Publish release**；尚需修改时可以 **Save draft**。[10]

第 6 节推荐首次使用 Zenodo 手动上传。如果改用 GitHub 自动归档，必须先连接并启用 Zenodo 仓库，再发布 Release；已发布的同一版本不重复建立两条归档记录。

## 4. skills.sh：从 GitHub 安装并进入发现目录

仓库公开后，在要使用 STCA 的项目目录打开终端。当前 skills CLI 要求 Node.js 22.20 或更高版本，可先运行 `node --version` 检查。[3]

```bash
npx skills add foukusa/stca-agent-skill --skill stca
```

按交互提示选择要安装到的 agent。若仓库 Owner 或名称改变，替换上面的 `foukusa/stca-agent-skill`。需要跨项目使用时，可在命令后加 `-g`。安装后检查：

```bash
npx skills list
```

skills.sh 从 GitHub 发现和安装 skill，并通过正常安装统计形成榜单；该渠道不要求再上传一次 ZIP。目录显示与排名由其收录机制决定，不把一次安装等同于即时上榜。[4]

在 README 中保留安装命令和真实仓库地址即可。以后发布更新，使用者可执行：

```bash
npx skills update stca
```

Node.js 用于 skills 安装工具，Python／RDKit 用于 STCA 计算，两者承担不同工作。

## 5. OpenAI：提交公共插件

入口：[OpenAI Plugins](https://platform.openai.com/plugins)。本次是只包含 skill 的插件包。

### 提交文件

直接选择 `stca-openai-plugin-0.1.0.zip`。包内根目录的 `plugin.json` 使用 Agent Plugins schema，`skills/stca/` 放工作流，`assets/stca-logo.png` 放图标；展示信息位于 `extensions.com.openai.interface`。相对路径与引用文件必须一起保留。[5]

### 页面操作

1. 选择插件归属的组织和项目；完成个人或企业验证。提交者为组织 Owner，或具有 **Apps Management Write** 权限。
2. 在 Plugins 点击 **Upload new or existing plugin**，选择你的已验证 **Developer identity**。
3. 点击 **Upload plugin**，上传专用 ZIP。
4. 打开 **Metadata & Skills**，核对名称、描述、分类、图标并处理扫描问题。分类使用门户实际提供的值；包内预设 `Developer Tools`，提交时核对。
5. 选择草稿，点击 **Submit for review** 并完成页面所需声明。
6. 获批后打开对应版本，点击 **Publish plugin**。[6]

列表基础文字使用英文。字段上限为：展示名 30 字符、短描述 30 字符、长描述 4000 字符、发布者名 80 字符。提交需主图标 `logo`，Codex 校验还要求 `composerIcon`；本包两项引用同一 logo。图标须为方形，至少 48×48；PNG／JPEG／WebP／SVG 单文件不超过 5 MiB，栅格边长不超过 4096。[6]

本包没有 MCP 服务配置，官网／支持／隐私／条款四个 URL 不是这类纯 skill 元数据的统一必填项；也不套用 MCP 专用的八个审核案例和演示录像要求。[6]

### 运行与版本更新

安装后的实际执行环境必须能够运行包内 Python 流程并准备所需依赖。发布包附有明确的环境说明和验收用例；目录包结构校验通过不代表已完成所有宿主的运行验证。

本包不强制桌面专用。如果后续测试确认必须依赖本地桌面执行，再按官方说明在 `extensions.com.openai` 内设置 `requires_local_executor: true`，并按相应提交要求处理。[7]

个人安装、项目内分发和工作区发布可用于使用及测试；面向所有用户的公共目录发布走以上审核流程。工作区内的 Publish 不等于公共目录上线。[5]

更新时保留同一插件名称和身份，递增版本，上传完整新 ZIP，再完成适用检查。修改技能或图标后，仅更新 GitHub 不会更新 OpenAI 目录中的包。[6]

如需重新压缩：在独立文件夹中解压专用包，修改后进入**直接包含 `plugin.json` 的目录**，选中全部发行文件再压缩。检查新 ZIP 的首层仍直接包含 `plugin.json`、`skills/`、`assets/`。

## 6. Zenodo：首次手动归档并取得软件 DOI

入口：[Zenodo](https://zenodo.org)。本次建议手动创建记录，以便在发布前核对最终许可。

1. 登录后点击顶部 **＋ > New upload**。[13]
2. 在 **Upload files** 上传最终的 `stca-github-release-0.1.0.zip` 和 `stca-openai-plugin-0.1.0.zip`；可同时上传 `STCA_logo.png`。
3. **Resource type** 选 **Software**；**Title** 填 `STCA Agent Skill`；版本填 `0.1.0`；**Creators** 填实际作者；**Publication date** 填首次公开日期。说明可使用 README 中的功能介绍，并放入已创建的 GitHub Release 地址。
4. 新软件发行尚无 DOI 时，回答 **No**。如需先把真实 DOI 写进 README，可点击 **Get a DOI now!** 预留；正式 DOI 在记录发布后注册。不要把原论文或原算法的 DOI 填成这个新包装的 DOI。[13]
5. 在 **Licenses** 中核对最终许可。页面默认的 **CC-BY 4.0** 不能直接代表本包的许可：删除或替换该默认项，按最终确认的 `LICENSE` 选择 **Add custom**，填许可名称，说明适用范围，并可链接实际仓库中的 `LICENSE`。如果最终采用标准许可，可用 **Edit** 搜索其名称；上游适用条款仍需保留。[14]
6. 选择文件公开可见，点击 **Save draft** 检查必填项，再用 **Preview** 核对文件、作者、版本和许可。
7. 核对完成后点击 **Publish** 并确认，打开生成的记录，复制真实的软件 DOI。[13]

取得 DOI 后更新 README 和 `CITATION.cff`。本包没有预填新软件 DOI 或新包装许可证；这些字段须对应本人最终确认的许可与实际 Zenodo 记录。

### 后续可选：GitHub 自动归档

这一选项需要先验证最终元数据及许可在 Zenodo 中的映射。同一版本只选一种归档路径；不要假定自动记录会合并进先前的手动记录。

1. Zenodo 头像／个人菜单进入 **Linked accounts**，在 GitHub 项点击 **Connect** 并完成授权。[8]
2. 个人菜单进入 **GitHub**，点击 **Sync now**，找到实际仓库并打开连接开关。[9]
3. 在 GitHub 核对最终 `CITATION.cff` 的作者、标题、版本和许可字段；若使用非标准许可，先确认 Zenodo 中的实际显示。若另加 `.zenodo.json`，它会优先于 `CITATION.cff`。[12]
4. **完成连接和启用后**再发布一个新 GitHub Release；首次版本的 tag 为 `v0.1.0`，后续发行按实际版本递增。建立 Release 的页面操作见第 3 节。[10]
5. 回到 Zenodo GitHub 页面等待处理，打开新记录，核对 DOI、版本、许可和文件。[11]

原论文 DOI 和原算法归档 DOI 作为研究出处保留。它们与这次 agent skill 软件发行的 DOI 各自指向不同对象。

## 7. 完成后的核对

| 渠道 | 完成标志 |
| --- | --- |
| GitHub | 公开仓库中可直接浏览 `skills/stca/SKILL.md`、代码、样例、logo 和许可 |
| skills.sh 安装 | 从真实仓库执行安装命令成功，目标 agent 中可调用 STCA |
| OpenAI 公共目录 | 审核通过并执行 Publish plugin，得到真实公共条目 |
| Zenodo | 最终发行文件已归档，取得可访问且元数据正确的软件 DOI 记录 |

同一版本的验收应保留 H-cap 处理、冻结模型和全部候选判断。公开的 10 个提案基准为 9 个通过结构规则；这不等同于 9 个候选的物性或实验已经验证。

## 官方操作依据

以下页面于 2026-11-07 核对；平台界面变化时以对应官方页面为准。

1. [GitHub：创建仓库](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
2. [GitHub：上传文件](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository?platform=mac)
3. [skills CLI：安装、Node 版本、更新命令](https://github.com/vercel-labs/skills/blob/main/README.md)
4. [skills.sh：托管、安装及目录收录](https://www.skills.sh/docs/faq)
5. [OpenAI：插件包装与工作区分发](https://developers.openai.com/plugins/build/plugins)
6. [OpenAI：公共目录提交、元数据、图标及更新](https://developers.openai.com/plugins/deploy/submission)
7. [OpenAI：需要桌面执行时的配置](https://developers.openai.com/plugins/deploy/desktop-only)
8. [Zenodo：连接 GitHub 账户](https://help.zenodo.org/docs/profile/linking-accounts/)
9. [Zenodo：启用 GitHub 仓库](https://help.zenodo.org/docs/github/enable-repository/)
10. [GitHub：创建 Release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
11. [Zenodo：归档 GitHub Release](https://help.zenodo.org/docs/github/archive-software/github-upload/)
12. [Zenodo：软件元数据](https://help.zenodo.org/docs/github/describe-software/)
13. [Zenodo：新建上传、预留 DOI、预览及发布](https://help.zenodo.org/docs/deposit/create-new-upload/)
14. [Zenodo：许可证、默认 CC-BY 与自定义许可](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
