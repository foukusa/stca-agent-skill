# Generate polymer repeat units with frozen exact AND rules

Method attribution: conditions labelled WRAcc were learned by WRAcc and are not STCA training conclusions. The historical `STCA|AND|` signature prefix identifies exact conditions, not the learner.

Propose 20 distinct polymer repeat-unit candidates for the goals below. Generate the structures in this conversation; the user does not need to configure Python or an external model API.

## Design goals

1. Thermal conductivity; high / Top 10%; source-training physical boundary: >= 0.356 W/(m K); rule source: current-ad-tc-wracc-high-10. Rule learner: WRAcc.

Each percentage describes the desired tail of its source dataset, not the percentage of generated candidates that will pass. A physical cutoff, when supplied, is the frozen training-label boundary; a rule match does not predict a property value or establish experimental success.

## Exact frozen structural constraints

Objective 1 — Thermal conductivity:

`K11=0 AND K14=0 AND K19=0 AND K22=0 AND K24=0 AND K27=0 AND K41=0 AND K42=0 AND K46=0 AND K50=0 AND K64=0 AND K66=0 AND K73=0 AND K74=0 AND K89=0 AND K107=0 AND K122=0 AND K123=0 AND K141=0`

Rule signature: `STCA|AND|K11=0&K14=0&K19=0&K22=0&K24=0&K27=0&K41=0&K42=0&K46=0&K50=0&K64=0&K66=0&K73=0&K74=0&K89=0&K107=0&K122=0&K123=0&K141=0`

Satisfy every literal within each selected rule using AND. For multiple goals, apply all selected rules to the same repeat unit and require their intersection. Preserve the key numbers and required 0/1 values. Do not substitute a rule from another percentage, weaken a condition, or combine alternative family members into a new rule. Report a conflict if the requirements cannot be satisfied together.

## MACCS activation semantics

- `K11=0`: SMARTS `*1~*~*~*~1`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K14=0`: SMARTS `[#16]-[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K19=0`: SMARTS `*1~*~*~*~*~*~*~1`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K22=0`: SMARTS `*1~*~*~1`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K24=0`: SMARTS `[#7]-[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K27=0`: SMARTS `[I]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K41=0`: SMARTS `[#6]#[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K42=0`: SMARTS `F`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K46=0`: SMARTS `Br`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K50=0`: SMARTS `[#6]=[#6](~[#6])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K64=0`: SMARTS `*@*!@[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K66=0`: SMARTS `[#6]~[#6](~[#6])(~[#6])~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K73=0`: SMARTS `[#16]=*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K74=0`: SMARTS `[CH3]~*~[CH3]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K89=0`: SMARTS `[#8]~*~*~*~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K107=0`: SMARTS `[F,Cl,Br,I]~*(~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K122=0`: SMARTS `*~[#7](~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K123=0`: SMARTS `[#8]~[#6]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K141=0`: SMARTS `[CH3]`; count_parameter=2; bit-one activation: `unique_substructure_match_count > 2`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.

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
