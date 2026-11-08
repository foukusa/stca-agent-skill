# 当前规则证据与结果解释

## 当前内置主线

最新来源为用户提供的 `stca_skill_summary_20261108 (1).zip`，SHA256为 `d22066c7bfa5239070dab9b8cf97e54c4215fce7ee77c645e90a83ed31181d39`。12项任务×3档10/20/30提供36组STCA/WRAcc主推备选，共72条精确AND规则。11条作者归档Tg/EC规则保持原条件；66条旧非论文条目以legacy隐藏，保留原ID。

每条当前开源规则的reference_evaluation明确分组5折×3的CV均值/SD，以及全量回筛selected/precision/recall，两种证据不能混为留出混淆矩阵。主推15条STCA、21条WRAcc；这是按AS差>0.02切换的方法选择，不是OR/AND合并。

72条全量规则均有非零支持；GAS/RadonPy的42条规则已在可再分发的7份cleaned数据上逐位独立回算并完全匹配支持数和精确率/召回率。ADEPT未附逐行原始数据，保存提供者精确条件与评价出处，不声称重新运行了全部研究。证据位于 `assets/rule_library/evidence/latest_20261108/`。

## 三种范围

- CV：每折训练阈值，在准备数据范围内的折外评价，条件于已确定的清理/D7和扫描制度。
- 全量回筛：最终全量模型的部署阈值与入选支持，是样本内应用，不冒充独立泛化。
- 可选外推附录：另外的source成员、cutoff和拟合模型；其零入选不能覆盖当前全量规则的支持或CV值。

附录中PI_CP10/20、AD_GAP10、AD_DC10/20/30零入选，而当前72条全量规则均非零。这些数字分别属于不同模型和评价对象，应保留真实范围。全量AD_DC的STCA仅选3/2/2条，主推为WRAcc；不能把备选STCA的稀疏支持改写成整个类别不可筛选。

## 状态与应用

当前 inrange_cv_evaluated 表示存在有出处的条件性CV，不是新材料的物性保证。旧 no_reference_coverage/no_demonstrated_enrichment/reference_inconclusive 仅适用于它们各自的legacy模型，明确选择旧ID时展示相关状态。零覆盖、零TP、没有正例、没有规则和计算错误应分开。

主推WRAcc时必须显示WRAcc方法；用户可选择STCA备选，不冒充它有WRAcc的得分。百分位描述训练标签目标尾部，实际入选比例由规则决定。MACCS特殊键和计数键按完整RDKit生成器核验；不能把K125的?当作普通SMARTS。

论文一致性核验：这些11条是SI-20260822作者快照；其中Tg Top10%代表与正式SI S7.1最优family的描述不同，不能称正式SI代表。逐行档案一致与正式论文全面复现分开，见provenance.md及catalog publication_alignment。
