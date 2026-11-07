# STCA DeepSeek Harness 版：安装、使用与分发

核对日期：2026-11-07。本版本面向 DeepSeek 官方的 **DeepSeek Harness（dsh）**。它支持从本地目录发现 `SKILL.md`，再由 agent 执行配套脚本；本包沿用 STCA 原作者实现、H-cap 和冻结规则。普通 DeepSeek 聊天页面的文件上传不属于这里的技能安装步骤。

## 1. 安装前准备

- 当前官方 CLI 源码要求 **Node.js ≥24.9.0**；另准备 Git 和 CPython 3.12。
- 在 [DeepSeek 开放平台](https://platform.deepseek.com/) 准备自己的 API Key，稍后填写到 Harness 的模型设置。
- STCA 首次计算需要下载固定版本的作者代码和 Python 依赖。使用 skill 内的 `scripts/setup_locked_environment.py`；后续计算使用其输出的实际解释器和源码路径。

Harness 当前处于开发者预览阶段。安装时记录实际版本；本说明依据下列官方文档及源码，不把目录格式符合要求等同于所有客户端版本均已实测。

## 2. ZIP 解压后放在哪里

DeepSeek 专用 ZIP 的最外层为 **`stca/`**，其中直接包含 `SKILL.md`、`scripts/`、`references/`、`assets/` 等文件。安装时复制完整 `stca` 文件夹，保留这些相对路径。

| 安装范围 | 正确的最终入口 |
| --- | --- |
| 用户全局，macOS／Linux 默认路径 | `~/.dsh/skills/stca/SKILL.md` |
| 用户全局，Windows 默认路径 | `%USERPROFILE%\.dsh\skills\stca\SKILL.md` |
| 当前项目 | `<项目根目录>/.dsh/skills/stca/SKILL.md` |

用户目录如设置了 `DSH_HOME`，则使用该目录下的 `skills/stca/`。项目根是最近的、包含 `.git` 的祖先目录；没有 Git 根时采用会话工作目录。全局安装与项目安装任选一种。已有同名版本时先保留旧版本，再整体替换。

关键层级是 `skills/stca/SKILL.md`，避免多出一层 `stca/stca/`。Harness 读取该目录下的技能入口；发布 ZIP 需先解压。frontmatter 的 `name: stca` 与 `description` 已由本技能提供。

## 3. 启动与调用

在准备处理候选文件的项目目录打开终端：

```bash
node --version
npx @deepseek-ai/dsh web
```

官方命令默认启动本地 Web UI，地址为 `http://127.0.0.1:3080`；以终端实际输出为准。

1. 在界面打开 **设置 → 模型**，在 DeepSeek 卡片填写 API Key 并保存。
2. 选择界面中当前可用的 DeepSeek 模型。保留默认官方端点即可。
3. 点击 **选择工作区**，添加并选中存放输入文件的项目目录。首次打开页面尚未选择工作区时，输入框不可用。
4. 新建会话，输入 `/stca` 加具体任务。这个前缀是 Harness 官方支持的显式技能调用。

首次可直接发送：

```text
/stca 筛选当前工作区的聚合物候选表。目标是高 Tg、低 EC 和高 TC；
请为每个目标分别选择档位，先生成 objective plan，再逐项核验同一批候选，
输出单项结果、失败条件和最终交集。
```

也可以分别请求：按已有规则筛选候选；从实测数据提取并冻结规则、评价独立留出集；导出规则供候选设计，再逐条计算验证。

## 4. 如何公开分发

将 DeepSeek 专用 ZIP 附在 STCA 的 GitHub Release，并在 README 中注明上述安装路径、启动命令和 `/stca` 示例。使用者下载后复制技能目录即可；这条路径交付可安装的本地 skill。

版本更新时同步更新发行说明和 ZIP，使用者整体替换已安装的 `stca` 目录。新封装的最终许可、作者信息及原实现的适用条款与主发行包一致。

## 5. 使用范围

本包提供完整的 skill 入口、执行脚本、目标规划和平台说明。安装后应先确认 Harness 能发现 `/stca`，再在自己的工作区处理实际数据。平台安装成功与材料筛选结果是两件事；实际任务以脚本输出为准。

## 官方依据

1. [DeepSeek Harness：官方项目与启动命令](https://github.com/deepseek-ai/deepseek-harness/blob/master/README.zh.md)
2. [官方 CLI package.json：Node 版本要求](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/package.json)
3. [本地技能格式、扫描目录和优先级](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)
4. [技能加载与 `/name` 显式调用](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md)
5. [Web UI：模型设置、工作区和运行任务](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/index.zh.md)
6. [模型提供方配置](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.zh.md)
