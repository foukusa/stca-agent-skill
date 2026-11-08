# STCA：DeepSeek Harness 使用说明

版本 **0.1.0**。安装并启用 STCA 后，在当前 DeepSeek Harness 对话中直接说明目标，由 LLM 读取 skill、管理文件及调用计算工具。

## 安装与调用

在 **插件 → 添加插件** 中填写：

```text
https://github.com/foukusa/stca-agent-skill.git
```

或使用 CLI：`dsh plugin --profile web add github:foukusa/stca-agent-skill`，把 `web` 换成实际 profile。安装并启用后输入 `/stca`。已下载的插件通过 `dsh-plugin-stca-0.1.0.tgz` 完整本地路径安装，不需重打包。npm 发布后可填写包名 `dsh-plugin-stca`。

手动安装 skill 时，解压 `stca-deepseek-harness-0.1.0.zip`，将完整 `stca` 目录放入已配置的 filesystem skill 根目录，例如 `~/.dsh/skills/stca`。GitHub `/tree/main` 是网页地址，不能作为 Add plugin 的 Git 安装源。

## 直接描述任务

- **从上传数据学习：**“从这份 RadonPy 数据总结高密度规则，返回筛选结果并保存。”读取 `smiles`、`density`，单位 g/cm³，标签来自计算。
- **现成筛选：**“使用内置含氟候选示例，按 RadonPy 高密度 Top 30% STCA 规则筛选。”
- **规则生成：**“先给我看高 Tg Top 20% 规则的生成 prompt。”或“用选定规则直接生成 10 个聚合物重复单元并核验。”
- **继续复用：**“使用刚才保存的 Top 20% 推荐规则筛选这份新候选表。”

目标缺失时简短说明可选操作；筛选/生成尚未选规则时才展示来源、性质和可用百分比，已明确选择时直接执行。STCA 与 WRAcc 分别应用，不能自动混合。用户不必经过固定编号菜单，也不要求平台提供“我的规则”页面。

## 保存和生成

学习默认使用 Top/Bottom 10%、20%、30%，允许自定义百分比。交付两方法的逐档规则、实际数值阈值/比较符/单位、原上传表的筛选结果和推荐理由。评分用交叉验证的平均筛选评分：马修斯相关系数、精确率和 F1 分数的平均值；向用户报告时解释名称。

成功保存后显示真实文件名、位置和可下载规则包。用户可以继续筛选或生成，新会话上传规则包载入，不重新要求训练数据。

预览生成时展示完整 prompt，允许调整并等待确认；明确要求直接生成时立即使用当前 LLM。保留全部提案并按相同冻结条件核验，报告实际生成、完成核验和匹配数量。无需为 STCA 再配置一个模型 API。

## 计算环境和状态

由 AI 助手用随包启动器自动查找并检查 Python 3.10+ 和 RDKit，普通 Python、虚拟环境、Conda 均可，Conda 不是必需。查找及隔离环境准备见 [platform-runtime.md](platform-runtime.md)。筛选使用 chem 后台，学习使用 fit 后台。

macOS 签名、依赖导入或执行权限失败时，尝试其他兼容环境。仍无法核验则保留提案并标为待核验，不把未执行解析记成无效 SMILES、零入选或零覆盖。界面激活 skill、LLM 已生成文本、结构已解析和规则已核验是不同步骤，按实际结果报告。

更多请求见 [usage_examples.md](usage_examples.md)。

## 平台说明

- [DeepSeek Harness filesystem skill 格式](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md)
- [skill 加载与调用](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md)
