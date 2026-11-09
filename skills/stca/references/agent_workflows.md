# 三条agent执行路径

用户只说开始时简短介绍归纳、筛选、生成三种用法；不要求用户回复固定编号。明确请求直接进入。普通用户无需脚本、Python路径或规则ID；以下命令仅供agent内部使用。版本0.1.0。

## 1 默认：先按 Morgan 距离留出，再归纳

先绑定文件、全部或指定数据行、结构列、数值目标列、单位、高低方向及实测/计算含义。学习前给出一行实际绑定说明，例如“PI1070.csv：1077行；结构smiles；密度density，g/cm³；高值方向”。明确列名优先；多列、实测/计算或条件有歧义时才补问，不能只凭数值猜目标。

保存原始带 `*` SMILES，仅将计算副本中支持的末端单键连接点 H-cap；输出读取原始列，不反推星号。默认入口：

```text
PY SKILL_DIR/scripts/agent_runtime.py run --script morgan_evaluation.py -- --structure-kind polymer_repeat_unit --input materials.csv --target TC --target-name Thermal_conductivity --property thermal_conductivity --unit "W/(m K)" --direction high --tiers 0.10 0.20 0.30 --smiles-column SMILES --distance-threshold 0.5 --output-dir out/analysis --library-dir USER_RULES_DIR
```

按实际字段填写；ID 可省略或用 `--id-column`，明确材料组可传 `--group-column`。百分比缺省使用10/20/30，用户自定15/25等合法档位照实执行，不替换为缺省值。先核对单位、是否已log；`--metadata-columns` 只传加工描述，`--condition-columns` 传可比测量条件；Reference/DOI/Journal 不作为加工描述扫描。

入口先从原始结构计算 ECFP4（radius=2，2048位），建立 source、holdout 和 buffer。相同原始canonical结构、H-cap副本及明确组保持同侧；每条holdout到source最近邻Tanimoto距离默认至少0.5，buffer不拟合、不外评。性质数值不选择划分。只对source进行每档独立准备、影响诊断、变换、步长与支持量选择。

source内部另做同样的Morgan距离划分，用内部训练规则的验证表现确定推荐；再在外部source训练和冻结最终规则，随后才读取外部holdout标签评价。内部划分不可用时保留明确状态和未获验证的默认偏好，不用外部结果选方法。source内随机保护组交叉验证若仍有输出，只是条件性的内部诊断，不是默认推荐依据或结构外推证据。

WRAcc 默认 `--wracc-max-literals auto --wracc-length-folds 3`，仅在对应训练分区中，从1、2、3、5、10及unlimited上限中选择长度。用户指定最多N条时传N，不限制时传unlimited；保留实际条件数及选择状态。STCA 正负方向各最多10条排序条件、每家族8个候选，不改变作者算法；WRAcc beam宽度30、最少入选支持5，两个支持参数不能等同。向用户解释平均筛选评分为（马修斯相关系数+精确率+F1）/3；source内Morgan验证中WRAcc高出STCA超过0.02才切换，否则STCA优先。

读取 `run_manifest.json`、`split_audit.json`、`split_membership.csv`、`source_inner_selection.json`、`screening_summary.json`、`holdout_metrics.json` 和 `morgan_holdout_evaluation.csv`。核对距离、source/holdout/buffer数量、无保护组重叠、内部推荐及每档source设置。指纹与逐行核验读取 `source_fit/fingerprint_contract.json` 及其逐档记录，执行 `PY SKILL_DIR/scripts/fingerprint_contract.py --run-dir RUN_DIR/source_fit`。缺少凭据不能仅凭汇总MD声称完成。

同时交付每方法/每档的具体物理cutoff、比较符和单位、精确条件、独立外推评分、原始上传表完整筛选及入选子表。source分位数阈值冻结后不从holdout或候选表重算。原表回筛含训练记录，不能称为外推评分。距离划分不可行、无有效规则、单类标签和计算错误不填伪0、不随机回退。各档独立准备，批量加入或重排其他档位不得改变已有档位。

检查每种有效方法的模型、精确约束、完整双语prompt、真实保存回执和便携规则包；确认保存成功才告知已保存。结果保留原上传全部字段、原星号结构、明确判断或unknown及每条未满足条件。独立候选另用相同冻结模型筛选。生成续用时读取当前 `screening_summary.json` 的推荐，不用source内部诊断文件替换。

## 1b 用户明确其他评价协议

用户给出原论文角色、固定source/holdout或明确要求旧投影外围协议时，保留其设置，通过 `auto_screen.py`/`custom_fit.py` 执行；设置和档位建议仅在source/inner形成，冻结后评价holdout。用户明确要求范围内随机保护组评价时，才直接调用 `inrange_evaluation.py` 并注明其条件性范围内协议。不能将随机五折或t-SNE外围留出改称最近邻距离约束。

## 2 选择并筛选已有规则

只需候选结构列与所选规则，不要求候选密度或其他性质标签。明确结构列并保留原始带星号SMILES；H-cap只用于计算副本，返回时读取原始列。

```text
PY SKILL_DIR/scripts/task_menu.py --rules --language zh-CN --library-dir USER_RULES_DIR
PY SKILL_DIR/scripts/rule_library.py show RULE_ID
PY SKILL_DIR/scripts/agent_runtime.py run --script rule_library.py -- screen RULE_ID --input candidates.csv --smiles-column SMILES --output-dir out/screening
```

按用户来源、性质、档位与方法选择，允许接受标出的主推。RadonPy高密度Top 30%示例读取当前目录标记的推荐及实际筛选结果；用户明确选择STCA或WRAcc时保留该选择。生成沿用当前选定的精确规则，不能因静态示例使用STCA就更换用户选择。两种方法是备选关系：比较时分别screen，不将同一目标主备自动AND。不同性质的明确联合请求才给选定规则交集。用户明确要求同目标方法交集时才使用--allow-method-intersection。

读取实际保存的用户规则目录（不是平台页面）：

```text
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR list
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR show SAVED_ID
PY SKILL_DIR/scripts/agent_runtime.py run --script stca_tools.py -- screen-candidates --model SAVED_MODEL --tier 0.20 --input candidates.csv --smiles-column SMILES --output-dir out/screen_saved
```

模型可为原生STCA或显式frozen literal类型；真实learner字段必须显示。复用不重新训练，不要求原训练数据。

## 3 选规则后生成

用户请求生成但尚未选定目标时，先给简洁目录并等待选择。目录包含当前可读的已保存规则、论文、GAS、RadonPy、ADEPT、OpenPoly，先列性质和可用档位，选中后才展开主推/备选、阈值与条件。不能自动替用户改性质、档位或方法；指代明确时直接执行，仍有多档/多方法时只补问缺失选择。

```text
PY SKILL_DIR/scripts/rule_library.py prompt RULE_ID --language zh-CN
PY SKILL_DIR/scripts/generation_prompt.py --structure-kind polymer_repeat_unit --constraints CONSTRAINTS --count 20 --language zh-CN --output out/prompt.md
```

新模型使用stca_tools export-rules导出精确约束。规则确定后，让用户选择“先查看并调整prompt，再生成”或“直接生成并核验”；已在自然语言中说明方式时直接采用。

用`generation_session.py prepare --structure-kind polymer_repeat_unit --constraints CONSTRAINTS --mode preview|direct --count 20 --language zh-CN --output-dir SESSION_DIR`准备会话。preview时展示完整prompt并等待；按要求revise后重新展示，只有用户明确确认后才调用confirm。direct时无需确认。具体接口见[generation.md](generation.md)。

当`generation_allowed=true`时，当前AI助手必须读取最终批准的完整prompt并实际生成SMILES，保存全部提案，连续执行同一冻结规则的精确核验，交付通过表与每条未满足的规则条件。确认或准备脚本本身没有调用LLM，不能据此声称已生成。用户只要prompt时交付完整可复制文本；不用执行生成链路。明确显示STCA或WRAcc，规则匹配不当作物性预测。

## 保存与继续对话

新默认流程自动保存两方法。其他路径仍可：

```text
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR save --name FRIENDLY_METHOD_NAME --model MODEL --constraints CONSTRAINTS...
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR export SAVED_ID --output out/my_rules.zip
PY SKILL_DIR/scripts/user_rule_library.py --library-dir USER_RULES_DIR import --input my_rules.zip
```

检查成功后交付真实文件名、保存路径和下载包。用户可直接说“用刚才的规则筛选”或“按刚才的规则生成”；新会话/跨平台导入包继续，不承诺临时文件自动持久保存。无条件项不能作为有效规则保存，用户数据不写回skill安装目录。

计算状态必须来自实际运行。RDKit 导入、macOS 签名或执行权限失败时不能把未解析提案记作无效 SMILES、零入选或零覆盖；保留错误并将提案标为待核验，自动尝试其他兼容环境。向用户显示验证评分时，把 AS 解释为马修斯相关系数、精确率和 F1 分数的平均筛选评分，不能只给 CV AS 缩写。

逐档准备记录见 `source_fit/run_manifest.json` 的 `per_tier_preparation` 和 `source_fit/preparation_by_tier.json`。每档返回实际变换、步长及扫描支持量；不能将第一档的根目录兼容记录用于解释其他档位。相同档位的学习与筛选不得依赖批量请求中的其他档位。
