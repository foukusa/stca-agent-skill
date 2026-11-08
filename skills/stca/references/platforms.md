# DeepSeek Harness 与 WorkBuddy

两个平台共用同一套 STCA skill、内置规则库、双语生成 prompt 与计算后端。用户安装后通过自然语言选择三种任务：应用现成规则、从上传数据归纳规则、按规则生成候选。

- DeepSeek Harness 的安装与调用见 [deepseek-harness.md](deepseek-harness.md)。
- WorkBuddy 的导入与启用见 [workbuddy.md](workbuddy.md)。
- 后端准备由平台 agent 执行，内部流程见 [platform-runtime.md](platform-runtime.md)。

浏览规则和使用生成 prompt 不需要科学计算依赖。结构筛选与重新学习需要平台具备代码执行能力；平台按 agent_runtime.py 的结果复用或准备后端，并将真实结果交付用户。
