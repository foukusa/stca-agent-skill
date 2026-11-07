# STCA 来源与版本依据

## 锁定实现

- 官方作者仓库：[foukusa/polymer-stca](https://github.com/foukusa/polymer-stca)。
- 本次读取提交：`5951b0ef23d63edc8f7e803aaaffa5e4168288f6`。
- 包名 `polymer-stca`，导入名 `stca`，版本 `1.0`；要求 Python >=3.10。
- 基础依赖：NumPy、pandas、SciPy；SMILES 功能另需 RDKit。`profiles` 成功不代表 SMILES 功能已可执行。
- 上游 README 在本次读取时仍写明 PyPI 发布待完成；从锁定源码安装，不假定 `pip install polymer-stca` 已可用。

优先保持此提交与原始 LICENSE、NOTICE，不将上游算法复制成另一份未经核对的实现。未来更新提交后重新核对接口、预置规则及本 skill 的适配层，再修改版本依据。

## 精确源码链接

| 依据 | 固定版本链接 |
|---|---|
| 安装、用例与范围 | [README.md](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/README.md) |
| 计算方法 | [docs/ALGORITHM.md](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/docs/ALGORITHM.md) |
| 协议与任务预设 | [docs/PROTOCOL_USAGE.md](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/docs/PROTOCOL_USAGE.md) |
| 阈值扫描及名义筛选 | [src/stca/scan.py](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/src/stca/scan.py) |
| 前缀、训练与家族选优 | [src/stca/training.py](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/src/stca/training.py) |
| 冻结模型与评价 | [src/stca/model.py](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/src/stca/model.py) |
| 真实数据重建记录及限制 | [docs/VERIFIED_RESULTS.md](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/docs/VERIFIED_RESULTS.md) |
| 数据/模型的出处说明 | [docs/SOURCES.md](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/docs/SOURCES.md) |
| 上游许可 | [LICENSE](https://github.com/foukusa/polymer-stca/blob/5951b0ef23d63edc8f7e803aaaffa5e4168288f6/LICENSE) |

## 论文与复现平台

论文：[Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design](https://www.nature.com/articles/s41524-026-02345-x)，Weihao Wang、Haoou Ruan、Keith T. Butler、Akiko Kumada、Masahiro Sato，npj Computational Materials，DOI [10.1038/s41524-026-02345-x](https://doi.org/10.1038/s41524-026-02345-x)。本次从出版社检索条目核实题名、作者、DOI 及在线日期 2026-09-28；全文入口遇到出版社身份重定向，未将论文全文或 SI 当作本次已完整读取来源。具体代码约定以上述锁定源码为准。

Code Ocean：[10.24433/CO.1601774.v1](https://doi.org/10.24433/CO.1601774.v1)。此链接已在官方仓库 README、包元数据与 SOURCES 中核实，是维护者给出的研究 capsule 地址；本次没有成功读取 capsule 内容或独立运行它。不要把该 DOI 写成论文 DOI，也不要声称已在线复现 capsule。

## 上游既有证据与本次验证的区别

上游 `VERIFIED_RESULTS.md` 记载 2026-09-21 使用五个作者提供结果包，对 7,291 条 Tg、863 条 EC 记录重建模型，匹配 11 条 paper 代表规则及 1,251 条家族/范围指标。该记录还明确披露：

- EC 的原始 PID 分割文件缺失；以行序重建分割，再用家族/范围结果核对，不能称为恢复了原始成员表。
- Tg 部分预存相关系数与新 value 网格计算存在小差异；所用排名与规则结果匹配，不代表全部系数逐位一致。
- `paper` 的外部范围标签参与核心代表规则选优，因此历史核心匹配不是独立测试精度。
- 全部重采样、其他性质迁移和所有 SI 任务并未重新运行。

以上最初来自上游记录。2026-11-07 的 skill 审计另行取得同一五个作者结果包，实际重跑并匹配 1,251 条历史指标、11 条 paper 和 11 条 source_locked 代表规则；两个核心档案 SHA-256 与上游记录一致。另做了预先固定 seed=20261107 的 canonical 结构分组留出与新拟合评价，见 [validation.md](validation.md)。这仍不是独立新采集实验、全部 SI 或 Code Ocean capsule 的复现。

作者明确原流程先将连接点 H-cap，再计算 MACCS。本次取得的 Tg/EC 档案已无 `*`；另追回 EC 原始指纹及 normal/outliers 表，确认 863×167=144,121 位全同，原始 691/172 成员与顺序均匹配。原 paper 低 EC 5% 规则在 source/extra/all 选中 328/61/389 条，不能用另一个 source_locked 代表在 extra 的 0 条代替原复现。

已检查的公开核心、作者 electrical_workflow_core_v12.py 和其调用脚本处理的是预计算指纹或传入 SMILES，未含更早 H-cap 转换函数。新增适配器按作者明确说明实现末端单键连接点换氢；不声称追回了那一历史函数。保留原始/处理列与哈希。公开源码不包含原始测量表或五个研究结果包，skill 仅记录汇总证据，不再分发私人逐材料数据。后续调用必须说明自身实际运行内容，不能把这里保存的历史验证说成每次重新完成。

## 归属与许可

上游版权声明为 `Copyright (c) 2025, The University of Tokyo, University College London`，使用 `LicenseRef-STCA-Academic-NonCommercial`。许可允许非商业学术研究、教学和结果复现中的使用与修改；商业使用及再分发（包括修改版）要求版权所有者事先书面许可；副本须保留版权及许可文字。

本 skill 的适配器调用原作者实现，并保留作者、论文、代码与协议来源；不要把封装工作表述为另行发明 STCA，也不要把其他独立方法的结果冒充本实现的内置功能。
