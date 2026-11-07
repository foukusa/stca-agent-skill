# STCA WorkBuddy 版：安装、使用与市场发布

核对日期：2026-11-07。适配文件为 `stca-workbuddy-0.1.1.zip`；这是 WorkBuddy 原生技能包。它使用同一套 STCA 计算脚本、H-cap 契约和固定作者代码版本，增加 WorkBuddy 展示元数据及安装说明。

## 1. 文件结构与平台要求

ZIP 中保留一个 `stca/` 技能目录；打开该目录即可看到 `SKILL.md`，同级保存 `scripts/`、`references/`、`assets/`，以及运行资源。避免再套一层完整 GitHub 仓库目录。

WorkBuddy 开放平台要求 `SKILL.md` 的 YAML 头部包含八项：`name`、`display_name`、`display_name_en`、`description`、`description_zh`、`description_en`、`version`、`author`。本包使用标识 `stca`、中文名“STCA 聚合物筛选”，并提供中英文说明与三种调用示例。`author` 在正式提交时应与实际发布主体对应。[1]

官方结构说明展示一个技能目录，并明确开放平台解析 ZIP；公开文档未给出 ZIP 的统一大小上限、压缩方法或全部可接受层级的枚举。因此本包采用这一层技能目录结构，提交时仍以解析结果为准，不宣称已经通过 WorkBuddy 在线解析或审核。[1]

## 2. 安装到自己的 WorkBuddy

1. 安装并登录 WorkBuddy 桌面端。
2. 左侧进入“专家·技能·连接器”，选择“技能”。
3. 点击“添加技能 → 上传技能”，选择本次 ZIP。
4. 导入完成后，在“已安装”列表中找到 STCA 并启用。
5. 新建一个任务，选择保存输入和结果的工作文件夹，发送下方验收请求。[2]

可直接使用的首次请求：

> 使用 STCA 技能筛选当前工作文件夹中的候选表。目标是高 Tg、低 EC 和高 TC；每个目标独立选择档位，先生成 objective plan，再逐项执行并给出同候选交集和失败条件。

日常也可分别请求“按已有规则筛选候选”“从实测数据提取并冻结规则”“导出约束、提出候选并运行核验”。提供 CSV 时明确 SMILES 列；拟合或评价时还需性能列、单位和数据角色。

## 3. 执行环境

WorkBuddy 客户端的系统要求为 Windows 10 及以上的 x64，或 macOS 12 及以上；Mac 按芯片选择 ARM64 或 X64 安装包。[3][4] 这是客户端要求，STCA 还需要 CPython 3.12、Git 及锁定的 Python 依赖。首次安装会访问 PyPI 和原作者 GitHub 仓库；后续使用已准备好的环境与固定源码。

先确定实际安装后的技能目录，再从该目录运行 `scripts/setup_locked_environment.py`；Mac 使用 `python3.12`，Windows 可使用已安装的 `py -3.12`。读取脚本返回 JSON 中的 `python` 和 `source`，后续始终复用。输出目录应放在任务工作文件夹，避免写回技能目录。

安装成功后先确认技能可被调用，再按实际任务准备 Python/RDKit 环境。运行结果应写入任务工作文件夹，不能把导入成功等同于已经完成 STCA 计算。[5]

## 4. 发布到 WorkBuddy 技能市场

入口：[WorkBuddy 开放平台](https://open.workbuddy.cn/)。本地上传安装和公开市场发布是两个独立步骤。

1. 点击“立即入驻”，完成主体认证。
2. 在“设置 → 开发者信息”完善公开资料：开发者昵称为 2–20 个字符，简介为 20–120 个字符，至少填写一种联系方式；头像可以使用平台默认头像，自定义上传要求为 512×512 的 JPG/PNG、不超过 5000KB。[6]
3. 在开放平台创建“技能”类型资产，上传本次 ZIP，并核对解析出的名称、简介、版本、作者和使用示例。
4. 根据表单补充资料；技能图标可使用随包 STCA logo，具体图标限制以该表单为准。
5. 提交平台审核；通过后按平台流程发布上线。后台按钮名称可能随版本变化，公开指引确认的是“创建业务 → 完善信息 → 提交审核 → 审核通过后发布”的流程。[7]

**个人入驻准备：**当前官方流程支持中国大陆二代居民身份证，需证件上的中文姓名、本人实名手机号、可收验证码的邮箱和人脸核身；同一身份证只能认证一个个人主体。[8]

**企业／组织入驻准备：**企业准备营业执照和管理员实名资料，可走法人核验、腾讯云或微信平台已认证主体授权。无营业执照的组织使用统一社会信用代码证书及已有腾讯云／微信认证。官方当前不支持海外组织主体。若以个人身份发布，应选择本人对应的个人认证流程。[8]

上线前沿用原发布包的许可定稿要求；保留原作者实现的许可和引用，避免把仅完成本地检查表述为官方认证。

## 官方依据

1. [WorkBuddy 技能结构与必填字段](https://open.workbuddy.cn/docs/skill)
2. [WorkBuddy 技能管理、导入与启用](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)
3. [Windows 安装要求](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Installation-Win-Guide)
4. [Mac 安装要求](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Installation-Mac-Guide)
5. [WorkBuddy 默认权限与工作空间](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Permission-Modes)
6. [开发者公开资料](https://open.workbuddy.cn/docs/developer-profile)
7. [开放平台概述与发布流程](https://open.workbuddy.cn/docs)
8. [个人、企业和组织入驻要求](https://open.workbuddy.cn/docs/onboarding)
