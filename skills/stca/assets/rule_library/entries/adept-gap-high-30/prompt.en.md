# Generate polymer repeat units with frozen STCA rules

Propose 20 distinct polymer repeat-unit candidates for the goals below. Generate the structures in this conversation; the user does not need to configure Python or an external model API.

## Design goals

1. Isolated-monomer HOMO-LUMO gap; high / Top 30%; source-training physical boundary: >= 12.296064242 eV; rule source: adept-gap-high-30.

Each percentage describes the desired tail of its source dataset, not the percentage of generated candidates that will pass. A physical cutoff, when supplied, is the frozen training-label boundary; a rule match does not predict a property value or establish experimental success.

## Exact frozen structural constraints

Objective 1 — Isolated-monomer HOMO-LUMO gap:

`K80=0 AND K161=0 AND K165=0 AND K119=0 AND K70=0 AND K156=0 AND K94=0 AND K142=0 AND K81=0 AND K127=0`

Rule signature: `STCA|AND|K70=0&K80=0&K81=0&K94=0&K119=0&K127=0&K142=0&K156=0&K161=0&K165=0`

Satisfy every literal within each selected rule using AND. For multiple goals, apply all selected rules to the same repeat unit and require their intersection. Preserve the key numbers and required 0/1 values. Do not substitute a rule from another percentage, weaken a condition, or combine alternative family members into a new rule. Report a conflict if the requirements cannot be satisfied together.

## MACCS activation semantics

- `K70=0`: SMARTS `[!#6;!#1]~[#7]~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K80=0`: SMARTS `[#7]~*~*~*~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K81=0`: SMARTS `[#16]~*(~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K94=0`: SMARTS `[!#6;!#1]~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K119=0`: SMARTS `[#7]=*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K127=0`: SMARTS `*@*!@[#8]`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K142=0`: SMARTS `[#7]`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K156=0`: SMARTS `[#7]~*(~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K161=0`: SMARTS `[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.
- `K165=0`: SMARTS `[R]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2025.09.4.

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
