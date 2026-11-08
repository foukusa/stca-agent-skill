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
Screen this PI1070.csv with the existing RadonPy high-density Top 30% STCA rule. Return selected records and every unmet condition.
```

The frozen condition is `K42=1`, with a density target boundary **≥ 1.222343047 g/cm³**. Applying it to all 1,077 structures gives **137 matches, 940 non-matches and no unknowns**. Keep the rule's frozen cutoff instead of recalculating it from candidates. Structural compliance is not a density measurement for a new proposal.

## Learn and check saved results

```text
Learn high-density rules from all rows of this RadonPy file. Use smiles for structures and density for the target, in g/cm³. Return screening results, compare them with the existing rule and save the new rules.
```

Default targets are Top 10%, 20% and 30%; other percentages are supported. The assistant selects transforms, scan steps and support settings, returns STCA and WRAcc separately and reports numerical cutoffs and recommendations.

Existing and newly learned rules should agree only when preparation, fingerprints, learning settings and versions agree. Adaptive relearning may produce different rules; retain both identities and explain any difference. Then check saving and loading:

```text
Reload the saved Top 30% STCA model, screen the same file again and check every row against its original screening result.
```

**The same saved model, tier and input must give identical row decisions.** Never merge distinct repeat-unit attachment positions to force agreement with an older rule. H-cap is used only for calculation copies.

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

[Five LLM proposals with row-level verification](generated_examples.csv) record one actual generation and calculation example. All five have two terminal attachment points, parse successfully and satisfy the frozen `K42=1` condition. See the [complete generation prompt](generation_prompt.zh-CN.md). Candidate density was not measured or predicted. A new generation request uses the current LLM instead of copying these static example rows.
