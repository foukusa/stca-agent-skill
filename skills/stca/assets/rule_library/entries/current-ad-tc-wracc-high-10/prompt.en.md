# Generate polymer repeat units with frozen exact AND rules

Method attribution: conditions labelled WRAcc were learned by WRAcc and are not STCA training conclusions. The historical `STCA|AND|` signature prefix identifies exact conditions, not the learner.

Propose 20 distinct polymer repeat-unit candidates for the goals below. Generate the structures in this conversation; the user does not need to configure Python or an external model API.

## Design goals

1. Thermal conductivity; high / Top 10%; source-training physical boundary: >= 0.342 W/(m K); rule source: current-ad-tc-wracc-high-10. Rule learner: WRAcc.

Each percentage describes the desired tail of its source dataset, not the percentage of generated candidates that will pass. A physical cutoff, when supplied, is the frozen training-label boundary; a rule match does not predict a property value or establish experimental success.

## Exact frozen structural constraints

Objective 1 — Thermal conductivity:

`K11=0 AND K13=0 AND K14=0 AND K15=0 AND K19=0 AND K21=0 AND K23=0 AND K24=0 AND K25=0 AND K26=0 AND K27=0 AND K28=0 AND K30=0 AND K31=0 AND K32=0 AND K33=0 AND K37=0 AND K39=0 AND K40=0 AND K41=0 AND K42=0 AND K43=0 AND K45=0 AND K46=0 AND K48=0 AND K49=0 AND K50=0 AND K51=0 AND K54=0 AND K55=0 AND K56=0 AND K57=0 AND K58=0 AND K60=0 AND K61=0 AND K63=0 AND K64=0 AND K66=0 AND K67=0 AND K68=0 AND K70=0 AND K71=0 AND K73=0 AND K76=0 AND K87=0 AND K89=0 AND K102=0 AND K103=0 AND K106=0 AND K107=0 AND K110=0 AND K112=0 AND K123=0 AND K130=0 AND K134=0 AND K136=0 AND K146=0 AND K162=1`

Rule signature: `STCA|AND|K11=0&K13=0&K14=0&K15=0&K19=0&K21=0&K23=0&K24=0&K25=0&K26=0&K27=0&K28=0&K30=0&K31=0&K32=0&K33=0&K37=0&K39=0&K40=0&K41=0&K42=0&K43=0&K45=0&K46=0&K48=0&K49=0&K50=0&K51=0&K54=0&K55=0&K56=0&K57=0&K58=0&K60=0&K61=0&K63=0&K64=0&K66=0&K67=0&K68=0&K70=0&K71=0&K73=0&K76=0&K87=0&K89=0&K102=0&K103=0&K106=0&K107=0&K110=0&K112=0&K123=0&K130=0&K134=0&K136=0&K146=0&K162=1`

Satisfy every literal within each selected rule using AND. For multiple goals, apply all selected rules to the same repeat unit and require their intersection. Preserve the key numbers and required 0/1 values. Do not substitute a rule from another percentage, weaken a condition, or combine alternative family members into a new rule. Report a conflict if the requirements cannot be satisfied together.

## MACCS activation semantics

- `K11=0`: SMARTS `*1~*~*~*~1`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K13=0`: SMARTS `[#8]~[#7](~[#6])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K14=0`: SMARTS `[#16]-[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K15=0`: SMARTS `[#8]~[#6](~[#8])~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K19=0`: SMARTS `*1~*~*~*~*~*~*~1`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K21=0`: SMARTS `[#6]=[#6](~[!#6;!#1])~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K23=0`: SMARTS `[#7]~[#6](~[#8])~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K24=0`: SMARTS `[#7]-[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K25=0`: SMARTS `[#7]~[#6](~[#7])~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K26=0`: SMARTS `[#6]=;@[#6](@*)@*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K27=0`: SMARTS `[I]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K28=0`: SMARTS `[!#6;!#1]~[CH2]~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K30=0`: SMARTS `[#6]~[!#6;!#1](~[#6])(~[#6])~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K31=0`: SMARTS `[!#6;!#1]~[F,Cl,Br,I]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K32=0`: SMARTS `[#6]~[#16]~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K33=0`: SMARTS `[#7]~[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K37=0`: SMARTS `[#7]~[#6](~[#8])~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K39=0`: SMARTS `[#8]~[#16](~[#8])~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K40=0`: SMARTS `[#16]-[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K41=0`: SMARTS `[#6]#[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K42=0`: SMARTS `F`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K43=0`: SMARTS `[!#6;!#1;!H0]~*~[!#6;!#1;!H0]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K45=0`: SMARTS `[#6]=[#6]~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K46=0`: SMARTS `Br`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K48=0`: SMARTS `[#8]~[!#6;!#1](~[#8])(~[#8])`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K49=0`: SMARTS `[!+0]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K50=0`: SMARTS `[#6]=[#6](~[#6])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K51=0`: SMARTS `[#6]~[#16]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K54=0`: SMARTS `[!#6;!#1;!H0]~*~*~[!#6;!#1;!H0]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K55=0`: SMARTS `[#8]~[#16]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K56=0`: SMARTS `[#8]~[#7](~[#8])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K57=0`: SMARTS `[#8R]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K58=0`: SMARTS `[!#6;!#1]~[#16]~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K60=0`: SMARTS `[#16]=[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K61=0`: SMARTS `*~[#16](~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K63=0`: SMARTS `[#7]=[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K64=0`: SMARTS `*@*!@[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K66=0`: SMARTS `[#6]~[#6](~[#6])(~[#6])~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K67=0`: SMARTS `[!#6;!#1]~[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K68=0`: SMARTS `[!#6;!#1;!H0]~[!#6;!#1;!H0]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K70=0`: SMARTS `[!#6;!#1]~[#7]~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K71=0`: SMARTS `[#7]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K73=0`: SMARTS `[#16]=*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K76=0`: SMARTS `[#6]=[#6](~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K87=0`: SMARTS `[F,Cl,Br,I]!@*@*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K89=0`: SMARTS `[#8]~*~*~*~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K102=0`: SMARTS `[!#6;!#1]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K103=0`: SMARTS `Cl`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K106=0`: SMARTS `[!#6;!#1]~*(~[!#6;!#1])~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K107=0`: SMARTS `[F,Cl,Br,I]~*(~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K110=0`: SMARTS `[#7]~[#6]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K112=0`: SMARTS `*~*(~*)(~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K123=0`: SMARTS `[#8]~[#6]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K130=0`: SMARTS `[!#6;!#1]~[!#6;!#1]`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K134=0`: SMARTS `[F,Cl,Br,I]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K136=0`: SMARTS `[#8]=*`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K146=0`: SMARTS `[#8]`; count_parameter=2; bit-one activation: `unique_substructure_match_count > 2`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K162=1`: SMARTS `a`; count_parameter=0; bit-one activation: `has_substructure_match`; definition RDKit 2026.09.1.

Use the complete RDKit MACCS167 calculation as the authority. A required zero means the key's activation criterion is false; for a count key it does not necessarily mean that no matching substructure exists. Preserve count thresholds and special-key logic. Do not turn a special key into a guessed SMARTS pattern or infer a functional-group name from a key number.

## Chemical preferences

No additional chemical preferences; diversify structures within the frozen constraints.

Respect explicit chemical exclusions and required motifs. Use the remaining preferences to diversify candidates. If a hard preference conflicts with a frozen rule, explain the conflict instead of silently relaxing it.

## Repeat-unit representation

- Return each original repeat unit in the `SMILES` field with exactly two terminal `*` attachment atoms. Each `*` must have one neighbor and a single attachment bond. Use chemically plausible valences and a single connected repeat unit.
- Keep both attachment sites in the reported structure. H-cap is a separate computational copy used to calculate MACCS: replace the two supported terminal single-bond stars with hydrogen using the frozen model's representation contract. Never return the H-capped molecule in place of the repeat unit or reconstruct attachment sites from it.
- Return distinct proposals; do not claim database novelty, synthetic feasibility, or measured property values without evidence.

## Output and checking

Return a table with columns `candidate_id`, `SMILES`, `design_note`, `verification_status`, and `failed_conditions`. Use short design notes tied to the stated chemical preferences.

When a compatible checker is available, retain every original proposal, check its structure and frozen MACCS conditions, and report the actual status plus every failed condition. Do not fill missing fingerprints with zeros or claim a pass from visual inspection. If fewer than 20 candidates pass, report the shortfall and retain the failed proposals rather than changing the rules.

Without a computational checker, use `verification_status=generation_only` and `failed_conditions=not_evaluated`.
