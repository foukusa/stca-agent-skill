# ADEPT gap: screen, learn and generate

[简体中文](README.zh-CN.md) · [Home](../../README.md)

Use one public dataset to try STCA's three workflows: apply a saved rule, learn and save rules, and ask the current LLM to generate repeat units with a chosen rule. This example explicitly selects **STCA, high gap, Top30%**.

## Contents

- [Data and columns](#data-and-columns)
- [Screen with an existing rule](#screen-with-an-existing-rule)
- [Learn rules from the data](#learn-rules-from-the-data)
- [Generate with the rule](#generate-with-the-rule)
- [Results and source](#results-and-source)

## Data and columns

Open the [ADEPT data file](https://github.com/sobinalosious/PolyGraphMT/blob/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw/BANDGAP_DFT.csv), click **Download raw file** to save `BANDGAP_DFT.csv`, and attach it in a conversation with STCA installed. It contains **2,916 records and 2 columns**: row 1 is the header and rows 2–2917 contain data.

| Role | Original column | Position |
|---|---|---|
| Polymer repeat unit | `SMILES` | A, column 1 |
| Computed gap | `BANDGAP` | B, column 2, eV |

The label is the **DFT HOMO–LUMO gap of a hydrogen-capped isolated monomer**, not a bulk-polymer band gap. Retain any original `*` attachment atoms. H-cap is a separate calculation copy; results return the original repeat unit.

## Screen with an existing rule

Attach the file and say:

```text
Screen this dataset with the ADEPT high isolated-monomer HOMO–LUMO gap Top30% STCA rule. Return selected records and every unmet rule condition.
```

The chosen rule targets **gap ≥11.914537535 eV**. Applied to the fixed file above, STCA matches **976 records**, with 1,940 unmatched and 0 unknown. Top30% defines the property target; it does not require 30% of candidates to match. Applying the rule to a candidate file needs only its structure column.

[Exact STCA conditions](../../skills/stca/assets/rule_library/entries/current-ad-gap-stca-high-30/constraints.json) · [Complete generation prompt](generation_prompt.en.md)

## Learn rules from the data

```text
Learn high isolated-monomer HOMO–LUMO gap Top30% rules from this ADEPT dataset. Use SMILES for structures and BANDGAP for the target, in eV, and include all rows. Return screening results, compare them with the existing rules and save the new rules.
```

The assistant splits structures first, then selects the transform, scan step and support using training data only. It returns separate rules, numeric cutoffs, complete screening tables and extrapolation scores for both methods, and saves reusable rule bundles. The same file and default settings reproduce the corresponding bundled rules.

Learning returns **both STCA and WRAcc**; training-side validation determines the recommendation. To continue this STCA example, say:

```text
Choose the saved Top30% STCA rule. Reload it, screen the same dataset again and check that every row agrees.
```

## Generate with the rule

Generate directly:

```text
Use the selected ADEPT high-gap Top30% STCA rule to directly generate and verify five polymer repeat units.
```

Preview and adjust first:

```text
Use the same STCA rule. Show the complete prompt for five repeat units first, without generating yet.
```

After adjusting the count or structural preferences, say “Confirm and generate.” The current LLM proposes candidates, and the calculation checks the frozen conditions. All proposals, original attachment atoms and unmet conditions are retained.

[Five proposals and their verification](generated_examples.csv) · [Verification record](generation_verification.json) · [Complete prompt used for this example](generation_prompt.used.zh-CN.md)

## Results and source

On 584 independent heldout records, STCA selects 192, including 144 that meet the target. Every heldout structure is at nearest-training ECFP4 Tanimoto distance **at least 0.5** from the actual training structures.

| Method | Precision | Recall | F1 | Matthews correlation coefficient |
|---|---:|---:|---:|---:|
| STCA |0.7500|0.7784|0.7639|0.6517|
| WRAcc |0.8241|0.8865|0.8542|0.7840|

Whole-file screening matches 976 records with STCA and 1,019 with WRAcc, with no unknowns. The complete input includes training and buffer records; independent extrapolation scores use the 584 heldout records only. See [evaluation.csv](evaluation.csv) for all three tiers and both methods, and [data splitting and evaluation](../../docs/MORGAN_EVALUATION.md) for the protocol. Structural rule verification does not predict a new candidate's numerical gap.

Source: [ADEPT data distributed with PolyGraphMT](https://github.com/sobinalosious/PolyGraphMT/tree/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw) · [ADEPT study](https://doi.org/10.1039/D6DD00206D). Cite the original source. Download the raw CSV from its source page. The [machine-readable case](case.json) records column bindings, rules and expected results.
