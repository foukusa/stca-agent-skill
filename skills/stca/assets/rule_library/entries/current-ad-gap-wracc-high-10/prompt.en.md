# Generate polymer repeat units with frozen exact AND rules

Method attribution: conditions labelled WRAcc were learned by WRAcc and are not STCA training conclusions. The historical `STCA|AND|` signature prefix identifies exact conditions, not the learner.

Propose 20 distinct polymer repeat-unit candidates for the goals below. Generate the structures in this conversation; the user does not need to configure Python or an external model API.

## Design goals

1. H-capped isolated-monomer HOMO–LUMO gap; high / Top 10%; source-training physical boundary: >= 12.938749639 eV; rule source: current-ad-gap-wracc-high-10. Rule learner: WRAcc.

Each percentage describes the desired tail of its source dataset, not the percentage of generated candidates that will pass. A physical cutoff, when supplied, is the frozen training-label boundary; a rule match does not predict a property value or establish experimental success.

## Exact frozen structural constraints

Objective 1 — H-capped isolated-monomer HOMO–LUMO gap:

`K13=0 AND K14=0 AND K17=0 AND K18=0 AND K19=0 AND K21=0 AND K22=0 AND K23=0 AND K24=0 AND K25=0 AND K26=0 AND K30=0 AND K32=0 AND K33=0 AND K34=0 AND K35=0 AND K36=0 AND K37=0 AND K38=0 AND K39=0 AND K40=0 AND K43=0 AND K44=0 AND K45=0 AND K47=0 AND K48=0 AND K49=0 AND K50=0 AND K51=0 AND K52=0 AND K53=0 AND K54=0 AND K55=0 AND K56=0 AND K58=0 AND K59=0 AND K60=0 AND K61=0 AND K62=0 AND K63=0 AND K64=0 AND K65=0 AND K67=0 AND K70=0 AND K71=0 AND K73=0 AND K75=0 AND K76=0 AND K77=0 AND K78=0 AND K79=0 AND K81=0 AND K84=0 AND K85=0 AND K88=0 AND K91=0 AND K92=0 AND K95=0 AND K97=0 AND K99=0 AND K100=0 AND K110=0 AND K113=0 AND K117=0 AND K121=0 AND K122=0 AND K125=0 AND K127=0 AND K133=0 AND K136=0 AND K140=0 AND K145=0 AND K158=0 AND K162=0`

Rule signature: `STCA|AND|K13=0&K14=0&K17=0&K18=0&K19=0&K21=0&K22=0&K23=0&K24=0&K25=0&K26=0&K30=0&K32=0&K33=0&K34=0&K35=0&K36=0&K37=0&K38=0&K39=0&K40=0&K43=0&K44=0&K45=0&K47=0&K48=0&K49=0&K50=0&K51=0&K52=0&K53=0&K54=0&K55=0&K56=0&K58=0&K59=0&K60=0&K61=0&K62=0&K63=0&K64=0&K65=0&K67=0&K70=0&K71=0&K73=0&K75=0&K76=0&K77=0&K78=0&K79=0&K81=0&K84=0&K85=0&K88=0&K91=0&K92=0&K95=0&K97=0&K99=0&K100=0&K110=0&K113=0&K117=0&K121=0&K122=0&K125=0&K127=0&K133=0&K136=0&K140=0&K145=0&K158=0&K162=0`

Satisfy every literal within each selected rule using AND. For multiple goals, apply all selected rules to the same repeat unit and require their intersection. Preserve the key numbers and required 0/1 values. Do not substitute a rule from another percentage, weaken a condition, or combine alternative family members into a new rule. Report a conflict if the requirements cannot be satisfied together.

## MACCS activation semantics

- `K13=0`: SMARTS `[#8]~[#7](~[#6])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K14=0`: SMARTS `[#16]-[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K17=0`: SMARTS `[#6]#[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K18=0`: SMARTS `[#5,#13,#31,#49,#81]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K19=0`: SMARTS `*1~*~*~*~*~*~*~1`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K21=0`: SMARTS `[#6]=[#6](~[!#6;!#1])~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K22=0`: SMARTS `*1~*~*~1`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K23=0`: SMARTS `[#7]~[#6](~[#8])~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K24=0`: SMARTS `[#7]-[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K25=0`: SMARTS `[#7]~[#6](~[#7])~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K26=0`: SMARTS `[#6]=;@[#6](@*)@*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K30=0`: SMARTS `[#6]~[!#6;!#1](~[#6])(~[#6])~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K32=0`: SMARTS `[#6]~[#16]~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K33=0`: SMARTS `[#7]~[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K34=0`: SMARTS `[CH2]=*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K35=0`: SMARTS `[Li,Na,K,Rb,Cs,Fr]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K36=0`: SMARTS `[#16R]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K37=0`: SMARTS `[#7]~[#6](~[#8])~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K38=0`: SMARTS `[#7]~[#6](~[#6])~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K39=0`: SMARTS `[#8]~[#16](~[#8])~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K40=0`: SMARTS `[#16]-[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K43=0`: SMARTS `[!#6;!#1;!H0]~*~[!#6;!#1;!H0]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K44=0`: SMARTS `[!#1;!#6;!#7;!#8;!#9;!#14;!#15;!#16;!#17;!#35;!#53]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K45=0`: SMARTS `[#6]=[#6]~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K47=0`: SMARTS `[#16]~*~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K48=0`: SMARTS `[#8]~[!#6;!#1](~[#8])(~[#8])`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K49=0`: SMARTS `[!+0]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K50=0`: SMARTS `[#6]=[#6](~[#6])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K51=0`: SMARTS `[#6]~[#16]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K52=0`: SMARTS `[#7]~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K53=0`: SMARTS `[!#6;!#1;!H0]~*~*~*~[!#6;!#1;!H0]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K54=0`: SMARTS `[!#6;!#1;!H0]~*~*~[!#6;!#1;!H0]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K55=0`: SMARTS `[#8]~[#16]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K56=0`: SMARTS `[#8]~[#7](~[#8])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K58=0`: SMARTS `[!#6;!#1]~[#16]~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K59=0`: SMARTS `[#16]!:*:*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K60=0`: SMARTS `[#16]=[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K61=0`: SMARTS `*~[#16](~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K62=0`: SMARTS `*@*!@*@*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K63=0`: SMARTS `[#7]=[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K64=0`: SMARTS `*@*!@[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K65=0`: SMARTS `c:n`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K67=0`: SMARTS `[!#6;!#1]~[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K70=0`: SMARTS `[!#6;!#1]~[#7]~[!#6;!#1]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K71=0`: SMARTS `[#7]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K73=0`: SMARTS `[#16]=*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K75=0`: SMARTS `*!@[#7]@*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K76=0`: SMARTS `[#6]=[#6](~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K77=0`: SMARTS `[#7]~*~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K78=0`: SMARTS `[#6]=[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K79=0`: SMARTS `[#7]~*~*~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K81=0`: SMARTS `[#16]~*(~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K84=0`: SMARTS `[NH2]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K85=0`: SMARTS `[#6]~[#7](~[#6])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K88=0`: SMARTS `[#16]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K91=0`: SMARTS `[$([!#6;!#1;!H0]~*~*~*~[CH2]~*),$([!#6;!#1;!H0;R]1@[R]@[R]@[R]@[CH2;R]1),$([!#6;!#1;!H0]~[R]1@[R]@[R]@[CH2;R]1),$([!#6;!#1;!H0]~*~[R]1@[R]@[CH2;R]1)]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K92=0`: SMARTS `[#8]~[#6](~[#7])~[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K95=0`: SMARTS `[#7]~*~*~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K97=0`: SMARTS `[#7]~*~*~*~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K99=0`: SMARTS `[#6]=[#6]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K100=0`: SMARTS `*~[CH2]~[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K110=0`: SMARTS `[#7]~[#6]~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K113=0`: SMARTS `[#8]!:*:*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K117=0`: SMARTS `[#7]~*~[#8]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K121=0`: SMARTS `[#7;R]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K122=0`: SMARTS `*~[#7](~*)~*`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K125=0`: special/undefined key; use the complete MACCS generator; the activation criterion must be false; a count key does not imply zero matches; definition RDKit 2026.09.1.
- `K127=0`: SMARTS `*@*!@[#8]`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K133=0`: SMARTS `*@*!@[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K136=0`: SMARTS `[#8]=*`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K140=0`: SMARTS `[#8]`; count_parameter=3; bit-one activation: `unique_substructure_match_count > 3`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K145=0`: SMARTS `*1~*~*~*~*~*~1`; count_parameter=1; bit-one activation: `unique_substructure_match_count > 1`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K158=0`: SMARTS `[#6]-[#7]`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.
- `K162=0`: SMARTS `a`; count_parameter=0; bit-one activation: `has_substructure_match`; The bit-one activation criterion is not met; for a count key this need not mean no matches.; definition RDKit 2026.09.1.

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
