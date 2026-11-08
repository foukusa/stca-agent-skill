# Data-backed STCA examples

[中文](README.zh-CN.md) · [Repository guide](../../README.md) · Version **0.1.0**

## Contents

- [Choose a dataset and target](#choose-a-dataset-and-target)
- [Representative ECFP4 comparisons](#representative-ecfp4-comparisons)
- [Understand the evidence files](#understand-the-evidence-files)
- [CO2 and the 15% option](#co2-and-the-15-option)
- [Run an automatic custom case](#run-an-automatic-custom-case)
- [Choose among tiers and combine targets](#choose-among-tiers-and-combine-targets)

## Choose a dataset and target

The supplied trial covers **13 property tasks** from three data families. The [registry](dataset_registry.csv) separates raw observations, finite target values and historical processed structure counts. These counts describe the supplied snapshot, not a fresh download.

| Family and public source | Targets | Stored units | Suggested task options |
|---|---|---|---|
| [RadonPy PI1070](https://github.com/RadonPy/RadonPy/blob/develop/data/PI1070.csv) | TC, refractive index, density, Cp, dielectric constant | W/(m·K), dimensionless, g/cm³, J/(kg·K), dimensionless | High TC; high refractive index; high or low density; high Cp; high or low dielectric constant |
| [ADEPT / PolyGraphMT raw data](https://github.com/sobinalosious/PolyGraphMT/tree/main/data/raw) and [property definitions](https://github.com/sobinalosious/PolyGraphMT/blob/main/data/README.md) | TC, density, monomer HOMO–LUMO gap, dielectric constant, refractive index, Tg | W/(m·K), g/cm³, eV, dimensionless, dimensionless, K | Same-property custom fitting; separate models for a multi-target intersection |
| [PolymerGasMembraneML Dataset A](https://github.com/jsunn-y/PolymerGasMembraneML/blob/main/datasets/datasetA_imputed_all.csv) | Measured CO2 and O2 permeability | Barrer or explicitly declared log10(Barrer) | High gas permeability or a user-defined low-permeability target; several tail sizes |

The registry provides immutable download links, source commits and case-sensitive raw target/structure column names for all 13 tasks. Gas uses `Smiles`; RadonPy uses `smiles`; ADEPT uses `SMILES`. Map these explicitly to your input contract. If roles already exist, preserve them with `--role-column` and their declared values.

RadonPy and ADEPT properties are computational observations, not new experimental validation. ADEPT `BANDGAP_DFT.csv` is the HOMO–LUMO gap of an isolated hydrogen-capped monomer, not a measured bulk-polymer bandgap. The data authors' method and condition definitions remain part of the target.

Public access and redistribution terms are different. RadonPy declares BSD-3-Clause. The ADEPT/PolyGraphMT and gas dataset reuse terms need checking at their source; this repository distributes aggregate case evidence and source links. For gas data, select original measured `CO2`/`O2` or their original log columns; Bayesian/Etree imputed columns are a separate data type.

## Representative ECFP4 comparisons

These cases were **selected from the archived final study to show settings where STCA exceeded the listed WRAcc and RF baselines**. They do not establish superiority on every task. The main workflow uses radius-2, 2048-bit Morgan (ECFP4-like) roles; the readable STCA rules use MACCS on calculation-only H-cap structures. Compare methods on the same data, roles, target definition and tier.

| Archived task | Tier | STCA MCC | WRAcc MCC | RF MCC |
|---|---|---:|---:|---:|
| ADEPT isolated-monomer HOMO–LUMO gap | Top 10% | **0.702837** | 0.467958 | 0.566755 |
| RadonPy density | Top 30% | **0.837995** | 0.807575 | 0.748950 |
| RI, ADEPT → RadonPy | Top 10% | **0.50** | 0.41 | 0.37 |
| RI, ADEPT → RadonPy | Top 20% | **0.60** | 0.54 | 0.44 |

ADEPT gap Top 10% has 554 outer records, 22 positives, 39 selected and 21 true positives: Precision 0.5385 and enrichment about 13.56, using minimum subset 1 and step 0.02 eV. This remains an isolated-monomer target. RadonPy density Top 30% has cutoff 1.205 g/cm³ and Precision 0.9468, using minimum subset 42 and step 0.001 g/cm³. The RI cross-source cases use **`dataset_relative`** labels after overlap removal, not a frozen physical-cutoff transfer claim. These are archived results; this update does not claim to rerun the entire final study.

### Results from this automatic workflow

A new full raw-data run on RadonPy density kept all 1,077 input records, creating 862 source / 215 outer records. It automatically chose transform `none`, step 0.001 g/cm³ and minimum subset 44. One displayed tier is:

| New automatic task | Tier and cutoff | STCA MCC | WRAcc MCC | RF MCC |
|---|---|---:|---:|---:|
| RadonPy density | Top 15%, 1.27979818 g/cm³ | **0.542267** | 0.390058 | 0.430808 |

At this tier, 19 of 24 selections are true positives: Precision 0.791667, recall 19/41 = 0.463415 and enrichment 4.1514. **Top 15% is shown as an observed result; the source-internal recommendation was Top 10%.** This displayed row must not be used to replace that recommendation after seeing outer scores. The [complete new five-tier table](current_computed_cases.csv) retains every requested outcome, including the low-support ADEPT gap run. New ECFP4 memberships and automatic settings differ from the historical study, so the two result sets are distinct experiments.

A second automatic run read the official raw Dataset A directly: **778 rows and 33 input columns**. It aliased the empty header in `input_format_audit.json` while preserving column values, then excluded 296 missing measured CO2 targets and one unsupported structure, leaving **481 rows (381 source / 100 outer)**. Source-only automation chose log10, step 0.0005 in model scale and minimum subset 20. Top 15% uses cutoff **2,800 Barrer**, with MCC **0.486**; MCC at 10/15/20/25/30% is 0.450/0.486/0.503/0.526/0.526. See the [raw-gas automatic summary](gas_auto_contract_summary.csv). This demonstrates the full input/preparation contract, retains mixed conditions, and is a different data version from the 251-row archived comparison; no baseline comparison was run for it.

## Understand the evidence files

| File | Scope |
|---|---|
| [dataset_registry.csv](dataset_registry.csv) | 13 targets, source links, units and historical data counts |
| [ecfp4_selected_comparisons.csv](ecfp4_selected_comparisons.csv) | The displayed representative winning cases and exact MCC differences |
| [archived_case_metrics.csv](archived_case_metrics.csv) | All final `three_mode_study` 30/20/10% outcomes, actual cutoffs and support; retains weak and negative cases |
| [ecfp4_cross_source_all.csv](ecfp4_cross_source_all.csv) | The full archived ECFP4 cross-source comparison, including direction-dependent results |
| [current_computed_cases.csv](current_computed_cases.csv) | Complete new ECFP4 automatic runs with all requested tiers |
| [current_case_provenance.json](current_case_provenance.json) | New input hashes, automatic choices, roles and original-field checks |
| [co2_tier_comparison.csv](co2_tier_comparison.csv) | Five-tier CO2 measurements and explicitly identified snapshot provenance; the main example below uses the 251-row ECFP4 snapshot |
| [gas_auto_contract_summary.csv](gas_auto_contract_summary.csv) | Official raw-gas automatic preparation and five-tier results |
| [co2_integrity_checks.json](co2_integrity_checks.json) | Independent MACCS predictions, confusion counts, original-field preservation and historical comparisons |

Historical blank metrics mean not reported. An archived zero can also reflect constant predictions or a caught error; the detailed table retains the raw value and interpreted status. Tg has a published-rule transfer record in the archive but no final custom-fitting metric row. No score is filled in for a missing experiment.

## CO2 and the 15% option

For the available **251-row ECFP4 snapshot (201 source / 50 outer)**, the original fixed step 0.01 and minimum subset 1 reproduce the archived 30/20/10% rules and outer metrics. The additional 25% and 15% runs are exploratory extensions requested after earlier results were visible.

| Top tier | Source-derived cutoff (Barrer) | Outer positives | Selected | TP | MCC |
|---|---:|---:|---:|---:|---:|
| 30% | 840 | 15 | 18 | 11 | 0.5092 |
| 25% | 1,360 | 14 | 9 | 5 | 0.2875 |
| 20% | 2,901.93 | 9 | 9 | 3 | 0.1870 |
| 15% | 4,100 | 9 | 7 | 2 | 0.1110 |
| 10% | 6,100 | 9 | 7 | 2 | 0.1110 |

The 15% rule has nonzero coverage. Its outer selected set happens to equal the 10% selected set; their target cutoffs and source selections differ. These small outer-positive counts limit generalization evidence. One unsuccessful tier would not establish that CO2 screening is impossible.

## Run an automatic custom case

Start from the linked public source or your own labeled table. For example, download the RadonPy CSV as `PI1070.csv`, keep its original `smiles` and `refractive_index` columns, and declare the target as computed and dimensionless. From the repository root, after setting `STCA_PY`, `SKILL_DIR` and `STCA_SOURCE` as in the main README:

```bash
"$STCA_PY" "$SKILL_DIR/scripts/auto_screen.py" \
  --input PI1070.csv --smiles-column smiles --target refractive_index \
  --unit dimensionless --data-kind computed --direction high \
  --tiers 0.10,0.15,0.20,0.25,0.30 --output-dir out/ri_auto
```

The automatic workflow:

1. Excludes unusable structures, unsupported H-cap connections and nonfinite targets, retaining the original fields, row mapping and reasons in `excluded_rows.csv` / `cleaning_audit.json`. An explicit stable ID only removes exact duplicate exports with the same nonempty ID **and complete original row**. Repeated measurements are not automatically averaged or deleted.
2. Creates ECFP4/t-SNE centroid-peripheral roles with a requested 20% outer fraction. Canonical original structures, H-cap identities and any declared groups are kept together, so the protected outer size may exceed 20%. The same procedure creates inner roles within source. These are new custom-data memberships, not the paper's exact split.
3. Chooses target transform and bounded scan resolution within source. Default nested selection compares minimum-subset settings within inner train/validation, then freezes the chosen recipe before evaluating the outer role. A broad positive target can use log10; an already-log input is declared with `--already-log` and its real input unit.
4. Reports every requested tier, physical cutoffs, rule failures and inner-validation eligibility. The strictest eligible requested tier is recommended; no eligible tier means no invented recommendation.

Use `--role-column Role` to preserve existing `source`/`holdout` roles; use `--source-value` / `--evaluation-value` for other labels. `--inner-role-column` can preserve predeclared source-internal `train`/`validation` roles. `--quality-column Quality --exclude-quality-value unusable` or declared `--target-min` / `--target-max` can apply documented data-contract filters. Do not set filters by searching for a better held-out score. Valid unusual values and condition differences remain visible rather than being removed using neighbour labels.

Preparation writes `input_format_audit.json`, `cleaned_input.csv`, `excluded_rows.csv`, `cleaning_audit.json`, `workflow_input.csv`, `split_membership.csv` and `split_audit.json`. Chosen source settings are in `fit/source_settings.json`; tier decisions are in `tier_recommendations.json`. A separate 72-record workflow check excluded one invalid SMILES and one missing target, retained 70 usable records and preserved the original input. This is a behavior check, not a generalization estimate.

The frozen model is `out/ri_auto/fit/model.json`; `run_manifest.json` and `automation_plan.json` record paths and settings. Apply a chosen fitted tier to independent candidates:

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --model out/ri_auto/fit/model.json --tier 0.15 \
  --input candidates.csv --smiles-column SMILES --output-dir out/ri_candidates15
```

Alternatively, add `--candidates candidates.csv` to the automatic command. It screens with the recommended inner-validation tier, or with an explicitly supplied fitted `--screen-tier`. With no eligible tier it retains diagnostics and does not invent a candidate screening result.

For a fully controlled recipe, use `custom_fit.py` with explicit roles and numerical settings, as shown in the [main guide](../../README.md#controlled-fitting-and-frozen-evaluation). `--scan-policy fixed` is an explicit alternative; fixed/source-only resubstitution supplies no independent inner-validation recommendation. If the nested split is unavailable, the program reports that failure rather than silently changing policies.

`candidates.csv` is your input; the evidence CSVs above contain aggregate results, not training observations. Exact reproduction of an archived score needs its exact cleaned input hash, roles, target scale and numerical settings. A fresh raw download followed by the automatic workflow is a new run, which must keep its own hashes and results. Automatic settings do not promise the same score or superiority over the baselines.

### Optional comparison on the same prepared rows

From the repository root, compare WRAcc and RF against a frozen STCA model on exactly its prepared rows and roles:

```bash
"$STCA_PY" tools/benchmark_cases.py \
  --input out/permeability_auto/fit/prepared_rows.csv \
  --model out/permeability_auto/fit/model.json --dataset my_case \
  --target-column stca_model_target --target-transform none \
  --role-column auto_role --source-role source --outer-role holdout \
  --output-dir out/same_rows_comparison
```

Replace paths and `auto_role` with your actual prepared input and role column. `stca_model_target` already contains the fitted model-scale values, so `--target-transform none` avoids transforming them again. The comparison retains the same requested tiers and source-derived cutoffs.

## Choose among tiers and combine targets

Predeclare a sequence such as **10%, 15%, 20%, 25%, 30%** when the application permits a range. Automatic eligibility uses the selected recipe's **source-internal validation**: a valid evaluation with nonzero coverage, positive MCC and precision above validation prevalence. It reports all tiers and recommends the smallest eligible fraction. If 10% fails these criteria, inspect 15% and the remaining requested choices; do not stop the whole task. The 20-positive support diagnostic is adjustable and does not prohibit fitting or screening.

Choose the main target before using outer results. A later expansion motivated by holdout results is exploratory and needs fresh independent confirmation. Moving from Top 10% to Top 20% changes the task; a fixed absolute application requirement remains fixed unless explicitly changed.

```text
Use STCA automatic custom-data mode on my computed RI table.
Predeclare Top 10%, 15%, 20%, 25% and 30%, use ECFP4 roles, clean unusable data with reasons,
and choose target scale, scan step and support inside source only.
Freeze every rule before outer evaluation. Report all outcomes and recommend the strictest
inner-validation-eligible tier; do not choose from outer performance.
```

Other valid tasks include high TC, low density, high isolated-monomer HOMO–LUMO gap or high CO2 permeability, each using its own labels, direction and units. **Low density is a new task**; archived high-density scores do not validate it. To combine targets, independently fit and freeze a high-TC model and a low-density model, then apply both to the same candidate table and return the structural intersection with every failed condition. Joint measured performance requires paired labels under comparable conditions; satisfying two rule sets alone does not establish it.
