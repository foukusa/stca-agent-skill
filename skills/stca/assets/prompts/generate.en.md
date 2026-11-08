# {{GENERATION_TITLE}}

Propose {{COUNT}} distinct {{CANDIDATE_KIND}} candidates for the goals below. Generate the structures in this conversation; the user does not need to configure Python or an external model API.

## Design goals

{{OBJECTIVES}}

Each percentage describes the desired tail of its source dataset, not the percentage of generated candidates that will pass. A physical cutoff, when supplied, is the frozen training-label boundary; a rule match does not predict a property value or establish experimental success.

## Exact frozen structural constraints

{{EXACT_AND_CONDITIONS}}

Satisfy every literal within each selected rule using AND. For multiple goals, apply all selected rules to the same {{STRUCTURE_SUBJECT}} and require their intersection. Preserve the key numbers and required 0/1 values. Do not substitute a rule from another percentage, weaken a condition, or combine alternative family members into a new rule. Report a conflict if the requirements cannot be satisfied together.

## MACCS activation semantics

{{MACCS_LITERAL_SEMANTICS}}

Use the complete RDKit MACCS167 calculation as the authority. A required zero means the key's activation criterion is false; for a count key it does not necessarily mean that no matching substructure exists. Preserve count thresholds and special-key logic. Do not turn a special key into a guessed SMARTS pattern or infer a functional-group name from a key number.

## Chemical preferences

{{CHEMICAL_PREFERENCES}}

Respect explicit chemical exclusions and required motifs. Use the remaining preferences to diversify candidates. If a hard preference conflicts with a frozen rule, explain the conflict instead of silently relaxing it.

{{STRUCTURE_REPRESENTATION}}

## Output and checking

Return a table with columns `candidate_id`, `SMILES`, `design_note`, `verification_status`, and `failed_conditions`. Use short design notes tied to the stated chemical preferences.

When a compatible checker is available, retain every original proposal, check its structure and frozen MACCS conditions, and report the actual status plus every failed condition. Do not fill missing fingerprints with zeros or claim a pass from visual inspection. If fewer than {{COUNT}} candidates pass, report the shortfall and retain the failed proposals rather than changing the rules.

Without a computational checker, use `verification_status=generation_only` and `failed_conditions=not_evaluated`.
