# 根据冻结精确 AND 规则生成聚合物重复单元

方法声明：标为 WRAcc 的条件来自 WRAcc 学习器，不是 STCA 算法的归纳结论。历史 `STCA|AND|` 签名前缀仅标识精确位条件，不表示学习方法。

请针对以下目标提出 20 个不同的聚合物重复单元候选，直接在当前对话中生成结构；用户无需配置 Python 或外部模型 API。

## 设计目标

1. H-capped isolated-monomer HOMO–LUMO gap; high / Top 10%; 源训练物理边界: >= 12.938749639 eV; 规则来源: current-ad-gap-wracc-high-10. 规则学习方法: WRAcc.

每个百分比表示相应源数据集的目标尾部范围，不是生成候选的通过比例。若给出物理 cutoff，它是冻结的训练标签边界；命中结构规则不等于预测出性质数值或证明实验达标。

## 精确的冻结结构条件

目标 1 — H-capped isolated-monomer HOMO–LUMO gap:

`K13=0 AND K14=0 AND K17=0 AND K18=0 AND K19=0 AND K21=0 AND K22=0 AND K23=0 AND K24=0 AND K25=0 AND K26=0 AND K30=0 AND K32=0 AND K33=0 AND K34=0 AND K35=0 AND K36=0 AND K37=0 AND K38=0 AND K39=0 AND K40=0 AND K43=0 AND K44=0 AND K45=0 AND K47=0 AND K48=0 AND K49=0 AND K50=0 AND K51=0 AND K52=0 AND K53=0 AND K54=0 AND K55=0 AND K56=0 AND K58=0 AND K59=0 AND K60=0 AND K61=0 AND K62=0 AND K63=0 AND K64=0 AND K65=0 AND K67=0 AND K70=0 AND K71=0 AND K73=0 AND K75=0 AND K76=0 AND K77=0 AND K78=0 AND K79=0 AND K81=0 AND K84=0 AND K85=0 AND K88=0 AND K91=0 AND K92=0 AND K95=0 AND K97=0 AND K99=0 AND K100=0 AND K110=0 AND K113=0 AND K117=0 AND K121=0 AND K122=0 AND K125=0 AND K127=0 AND K133=0 AND K136=0 AND K140=0 AND K145=0 AND K158=0 AND K162=0`

规则签名: `STCA|AND|K13=0&K14=0&K17=0&K18=0&K19=0&K21=0&K22=0&K23=0&K24=0&K25=0&K26=0&K30=0&K32=0&K33=0&K34=0&K35=0&K36=0&K37=0&K38=0&K39=0&K40=0&K43=0&K44=0&K45=0&K47=0&K48=0&K49=0&K50=0&K51=0&K52=0&K53=0&K54=0&K55=0&K56=0&K58=0&K59=0&K60=0&K61=0&K62=0&K63=0&K64=0&K65=0&K67=0&K70=0&K71=0&K73=0&K75=0&K76=0&K77=0&K78=0&K79=0&K81=0&K84=0&K85=0&K88=0&K91=0&K92=0&K95=0&K97=0&K99=0&K100=0&K110=0&K113=0&K117=0&K121=0&K122=0&K125=0&K127=0&K133=0&K136=0&K140=0&K145=0&K158=0&K162=0`

每条选定规则中的所有条件必须以 AND 同时满足。多目标时，对同一个重复单元应用全部选定规则并取交集。保留每个位编号及其要求的 0/1 值。不要换用其他百分比的规则、放宽条件，或将多个备选家族成员拼成新规则。要求无法同时满足时，明确报告冲突。

## MACCS 激活语义

- `K13=0`: SMARTS `[#8]~[#7](~[#6])~[#6]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K14=0`: SMARTS `[#16]-[#16]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K17=0`: SMARTS `[#6]#[#6]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K18=0`: SMARTS `[#5,#13,#31,#49,#81]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K19=0`: SMARTS `*1~*~*~*~*~*~*~1`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K21=0`: SMARTS `[#6]=[#6](~[!#6;!#1])~[!#6;!#1]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K22=0`: SMARTS `*1~*~*~1`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K23=0`: SMARTS `[#7]~[#6](~[#8])~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K24=0`: SMARTS `[#7]-[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K25=0`: SMARTS `[#7]~[#6](~[#7])~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K26=0`: SMARTS `[#6]=;@[#6](@*)@*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K30=0`: SMARTS `[#6]~[!#6;!#1](~[#6])(~[#6])~*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K32=0`: SMARTS `[#6]~[#16]~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K33=0`: SMARTS `[#7]~[#16]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K34=0`: SMARTS `[CH2]=*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K35=0`: SMARTS `[Li,Na,K,Rb,Cs,Fr]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K36=0`: SMARTS `[#16R]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K37=0`: SMARTS `[#7]~[#6](~[#8])~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K38=0`: SMARTS `[#7]~[#6](~[#6])~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K39=0`: SMARTS `[#8]~[#16](~[#8])~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K40=0`: SMARTS `[#16]-[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K43=0`: SMARTS `[!#6;!#1;!H0]~*~[!#6;!#1;!H0]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K44=0`: SMARTS `[!#1;!#6;!#7;!#8;!#9;!#14;!#15;!#16;!#17;!#35;!#53]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K45=0`: SMARTS `[#6]=[#6]~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K47=0`: SMARTS `[#16]~*~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K48=0`: SMARTS `[#8]~[!#6;!#1](~[#8])(~[#8])`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K49=0`: SMARTS `[!+0]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K50=0`: SMARTS `[#6]=[#6](~[#6])~[#6]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K51=0`: SMARTS `[#6]~[#16]~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K52=0`: SMARTS `[#7]~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K53=0`: SMARTS `[!#6;!#1;!H0]~*~*~*~[!#6;!#1;!H0]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K54=0`: SMARTS `[!#6;!#1;!H0]~*~*~[!#6;!#1;!H0]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K55=0`: SMARTS `[#8]~[#16]~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K56=0`: SMARTS `[#8]~[#7](~[#8])~[#6]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K58=0`: SMARTS `[!#6;!#1]~[#16]~[!#6;!#1]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K59=0`: SMARTS `[#16]!:*:*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K60=0`: SMARTS `[#16]=[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K61=0`: SMARTS `*~[#16](~*)~*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K62=0`: SMARTS `*@*!@*@*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K63=0`: SMARTS `[#7]=[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K64=0`: SMARTS `*@*!@[#16]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K65=0`: SMARTS `c:n`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K67=0`: SMARTS `[!#6;!#1]~[#16]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K70=0`: SMARTS `[!#6;!#1]~[#7]~[!#6;!#1]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K71=0`: SMARTS `[#7]~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K73=0`: SMARTS `[#16]=*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K75=0`: SMARTS `*!@[#7]@*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K76=0`: SMARTS `[#6]=[#6](~*)~*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K77=0`: SMARTS `[#7]~*~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K78=0`: SMARTS `[#6]=[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K79=0`: SMARTS `[#7]~*~*~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K81=0`: SMARTS `[#16]~*(~*)~*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K84=0`: SMARTS `[NH2]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K85=0`: SMARTS `[#6]~[#7](~[#6])~[#6]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K88=0`: SMARTS `[#16]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K91=0`: SMARTS `[$([!#6;!#1;!H0]~*~*~*~[CH2]~*),$([!#6;!#1;!H0;R]1@[R]@[R]@[R]@[CH2;R]1),$([!#6;!#1;!H0]~[R]1@[R]@[R]@[CH2;R]1),$([!#6;!#1;!H0]~*~[R]1@[R]@[CH2;R]1)]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K92=0`: SMARTS `[#8]~[#6](~[#7])~[#6]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K95=0`: SMARTS `[#7]~*~*~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K97=0`: SMARTS `[#7]~*~*~*~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K99=0`: SMARTS `[#6]=[#6]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K100=0`: SMARTS `*~[CH2]~[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K110=0`: SMARTS `[#7]~[#6]~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K113=0`: SMARTS `[#8]!:*:*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K117=0`: SMARTS `[#7]~*~[#8]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K121=0`: SMARTS `[#7;R]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K122=0`: SMARTS `*~[#7](~*)~*`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K125=0`: 特殊/未定义键，使用完整 MACCS 算法; 要求对应激活条件不成立；计数键不等于零匹配; definition RDKit 2026.09.1.
- `K127=0`: SMARTS `*@*!@[#8]`; count_parameter=1; 位 1 激活条件: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K133=0`: SMARTS `*@*!@[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K136=0`: SMARTS `[#8]=*`; count_parameter=1; 位 1 激活条件: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K140=0`: SMARTS `[#8]`; count_parameter=3; 位 1 激活条件: `unique_substructure_match_count > 3`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K145=0`: SMARTS `*1~*~*~*~*~*~1`; count_parameter=1; 位 1 激活条件: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K158=0`: SMARTS `[#6]-[#7]`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K162=0`: SMARTS `a`; count_parameter=0; 位 1 激活条件: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.

以完整的 RDKit MACCS167 计算为判据。要求位值为 0，表示对应激活条件不成立；对于计数位，这不一定表示匹配子结构完全不存在。保留计数阈值和特殊位逻辑。不要把特殊位改写成猜测的 SMARTS，也不要根据位编号编造官能团名称。

## 化学偏好

无额外化学偏好；在冻结条件内增加结构多样性。

遵守明确的化学排除项和必需基团，用其他偏好增加候选的多样性。硬性偏好与冻结规则冲突时，说明冲突，不要静默放宽。

## 重复单元表示

- 在 `SMILES` 字段返回原始重复单元，恰好保留两个末端 `*` 连接原子。每个 `*` 仅有一个相邻原子，以单键连接。使用合理价态，表示为单一连通的重复单元。
- 最终结构保留两个连接点。H-cap 仅是用于计算 MACCS 的独立副本：按照冻结模型的表示契约，将两个受支持的末端单键星号换成氢。不要用 H-cap 分子代替最终重复单元，也不要从 H-cap 反推连接点。
- 返回不同的提案；没有证据时，不声称数据库新颖性、合成可行性或实测性质数值。

## 输出与核验

返回表格，列名为 `candidate_id`、`SMILES`、`design_note`、`verification_status` 和 `failed_conditions`。设计说明保持简短，并对应上述化学偏好。

存在兼容计算后端时，保留所有原始提案，核验结构和冻结 MACCS 条件，报告实际状态及每条失败条件。不要把缺失指纹补成全零，也不要凭目测声称通过。通过数不足 20 时，报告差额并保留失败提案，不修改规则。

没有计算核验后端时，标记 `verification_status=generation_only`、`failed_conditions=not_evaluated`。
