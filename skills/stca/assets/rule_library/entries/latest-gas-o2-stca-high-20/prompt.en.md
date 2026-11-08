Learner: STCA. Role: primary for GAS_O2 Top 20%. These supplied frozen conditions were refitted on all cleaned data. The STCA|AND| signature identifies the conjunction format; the learner is STCA.

# Generate polymer repeat units with frozen STCA rules

Propose 20 distinct polymer repeat-unit candidates for the goals below. Generate the structures in this conversation; the user does not need to configure Python or an external model API.

## Design goals

1. O2 permeability; high / Top 20%; source-training physical boundary: >= 203.080764076594 Barrer; model-space boundary: >= 2.30766878873702 log10(Barrer); rule source: latest-gas-o2-stca-high-20. Rule learner: STCA.

Each percentage describes the desired tail of its source dataset, not the percentage of generated candidates that will pass. A physical cutoff, when supplied, is the frozen training-label boundary; a rule match does not predict a property value or establish experimental success.

## Exact frozen structural constraints

Objective 1 — O2 permeability:

`K149=1 AND K112=1 AND K125=1 AND K145=1 AND K105=1 AND K74=1 AND K101=1 AND K162=1 AND K165=1 AND K99=1`

Rule signature: `STCA|AND|K74=1&K99=1&K101=1&K105=1&K112=1&K125=1&K145=1&K149=1&K162=1&K165=1`

Satisfy every literal within each selected rule using AND. For multiple goals, apply all selected rules to the same repeat unit and require their intersection. Preserve the key numbers and required 0/1 values. Do not substitute a rule from another percentage, weaken a condition, or combine alternative family members into a new rule. Report a conflict if the requirements cannot be satisfied together.

## MACCS activation semantics

- `K74=1`: SMARTS `[CH3]~*~[CH3]`; count_parameter=0; bit-one activation: `has_substructure_match`; definition RDKit 2026.09.1.
- `K99=1`: SMARTS `[#6]=[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; definition RDKit 2026.09.1.
- `K101=1`: SMARTS `[$([R]@1@[R]@[R]@[R]@[R]@[R]@[R]@[R]1),$([R]@1@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]1),$([R]@1@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]1),$([R]@1@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]1),$([R]@1@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]1),$([R]@1@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]1),$([R]@1@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]@[R]1)]`; count_parameter=0; bit-one activation: `has_substructure_match`; definition RDKit 2026.09.1.
- `K105=1`: SMARTS `*@*(@*)@*`; count_parameter=0; bit-one activation: `has_substructure_match`; definition RDKit 2026.09.1.
- `K112=1`: SMARTS `*~*(~*)(~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; definition RDKit 2026.09.1.
- `K125=1`: special/undefined key; use the complete MACCS generator; definition RDKit 2026.09.1.
- `K145=1`: SMARTS `*1~*~*~*~*~*~1`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; definition RDKit 2026.09.1.
- `K149=1`: SMARTS `[C;H3,H4]`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; definition RDKit 2026.09.1.
- `K162=1`: SMARTS `a`; count_parameter=0; bit-one activation: `has_substructure_match`; definition RDKit 2026.09.1.
- `K165=1`: SMARTS `[R]`; count_parameter=0; bit-one activation: `has_substructure_match`; definition RDKit 2026.09.1.

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
