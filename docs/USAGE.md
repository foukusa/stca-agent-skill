# Use STCA after installation

**Version 0.1.0** · [简体中文](USAGE.zh-CN.md) · [Home](../README.md) · [Install](INSTALL.md)

STCA combines the skill's rules and calculation tools with your current LLM conversation. Upload a file and describe what you want; the assistant selects the tools and asks for any missing scientific information.

## Contents

- [Start a conversation](#start-a-conversation)
- [Bind columns and preserve attachment points](#bind-columns-and-preserve-attachment-points)
- [Try ADEPT monomer gap](#try-adept-monomer-gap)
- [Learn rules and receive screening results](#learn-rules-and-receive-screening-results)
- [Screen candidates with existing rules](#screen-candidates-with-existing-rules)
- [Choose rules before generating](#choose-rules-before-generating)
- [Get only the generation prompt](#get-only-the-generation-prompt)
- [Continue in another session or platform](#continue-in-another-session-or-platform)
- [Optional multi-objective screening](#optional-multi-objective-screening)

## Start a conversation

```text
Start STCA.
```

The assistant can explain three workflows: learn from uploaded data, screen with existing rules, or generate with selected rules. You can state a complete task immediately and continue with requests such as “Use the rules just saved” or “Show other available rules.”

## Bind columns and preserve attachment points

Learning requires an explicitly bound **structure column, numeric property column and unit**. You can name them in your request. For a recognized source such as the ADEPT data below, the mapping is already supplied; otherwise the assistant reads the headers and displays the columns, target meaning and unit it will use before learning. If more than one column could mean the target—such as measured versus calculated density, different temperatures, or a mean versus a minimum/maximum—it asks you to choose first. Your explicit column names take precedence. Numeric ranges alone do not establish a column's meaning. Screening with an existing rule needs the structure column, without property labels for the candidates.

Upload the original repeat-unit SMILES **with their `*` attachment points retained**. STCA keeps that original text and creates a separate calculation copy: supported terminal single-bond attachment atoms are capped with hydrogen (**H-cap**) before fingerprints are calculated. Results return the preserved original SMILES with the same `*` positions. This is not a text replacement or an attempt to infer attachment positions from the capped molecule. Already capped inputs remain as supplied; attachment points are not invented.

| Uploaded original | H-cap calculation copy | Returned structure |
|---|---|---|
| `*CCO*` | `CCO` | `*CCO*` |

## Try ADEPT monomer gap

Use the same [ADEPT `BANDGAP_DFT.csv`](https://github.com/sobinalosious/PolyGraphMT/blob/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw/BANDGAP_DFT.csv) for screening, learning and generation. Download the CSV from its source file page and upload it to the conversation.

| Use | Column | Position |
|---|---|---|
| Polymer repeat-unit structure | `SMILES` | A · column 1 |
| DFT monomer gap, eV | `BANDGAP` | B · column 2 |

The file has 2,916 data rows and 2 columns: row 1 is the header and rows 2–2917 are data. The target is the **HOMO–LUMO gap of a hydrogen-capped isolated monomer**, rather than a bulk-polymer bandgap. This example explicitly chooses STCA.

**Apply an existing rule:**

```text
Use the existing ADEPT high-monomer-gap Top 30% STCA rule to screen this dataset.
```

For this fixed file, the target boundary is **≥11.914537535 eV**; STCA matches 976 records, with 0 unknown. Its 584 labeled distance-holdout records give precision 0.7500, recall 0.7784, F1 0.7639 and MCC 0.6517. Original-table matches and independent extrapolation performance are reported separately.

**Learn from the same file and return its screening results:**

```text
Learn high-monomer-gap Top 30% rules from all rows of this ADEPT file. Use SMILES for structures and BANDGAP for the target, in eV. Return both methods and screening results, compare with the existing rules and save the rules.
```

The assistant splits structures first, then selects transformations, scan step and support within source, learns STCA and WRAcc and saves both. Subsequent requests in this example explicitly use STCA. The catalog's automatic recommendation still follows training-side validation.

```text
Reload the Top 30% STCA rule just saved and screen the same ADEPT file again. Check that every row matches its earlier decision.
```

Reloading applies the saved model without retraining. See the [complete ADEPT monomer-gap case](../examples/adept_gap/README.md). [RadonPy density](../examples/radonpy_density/README.md) remains an optional task.

## Learn rules and receive screening results

Upload `materials.csv` with polymer structures and numeric property values, then ask:

```text
Learn high thermal-conductivity rules from this computed data, in W/(m K). Return the screening results and save the rules.
```

STCA asks about unclear column meanings, units or targets. If percentages are omitted, high targets use Top **10%, 20% and 30%**, and low targets use Bottom **10%, 20% and 30%**. You may choose any percentages strictly between 0% and 100%:

```text
Learn high-density rules from this computed data in g/cm³, using Top 15% and 25%. Return both methods' results and numeric thresholds, recommend a method, and save as high-density rules.
```

Each tier reports the cutoff on the original physical scale, its comparison sign (≥ for high targets, ≤ for low targets) and unit. Log-transformed learning still returns physical cutoffs.

New learning uses **strict Morgan-distance extrapolation**: ECFP4 fingerprints, with every holdout structure at nearest-neighbour Tanimoto distance **at least 0.5** from source. Structures are split before label-dependent preparation; any buffer records are reported. A further Morgan-distance validation within source compares STCA and WRAcc and fixes the recommendation before the outer holdout is evaluated. See [how evaluation works](MORGAN_EVALUATION.md).

The **average screening score** introduced in the [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) is the arithmetic mean of **Matthews correlation coefficient, precision and F1 score**. When both methods have usable source-validation evidence, WRAcc becomes primary only if its score exceeds STCA's by more than 0.02; otherwise STCA remains primary. The assistant returns both methods and explains its recommendation. Say “Use the recommendation” or name either method.

WRAcc automatically selects a maximum condition count from **1, 2, 3, 5, 10 and no length limit**, separately for each target tier. This selection uses only the relevant training data; the outer holdout never selects rule length. The chosen setting and actual condition count are saved with the rule. If there is insufficient evidence to choose a length, the report states this rather than presenting the fallback as validated.

You may override the length policy in ordinary language:

```text
Learn these rules with at most 10 WRAcc conditions.
```

```text
Learn these rules without a WRAcc condition-count limit.
```

“No length limit” removes the condition-count ceiling; WRAcc still uses a beam of 30 conjunctions and a minimum selected support of 5. More conditions do not necessarily improve validation performance. STCA also has a defined search scope: up to 10 ranked positive and 10 ranked negative MACCS conditions, with 8 candidates retained per family. Neither search enumerates every possible rule. Existing frozen rules keep their saved conditions; these settings apply when learning new rules.

You receive:

- Each tier's two method results and availability, with exact rules, evaluation scores, recommendations and reusable models where available.
- Row-level screening results for both methods: original identifiers and SMILES, selection decisions, unmet conditions and uncomputable records.
- Numeric physical cutoffs, comparison signs and units, plus complete English and Chinese generation prompts.
- Saved rule files, their actual location and a rule bundle for reuse.

The original uploaded table receives results for every requested tier. If you also upload a separate candidate table, add:

```text
Apply each tier to the separate candidates.csv I uploaded and return its screening results.
```

The assistant reports unavailable distance splits, insufficient evaluation support, missing rules and computation failures explicitly. It does not silently switch to a random split. If you provide an existing source/holdout protocol, it preserves that choice and names the actual evaluation method.

## Screen candidates with existing rules

Upload candidates and ask:

```text
Show the available high-Tg rules from the STCA paper, then help me select one for screening this table.
```

The assistant shows relevant rules with their source, property, direction, percentage, numeric cutoff and method. If you already know the target, ask directly:

```text
Use the high-Tg Top 20% STCA-paper rule to screen my uploaded candidates.
```

Or reuse a result from the same conversation:

```text
Screen this candidate table with the Top 30% STCA rule just saved.
```

The result includes original SMILES and identifiers, selected records, unmet conditions and records that could not be evaluated. Each method and tier is applied separately. A percentage absent from a frozen catalog requires labelled data to learn a new rule; existing rules are not interpolated.

## Choose rules before generating

If no rule is selected, start with:

```text
I want to generate polymer repeat units. Show the available rules first.
```

Choose the source, property and percentage in the conversation. For the ADEPT case, continue with the existing high-monomer-gap Top 30% STCA rule or the STCA rule just saved.

**Preview and confirm:**

```text
Use the high-monomer-gap Top 30% STCA rule just saved. Show the complete prompt for five polymer repeat units before generating.
```

The assistant shows the prompt and waits. Adjust it in ordinary language:

```text
Keep five candidates, increase structural diversity, and show the revised prompt.
```

Then say **“Confirm and generate.”** The current LLM generates using the approved prompt, and STCA's calculation tools verify the proposals.

**Generate directly:**

```text
Use the high-monomer-gap Top 30% STCA rule just saved to directly generate and verify five polymer repeat units.
```

This uses the current conversation's LLM without separate model API setup for STCA. Counts, structural preferences and output formats can be changed; changing the target or frozen conditions requires choosing the corresponding rule.

Both modes retain the original proposals and final prompt. Generation count and verified rule-pass count are reported separately. If RDKit or another computation dependency cannot run, proposals are marked **unverified**, with the environment error. An unavailable checker does not establish that SMILES are invalid or that zero candidates match. Structural-rule matches are also distinct from measured property performance.

## Get only the generation prompt

```text
Give me only the complete English generation prompt for this rule. Do not generate structures yet.
```

Copy it into another LLM. Upload that LLM's candidate table and say **“Verify these candidates with the same rule.”**

## Continue in another session or platform

In the same conversation, say “Use the rules just saved” and specify screening or generation. The assistant reads the saved files and continues the requested task.

Download the rule bundle before leaving a temporary session. Upload it in the new session and ask:

```text
Load this rule bundle and use its Top 30% STCA rule to screen these candidates.
```

No retraining is required. Files remain available according to the platform's storage; a temporary conversation alone does not guarantee cross-session persistence.

## Optional multi-objective screening

```text
Screen with both the high-Tg Top 20% and low-electrical-conductivity Bottom 10% STCA-paper rules. Return each objective's decision, unmet conditions and the candidates passing both.
```

Choose each objective's percentage independently. STCA checks structural conditions; property performance is assessed using the relevant validation data.
