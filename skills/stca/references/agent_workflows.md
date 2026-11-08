# 三条agent执行路径

用户只说开始时展示1归纳、2筛选、3生成。明确请求直接进入。普通用户无需脚本、Python路径或规则ID；以下命令仅供agent内部使用。版本0.1.0。

## 1 默认：自己数据范围内归纳

识别SMILES、数值目标、单位、高低方向、实测/计算含义。复用兼容后台，若没有用户指定holdout/外推协议：

```text
PY SKILL_DIR/scripts/agent_runtime.py run --script inrange_evaluation.py -- --input materials.csv --target TC --target-name Thermal_conductivity --property thermal_conductivity --unit "W/(m K)" --direction high --tiers 0.10 0.20 0.30 --smiles-column SMILES --output-dir out/analysis --library-dir USER_RULES_DIR
```

参数按实际文件填写，ID可省略或用--id-column。未定义百分比时直接用10/20/30，明确百分比时按请求（包括15/25）计算，不为缺省档位再问。读取screening_summary.json/recommendation.md，向用户同时显示每档物理cutoff、比较符、单位，两方法各自入选/未知数、AS及主推理由和结果表。先读取文件单位及是否已log；`--metadata-columns`只传样品加工描述，`--condition-columns`传可比测量条件，Reference/DOI/Journal是书目信息，不能作为加工描述扫描。用户可给任意合法档位，例如0.10 0.15 0.20 0.25 0.30；内置目录只有已供给的10/20/30，不能插值伪造15/25。

默认准备数据、按protected_group做5折×3，STCA与WRAcc在相同训练折标签边界比较；AS差超过0.02才取WRAcc，否则STCA优先。`--nested`按外层训练内部3折选择方法，`--with-rf`仅在用户要求预测参照时启用。

读取run_manifest、inrange结果、两方法各模型与导出约束、全量逐档筛选表和主推记录。预处理后CV、最终全量回筛和可选外推各自注明范围；方法选择不是规则OR或AND。没有有效规则、单一标签类、无法CV和运行失败不能填伪0。

流程会自动导出每方法的精确约束、完整双语prompt，保存并导出用户规则包；检查真实save/export状态后才告知已保存。对原上传表每方法/每档返回全部原行、原字段、星号SMILES、明确布尔判断或unknown、每条未满足的规则条件与入选子表。独立候选另用相同冻结模型screen-candidates，不替换原上传表。

## 1b 明确source/holdout或外推协议

保留用户角色和参数，通过原auto_screen.py执行，不能用全量D7或CV选择跨入该holdout。设置和档位建议只在source/inner中形成，冻结后评价holdout。原自动入口仍支持保护ECFP4/t-SNE角色。

```text
PY SKILL_DIR/scripts/agent_runtime.py run --script auto_screen.py -- --input materials.csv --target TC --unit "W/(m K)" --direction high --tiers 0.10,0.15,0.20 --role-column Role --source-value source --evaluation-value holdout --smiles-column SMILES --output-dir out/heldout
```

该路径自动返回upload_screening的全档长表、summary和每档results/selected；随后逐档export-rules→user_rule_library save/export，并返回主菜单。固定参数或论文精确成员用custom_fit并同样补齐筛选和保存。不要用另一种评价改写明确协议。

## 2 选择并筛选已有规则

```text
PY SKILL_DIR/scripts/task_menu.py --rules --language zh-CN --library-dir USER_RULES_DIR
PY SKILL_DIR/scripts/rule_library.py show RULE_ID
PY SKILL_DIR/scripts/agent_runtime.py run --script rule_library.py -- screen RULE_ID --input candidates.csv --smiles-column SMILES --output-dir out/screening
```

按用户来源、性质、档位与方法选择，允许接受标出的主推。两种方法是备选关系：比较时分别screen，不将同一目标主备自动AND。不同性质的明确联合请求才给选定规则交集。用户明确要求同目标方法交集时才使用--allow-method-intersection。

读取“我的规则”：

```text
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR list
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR show SAVED_ID
PY SKILL_DIR/scripts/agent_runtime.py run --script stca_tools.py -- screen-candidates --model SAVED_MODEL --tier 0.20 --input candidates.csv --smiles-column SMILES --output-dir out/screen_saved
```

模型可为原生STCA或显式frozen literal类型；真实learner字段必须显示。复用不重新训练，不要求原训练数据。

## 3 选规则后生成

用户只选3时先给简洁目录并等待选择。目录包含我的规则、论文、GAS、RadonPy、ADEPT，先列性质和可用档位，选中后才展开主推/备选、阈值与条件。不能自动替用户改性质、档位或方法；指代明确时直接执行，仍有多档/多方法时只补问缺失选择。

```text
PY SKILL_DIR/scripts/rule_library.py prompt RULE_ID --language zh-CN
PY SKILL_DIR/scripts/generation_prompt.py --constraints CONSTRAINTS --count 20 --language zh-CN --output out/prompt.md
```

新模型使用stca_tools export-rules导出精确约束。规则确定后，让用户选择“先查看并调整prompt，再生成”或“直接生成并核验”；已在自然语言中说明方式时直接采用。

用`generation_session.py prepare --constraints CONSTRAINTS --mode preview|direct --count 20 --language zh-CN --output-dir SESSION_DIR`准备会话。preview时展示完整prompt并等待；按要求revise后重新展示，只有用户明确确认后才调用confirm。direct时无需确认。具体接口见[generation.md](generation.md)。

当`generation_allowed=true`时，当前AI助手必须读取最终批准的完整prompt并实际生成SMILES，保存全部提案，连续执行同一冻结规则的精确核验，交付通过表与每条未满足的规则条件。确认或准备脚本本身没有调用LLM，不能据此声称已生成。用户只要prompt时交付完整可复制文本；不用执行生成链路。明确显示STCA或WRAcc，规则匹配不当作物性预测。

## 保存与返回

新默认流程自动保存两方法。其他路径仍可：

```text
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR save --name FRIENDLY_METHOD_NAME --model MODEL --constraints CONSTRAINTS...
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR export SAVED_ID --output out/my_rules.zip
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR import --input my_rules.zip
```

检查成功后交付友好名称和下载包，平台有持久文件能力时自动保存，再显示主菜单。用户可继续选2/3；新会话/跨平台导入包继续。无条件项不能作为有效规则保存，用户数据不写回skill安装目录。
