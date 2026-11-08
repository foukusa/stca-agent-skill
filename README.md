<p align="center"><img src="assets/stca-logo.png" alt="STCA logo" width="104"></p>
<h1 align="center">STCA Agent Skill</h1>
<p align="center">Readable polymer screening rules, labeled-data rule extraction, and rule-guided candidate verification.</p>
<p align="center"><strong>0.1.0</strong> · English · <a href="README.zh-CN.md">简体中文</a></p>

## Contents

- [What it does](#what-it-does)
- [Quick start](#quick-start)
- [Install and invoke](#install-and-invoke)
- [Published rules](#published-rules)
- [Rules from your labeled data](#rules-from-your-labeled-data)
- [Case studies and target choices](#case-studies-and-target-choices)
- [Rule-guided candidate design](#rule-guided-candidate-design)
- [Data and output contracts](#data-and-output-contracts)
- [Evidence and limits](#evidence-and-limits)
- [Paper and author](#paper-and-author)
- [License](#license)

## What it does

STCA Agent Skill calls Weihao Wang’s pinned **Sliding Threshold Correlation Analysis** implementation. The host agent organizes the task and proposes candidates; the author’s code computes threshold–substructure correlations, ranked prefix rule families, frozen decisions and evaluation metrics.

| Workflow | Input | Output |
|---|---|---|
| **Apply published rules** | New repeat-unit SMILES and explicit profile/tier | Frozen-rule decisions and each failed structural condition |
| **Learn from labeled data** | Structures, labeled target, unit, direction, percentage tiers and source/evaluation roles | Source-only preparation, complete rule family, frozen model, physical cutoffs and holdout metrics |
| **Guide and verify design** | Frozen constraints, proposal count and allowed chemistry | All raw proposals, H-cap audit structures and verified original repeat units |

The paper’s chemical-space split uses **2048-bit Morgan radius 2 (ECFP4-like)**. The readable STCA rules use **RDKit MACCS167**, a separate representation. Applying a frozen paper rule to new candidates does not re-split or retrain them. Custom-data analysis is identified separately from paper reproduction.

## Quick start

Example candidate input:

```csv
CandidateKey,SMILES
sample-A7,*CC*
42-blue,*CCO*
```

Invoke a published-rule task:

```text
Use STCA to screen candidates.csv with the frozen paper rules.
Targets: Tg high, tier 0.20; EC low, tier 0.10.
CandidateKey is an optional row label and SMILES is the original repeat unit.
Use H-cap only for MACCS calculation, return the original star-containing structures,
list every failed condition, and save the results in out/screening.
```

Every target has its own **property, direction and percentage tier**. `high/low` is the direction; the tier defines the corresponding tail. No default 5% tier or shared global percentage is assumed. An identifier is optional, may have any name and is never a descriptor.

## Install and invoke

Install from the repository in a compatible Agent Skills host:

```bash
npx skills add foukusa/stca-agent-skill --skill stca
```

Or copy the complete `skills/stca` directory into your host’s skill directory. Keep its `scripts/`, `references/` and `assets/` together.

| Host | Invocation |
|---|---|
| ChatGPT | Select the installed STCA plugin/skill, then `@STCA` with input and targets |
| Codex | Select the installed skill or write `Use $stca ...` |
| DeepSeek Harness | `/stca ...`; default global skill location `~/.dsh/skills/stca` |
| WorkBuddy | Enable the installed STCA skill and write `Use the STCA skill ...` |

Catalog installation depends on an available published listing. Local skill installation requires a host with script execution and the Python/RDKit runtime. Use the bundled environment instructions; attaching a skill alone does not supply scientific libraries.

For a local environment from the repository root:

```bash
export SKILL_DIR="$PWD/skills/stca"
python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$HOME/.venvs/stca-0.1.0" > stca-setup.json
STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"
```

Reuse an existing prepared environment instead of overwriting it. The pinned source commit is `5951b0ef23d63edc8f7e803aaaffa5e4168288f6`.

## Published rules

| Profile | Direction | Supported tiers |
|---|---|---|
| `tg-high` | High Tg | Top 30%, 20%, 10% |
| `ec-low` | Insulating / low EC | Bottom 20%, 15%, 10%, 5% |
| `ec-high` | Conducting / high EC | Top 20%, 15%, 10%, 5% |

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --profile tg-high --protocol paper --tier 0.20 \
  --input candidates.csv --id-column CandidateKey --smiles-column SMILES \
  --output-dir out/tg_top20
```

Omit `--id-column` if no row label is supplied. `results.csv` returns the preserved original structures; `rows.csv` includes calculation-only H-cap structures and errors. Invalid rows remain explicit errors/unknowns.

Published transfer examples are not universal property models. Applying Tg-derived rules to TC or EC-derived rules to permittivity requires an **explicit transfer request**; a new measured property should normally have its own custom rule model. The software never substitutes one property’s cutoff for another property’s unit.

## Rules from your labeled data

Use **`auto_screen.py`** for a complete custom-data task: validate and clean unusable records, prepare H-cap, choose the target transform and scan resolution within source data, select scan support within source, freeze the rules and evaluate the held-out role.

```text
Use STCA automatic custom-data mode on permeability.csv.
The target is Permeability in Barrer, direction high, with tiers 0.10, 0.15, 0.20, 0.25 and 0.30.
Automatically clean unusable structures and targets, preserve the original rows and exclusion reasons,
and use ECFP4 chemical-space roles. If Role already contains source/holdout, preserve those roles.
Choose the transform, value-scan step and support settings from source data only;
freeze the rules before outer evaluation. Return all tiers, physical cutoffs, failed conditions
and the strictest source-eligible tier. Do not select settings from holdout performance.
```

```bash
"$STCA_PY" "$SKILL_DIR/scripts/auto_screen.py" \
  --input permeability.csv --smiles-column SMILES --target Permeability \
  --unit Barrer --direction high --tiers 0.10,0.15,0.20,0.25,0.30 \
  --data-kind experimental --output-dir out/permeability_auto
```

- Without `--role-column`, the automatic workflow creates **2048-bit Morgan radius-2 (ECFP4-like) t-SNE roles**, with a requested outer 20% reserved for evaluation, and repeats the procedure within source for inner selection. Original-structure, H-cap and optional group protection can increase the held-out fraction. These are new custom-data roles, not a recreation of the paper’s exact members.
- With `--role-column Role`, the provided source/holdout roles are preserved. Inner selection remains within source.
- Unusable SMILES, unsupported connection points, nonfinite targets and exact duplicate exports with the same nonempty explicit ID and complete original row are automatically excluded from fitting with an `excluded_rows.csv` reason/row mapping. The original file is unchanged.
- Explicit `--quality-column` with `--exclude-quality-value` (repeat for multiple values), or `--target-min` / `--target-max`, applies declared quality or admissible-range rules. These are data-contract filters, not a search for deletions that raise a score. Valid unusual values, processing differences and repeated measurements are not silently averaged or removed using neighbour labels.
- Transform and bounded value-grid settings are source-owned. Strictly positive targets spanning at least two robust decades can use log10. Input that is already logarithmic must be declared to prevent a second log.
- Default nested selection compares predeclared minimum-subset settings within source, then refits the chosen recipe on the complete source. `--scan-policy fixed` is available for an explicitly fixed recipe.
- Every requested tier remains in the report. Eligibility uses the selected recipe’s source-internal validation: a valid evaluation with nonzero coverage, positive MCC and precision above validation prevalence. The smallest eligible fraction is the recommendation; it is not outer validation. An explicitly fixed recipe has no inner-validation recommendation.

The model retains its real target, unit, transform and numerical cutoffs in both model and physical scales. Automatic outputs include `input_format_audit.json`, `cleaned_input.csv`, `excluded_rows.csv`, `cleaning_audit.json`, `workflow_input.csv`, `split_membership.csv`, `split_audit.json`, `fit/source_settings.json` and `tier_recommendations.json`. A 72-record workflow check excluded an invalid SMILES and a missing target, kept 70 usable records and preserved the input unchanged; this verifies cleaning behavior, not scientific generalization. The automatic model is `out/permeability_auto/fit/model.json`; the run manifest records the path. Add `--candidates candidates.csv` to screen at the recommended inner-validation tier, or specify a fitted `--screen-tier`. No eligible tier means diagnostics are retained without an invented recommendation. Use the frozen model for later screening, constraint export and evaluation.

### Controlled fitting and frozen evaluation

For manually declared roles and settings, `custom_fit.py` remains available:

```bash
"$STCA_PY" "$SKILL_DIR/scripts/custom_fit.py" \
  --input permeability.csv --smiles-column SMILES \
  --target Permeability --unit Barrer --direction high --tiers 0.30,0.20,0.15,0.10 \
  --role-column Role --source-value source --evaluation-value holdout \
  --transform auto --scan-policy fixed --min-subset-size 1 \
  --data-kind experimental --output-dir out/permeability_fit
```

This controlled interface defaults to transform `none` and a fixed minimum subset of 1; `auto` or nested settings must be requested explicitly. It does not change the published frozen rules.

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --model out/permeability_fit/model.json --tier 0.20 \
  --input candidates.csv --smiles-column SMILES --output-dir out/permeability_candidates
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" export-rules \
  --model out/permeability_fit/model.json --tier 0.20 --output-dir out/permeability_constraints
"$STCA_PY" "$SKILL_DIR/scripts/evaluate_custom.py" \
  --model out/permeability_fit/model.json --input independent.csv \
  --target Permeability --property Permeability --unit Barrer \
  --smiles-column SMILES --cutoff-mode fixed_train --output-dir out/independent_evaluation
```

Frozen evaluation reuses the saved transform and source cutoff without refitting. The property and input unit must match the contract; `--property` is the actual saved target name. `dataset_relative` is a separately declared percentile-based task, not the same physical-threshold target. Exceptions remain explicit errors rather than invented zero scores.

Detailed contracts: [custom-data guide](skills/stca/references/custom_data.md), [commands](skills/stca/references/commands.md).

## Case studies and target choices

The supplied trial contains **13 property tasks**: measured CO₂/O₂ permeability; RadonPy MD thermal conductivity, refractive index, density, heat capacity and dielectric constant; and ADEPT MD/DFT thermal conductivity, density, isolated-monomer HOMO–LUMO gap, dielectric constant, refractive index and Tg. See the [dataset guide](examples/open_data/README.md) and [registry](examples/open_data/dataset_registry.csv) for public source links, raw column names, units, counts and source/license notes. Computed labels are not experimental confirmation, and public access does not establish unrestricted data redistribution.

### Representative ECFP4 results

The following **archived cases were selected to illustrate settings where STCA outperformed the listed WRAcc and RF comparisons**. They are not a claim of superiority on every dataset. The main study uses 2048-bit radius-2 Morgan/ECFP4-like roles; [all archived cases](examples/open_data/archived_case_metrics.csv) and the [full cross-source table](examples/open_data/ecfp4_cross_source_all.csv) remain available, including weaker results. Compare methods only on the same dataset, role definition and tier.

| Archived task | Tier | STCA MCC | WRAcc MCC | RF MCC |
|---|---|---:|---:|---:|
| ADEPT isolated-monomer HOMO–LUMO gap | Top 10% | **0.702837** | 0.467958 | 0.566755 |
| RadonPy density | Top 30% | **0.837995** | 0.807575 | 0.748950 |
| RI, ADEPT → RadonPy | Top 10% | **0.50** | 0.41 | 0.37 |
| RI, ADEPT → RadonPy | Top 20% | **0.60** | 0.54 | 0.44 |

For ADEPT gap Top 10%, the archived outer role has 554 records, 22 positives, 39 selected and 21 true positives: Precision 0.5385, enrichment about 13.56, minimum subset 1 and scan step 0.02 eV. The target is the **hydrogen-capped isolated-monomer HOMO–LUMO gap**, not a bulk-polymer band gap. RadonPy density Top 30% uses a cutoff of 1.205 g/cm³, Precision 0.9468, minimum subset 42 and step 0.001 g/cm³. The RI cross-source rows use **`dataset_relative`** target labels after overlap removal; they must not be presented as unchanged physical-cutoff transfer. These are historical comparisons, not a claim that this update reran the full final study.

### Results from this automatic workflow

A new full raw-data run on RadonPy density kept all 1,077 input records, creating 862 source / 215 outer records. It automatically chose transform `none`, step 0.001 g/cm³ and minimum subset 44. One displayed tier is:

| New automatic task | Tier and cutoff | STCA MCC | WRAcc MCC | RF MCC |
|---|---|---:|---:|---:|
| RadonPy density | Top 15%, 1.27979818 g/cm³ | **0.542267** | 0.390058 | 0.430808 |

At this tier, 19 of 24 selections are true positives: Precision 0.791667, recall 19/41 = 0.463415 and enrichment 4.1514. **Top 15% is shown as an observed result; the source-internal recommendation was Top 10%.** This displayed row must not be used to replace that recommendation after seeing outer scores. The [complete new five-tier table](examples/open_data/current_computed_cases.csv) retains every requested outcome, including the low-support ADEPT gap run. New ECFP4 memberships and automatic settings differ from the historical study, so the two result sets are distinct experiments.

A second automatic run read the official raw Dataset A directly: **778 rows and 33 input columns**. It aliased the empty header in `input_format_audit.json` while preserving column values, then excluded 296 missing measured CO2 targets and one unsupported structure, leaving **481 rows (381 source / 100 outer)**. Source-only automation chose log10, step 0.0005 in model scale and minimum subset 20. Top 15% uses cutoff **2,800 Barrer**, with MCC **0.486**; MCC at 10/15/20/25/30% is 0.450/0.486/0.503/0.526/0.526. See the [raw-gas automatic summary](examples/open_data/gas_auto_contract_summary.csv). This demonstrates the full input/preparation contract, retains mixed conditions, and is a different data version from the 251-row archived comparison; no baseline comparison was run for it.

### CO₂: several usable target choices

For the available **251-row ECFP4 snapshot (201 source / 50 outer)**, the archived step 0.01 and minimum subset 1 reproduce the 30%/20%/10% rules; the additional 25% and 15% runs extend that same snapshot.

| Top tier | Source cutoff (Barrer) | Outer positives | Selected | TP | MCC |
|---|---:|---:|---:|---:|---:|
| 30% | 840 | 15 | 18 | 11 | 0.5092 |
| 25% | 1,360 | 14 | 9 | 5 | 0.2875 |
| 20% | 2,901.93 | 9 | 9 | 3 | 0.1870 |
| 15% | 4,100 | 9 | 7 | 2 | 0.1110 |
| 10% | 6,100 | 9 | 7 | 2 | 0.1110 |

The 15% rule selects candidates; it happens to select the same seven outer records as the 10% rule, although the targets and source selections differ. Small outer-positive counts limit confidence. The added 15%/25% comparisons are exploratory extensions after earlier results were visible. The [case guide](examples/open_data/README.md) records these identities and reproducibility requirements.

### Choose the target rather than force 10%

Predeclare a range such as `0.10,0.15,0.20,0.25,0.30`. Automatic source eligibility returns each rule’s status and recommends the lowest eligible fraction; if 10% has no eligible source rule, it continues to 15%, 20% and the remaining requested choices. It does not stop the entire task or promise that a broader tier will succeed. Keep every prespecified outcome.

Select the main target using declared source/inner-validation criteria before looking at holdout performance. Expanding tiers because of a holdout result is exploratory and needs fresh independent confirmation. Top 10% → Top 20% changes the task; a fixed absolute application requirement remains fixed unless explicitly changed by the user.

```text
Automatically analyze my computed RI dataset with STCA using ECFP4 roles.
Predeclare Top 10%, 15%, 20%, 25% and 30%. Clean unusable records with a reason log,
choose transform/step/support within source, and recommend the strictest source-eligible tier.
Fit and freeze all requested tiers before outer evaluation; report the full results,
physical cutoffs and all failures. Do not choose a tier from holdout performance.
```

```bash
"$STCA_PY" "$SKILL_DIR/scripts/auto_screen.py" \
  --input computed_ri.csv --smiles-column SMILES --target RI --unit dimensionless \
  --direction high --tiers 0.10,0.15,0.20,0.25,0.30 --data-kind computed \
  --output-dir out/ri_multiple_tiers
```

Choose **high RI**, **high TC**, **low density**, **high isolated-monomer HOMO–LUMO gap** or **high CO₂ permeability**, using each property’s labels and units. Low density is a new direction, not validated by the archived high-density scores. A trained model can be frozen for repeated screening, used to constrain proposals, or combined with independently trained models on one candidate table.

```text
Automatically train a high-TC model and a low-density model from the supplied labeled tables.
Predeclare each property's own tiers. Use ECFP4 roles, automatic validity cleaning,
and source-only transform, scan step and support selection. Freeze both models,
then apply them to the same candidate SMILES. Report each decision, every failed condition
and the structural intersection. Claim joint measured performance only with paired
TC/density labels under comparable conditions.
```

## Rule-guided candidate design

```text
Use the frozen permeability model at tier 0.20 to propose 20 repeat units
with two terminal connection points. Preserve every raw proposal, use a temporary
H-cap copy for MACCS, verify every bit condition, and return original star structures.
Report all failed candidates and do not describe rule compliance as measured performance.
```

The host LLM proposes candidates; STCA supplies constraints and deterministic verification. Different frozen rules can be applied to the same candidate table and intersected. Constraints that conflict remain visible; the software does not discard conditions to manufacture a nonempty intersection.

## Data and output contracts

- **Identifiers:** any optional row label; generated receipts if absent. IDs do not define chemical-space splits or become model features.
- **Structures:** preserve original connection points, create H-cap only for calculation, return the exact original repeat unit. Identical capped graphs do not prove identical polymers.
- **Labeled data:** declare target, unit, direction, tiers, conditions, source/evaluation roles and any grouping needed to prevent related records crossing roles.
- **Auditable automatic cleaning:** unusable rows and declared quality/range filters are applied with exclusion reasons and raw-row mapping. Other unusual observations are flagged; aggregation or label-driven exclusion is not silently performed.
- **Evaluation:** freeze first. Report numerical physical cutoff, target counts, confusion counts, metric status and rule coverage. Few positives limit inference; they do not prohibit rule extraction or screening.

| Output | Meaning |
|---|---|
| Frozen model and complete rule family | Reusable conditions with target and protocol provenance |
| Source audit and scan settings | Source-only transform, scan grid, support and unresolved data flags |
| Tier cutoff table | Every percentage together with model-scale and physical-unit cutoff |
| Evaluation report | Counts, metrics, undefined/limited-support states and unchanged fixed training cutoff |
| Candidate results and audit rows | Original repeat units, decisions, failed conditions, H-cap evidence and collision flags |
| Constraint JSON / prompt | Exact bit logic for subsequent agent proposals |

A 20-positive support threshold is an adjustable diagnostic heuristic. A holdout with zero positives does not support a meaningful recall estimate; undefined values remain distinguishable from valid zero scores. Structural screening still runs.

## Evidence and limits

The main case study uses 13 experimental/MD/DFT property tasks and ECFP4-based roles. The representative comparison table above was selected from archived results; the full tables retain weak, negative and asymmetric transfer outcomes. New automatic workflow runs are reported with their own data hashes and settings rather than being substituted for archived scores.

- Original STCA prefix families and source selection remain in the author implementation.
- Source-only preprocessing and nested configuration are adapter recipes whose settings are recorded.
- Cross-property transfer is a hypothesis requiring explicit intent and validation; same-property cross-source transfer also needs condition and overlap checks.
- Structural intersections do not establish jointly measured properties without paired labels under comparable conditions.
- Rule compliance does not establish synthesis, novelty, causality or experimental property success.
- Recorded tests identify the runtime actually used. Target-host installation and macOS/Windows execution require their own checks.

See [validation scope](skills/stca/references/validation.md) and the release’s `validation/` records for exact evidence boundaries.

## Paper and author

- [STCA paper](https://doi.org/10.1038/s41524-026-02345-x)
- [Original polymer-stca implementation](https://github.com/foukusa/polymer-stca)
- [ORCID: 0009-0005-4445-7074](https://orcid.org/0009-0005-4445-7074)
- [Google Scholar: Weihao Wang](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)
- [ResearchGate: Weihao Wang](https://www.researchgate.net/profile/Weihao-Wang-23)
- [Software citation](CITATION.cff)

## License

Read [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The integration and original author implementation retain their respective terms.
