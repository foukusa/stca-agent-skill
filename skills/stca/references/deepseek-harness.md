# STCA：DeepSeek Harness 使用说明

版本 **0.1.0**。在能够加载本地 skill 的 **DeepSeek Harness** 中安装 STCA 后，用户提供文件和自然语言目标，由 AI 助手管理规则及计算。

## 安装与开始

解压 `stca-deepseek-harness-0.1.0.zip`，保留完整 `stca` 目录。默认用户位置为 `~/.dsh/skills/stca/SKILL.md`，项目位置为 `<项目>/.dsh/skills/stca/SKILL.md`；自定义目录按平台配置使用。Mac 在 Finder 按 **Command＋Shift＋G** 打开已有扫描根目录，再复制完整 `stca` 文件夹。目录不存在时，可在 Harness 中让 AI 助手创建或确认实际扫描位置。

输入 **`/stca`**，选择：

1. 上传自己的文件总结规则。
2. 根据已有规则直接筛选。
3. 根据已有规则直接生成。

只选 2 或 3 时，先展示“我的规则”和内置的作者归档、GAS、RadonPy、ADEPT目录，再选择来源、性质、方向、百分比和方法。每档STCA/WRAcc主推与备选是二选一，不能自动混合。用户已经明确选定某条规则或“刚保存的规则”时直接复用，不重复选择。

## 生成方式

选定规则后，选择“先查看并调整 prompt，确认后生成”或“直接生成并核验”。前者展示完整文本并接受修改，明确确认后调用当前 LLM；后者立即调用当前 LLM。两者均保存全部候选并逐条核验，给出通过项和失败条件。用户已说明方式时直接执行，不要求配置模型 API。

## 简短范例

- **上传归纳：**“1。从这份实测气体渗透率表总结高 CO₂ 规则，单位 Barrer。”
- **现成筛选：**“2。选择 GAS 高 CO₂ 渗透率 Top 10%，筛选这份候选。”
- **按规则生成：**“3。”从目录选好规则后说：“直接生成 10 个候选并核验。”
- **复用：**“使用刚才保存的规则生成 20 个候选。”
- **只要 prompt：**“把选中规则的完整生成 prompt 给我，我要在其他 LLM 中使用。”

归纳后默认交付上传表各档完整筛选结果、入选子表和逐条失败条件，同时保留原始星号结构、字段与数据角色。保存模型、各档约束、双语 prompt 和下载包后返回主菜单。用户不用手工导出或重新上传训练数据。

更多范例见 [usage_examples.md](usage_examples.md)。导出的完整 prompt 可用于其他 LLM；实际结构核验由具备计算能力的 STCA 平台执行。平台计算准备与能力边界见 [platform-runtime.md](platform-runtime.md)。

## 官方说明

- [DeepSeek Harness 本地 skill 格式与扫描目录](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)
- [DeepSeek Harness skill 加载与 `/name` 调用](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md)

当前开源目录提供12任务的Top10/20/30两方法主推与备选。新归纳默认按结构分组5折×3次比较STCA与WRAcc，分别回筛原表、保存模型/完整prompt并返回菜单；15/25等自定义档位可用自己的数据学习，不能冒称已有新版内置规则。
