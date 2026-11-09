# RadonPy density: screen, learn and generate

[简体中文](README.zh-CN.md) · [Home](../../README.md)

Use the same file to screen with existing rules, learn new rules and generate with a chosen rule. Download `PI1070.csv` from the [official RadonPy file page](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv), then upload it to the assistant.

## Rows and columns

The file contains **1,077 records and 157 columns**. Spreadsheet row 1 is the header and rows **2–1078** contain data. Use all records; no polymer-class filter is required.

| Role | Column | Spreadsheet position |
|---|---|---|
| Optional identifier | `monomer_ID` | A / column 1 |
| Polymer repeat unit | `smiles` | B / column 2 |
| Density target | `density` | AA / column 27, g/cm³ |

Labels come from molecular-dynamics calculations. `density_min`, `density_max`, `density_std` and `density_count` are statistics, not this task's target. Fingerprints use `smiles`; other property columns are not structure-rule features. Keep original fields and attachment points. The known-file mapping binds `smiles` to structures and `density` to the target; the assistant displays that binding and g/cm³ before learning. Manual cell selection is unnecessary. For a modified or unfamiliar file, ambiguous target columns are confirmed with you first; explicit column names in your request take precedence. Existing-rule screening itself needs no density labels.

Upload the original repeat-unit SMILES **with their `*` attachment points retained**. STCA keeps that original text and creates a separate calculation copy: supported terminal single-bond attachment atoms are capped with hydrogen (**H-cap**) before fingerprints are calculated. Results return the preserved original SMILES with the same `*` positions. This is not a text replacement or an attempt to infer attachment positions from the capped molecule. Already capped inputs remain as supplied; attachment points are not invented.

| Uploaded original | H-cap calculation copy | Returned structure |
|---|---|---|
| `*CCO*` | `CCO` | `*CCO*` |

## Screen with an existing rule

```text
Screen this PI1070.csv with the recommended existing RadonPy high-density Top 30% rule. Return selected records and every unmet condition.
```

The paired [Top 30% STCA rule](../../skills/stca/assets/rule_library/entries/current-pi-rho-stca-high-30/constraints.json) and [WRAcc rule](../../skills/stca/assets/rule_library/entries/current-pi-rho-wracc-high-30/constraints.json) retain separate exact conditions and a source-derived density boundary. The assistant reads the current recommendation, physical cutoff and actual screening counts from [the case configuration](case.json). You can explicitly select either available method. A match is a structural screening result; candidate density has not been measured or predicted.

## Learn and check saved results

```text
Learn high-density Top 30% rules from all rows of this RadonPy file. Use smiles for structures and density for the target, in g/cm³. Return screening results, compare them with the existing rule and save the new rules.
```

If you omit percentages, the defaults are Top 10%, 20% and 30%; other percentages are supported. Each requested percentage is prepared and fitted independently. The assistant reports the chosen transform, scan step and support, both methods, physical cutoffs and its recommendation.

The complete uploaded file is first split by ECFP4 structures. Each holdout record must be at nearest-source Tanimoto distance **at least 0.5**; buffer records remain available for screening but do not train or score the models. All preparation and automatic scan settings use source labels only, and source-inner Morgan validation determines the recommendation before the outer holdout is evaluated. The same file, package and split settings reproduce the corresponding bundled rules. Requesting 30% alone or with other percentages keeps that task unchanged. Distinct original attachment patterns remain separate even when H-cap copies coincide. Check saving and loading:

```text
Reload the saved recommended Top 30% model, screen the same file again and check every row against its original screening result.
```

**The same saved model, tier and input must give identical row decisions.** H-cap is used only for calculation copies; output keeps every original field and attachment point.

## Generate with the selected rule

Generate directly:

```text
Use the selected high-density Top 30% rule to directly generate and verify five polymer repeat units.
```

Preview and adjust first:

```text
Use the existing RadonPy high-density Top 30% STCA rule. Show the complete prompt for five repeat units first.
```

Adjust the count, structural preferences or output requirements, then say “Confirm and generate.” The current LLM generates proposals; the calculation checks the selected exact rule. Retain every proposal, passing results and unmet conditions. Mark proposals pending if calculation cannot run.

The [machine-readable case](case.json) records the file, columns and consistency checks for the assistant.

## A computed generation example

[LLM proposals with row-level verification](generated_examples.csv) illustrate how proposals and each unmet condition are returned. Use the exact rule identified by the linked [generation prompt](generation_prompt.en.md) when checking those saved proposals. To test a different or newly learned rule, ask the assistant to verify them again with that rule. Candidate density is not measured or predicted by structural verification; a new generation request uses the current LLM to produce its own proposals.
