# Use STCA after installation

**Version 0.1.0** · [简体中文](USAGE.zh-CN.md) · [Home](../README.md) · [Install](INSTALL.md)

After installing and enabling STCA, upload your files and use these short requests. The skill loads the complete task prompts.

## Contents

- [Open the main menu](#open-the-main-menu)
- [Try the open-data examples](#try-the-open-data-examples)
- [1 Learn rules and receive screening results](#1-learn-rules-and-receive-screening-results)
- [2 Screen candidates with existing rules](#2-screen-candidates-with-existing-rules)
- [3 Choose rules before generating](#3-choose-rules-before-generating)
- [Get only the generation prompt](#get-only-the-generation-prompt)
- [Continue in another session or platform](#continue-in-another-session-or-platform)
- [Optional multi-objective screening](#optional-multi-objective-screening)

## Open the main menu

```text
Start STCA.
```

STCA offers:

1. Upload my data and learn rules.
2. Screen directly with existing rules.
3. Generate with existing rules.

Say **“Main menu”** or **“Back”** at any time. Saved rules are preserved. You can also state a complete task directly.

## Try the open-data examples

For an immediate screening trial, use the bundled [five-candidate CSV](../examples/quick_start/candidates.csv?raw=true), or ask:

```text
Use the bundled fluorinated-candidate example. Screen it with the RadonPy high-density Top 30% STCA rule and show every failed condition.
```

You receive three structural-rule matches and two non-matches, with the original star-containing SMILES and a reason for each failed condition.

To try learning, download the [GAS Dataset A CSV](https://github.com/jsunn-y/PolymerGasMembraneML/blob/30981d71e1e3f12a057e009cd79f119bc659c7f5/datasets/datasetA_imputed_all.csv), upload it and say:

```text
Learn high-CO₂-permeability rules from this measured data, in Barrer, for Top 10%, 20% and 30%. Automatically choose the data transform and scan step, return each tier's screening results and save the rules.
```

The assistant uses the original measured `CO2` column, rather than the Bayesian or Etree imputed columns. It returns the rules, automatically chosen settings and screening results, saves the rules and returns to the main menu. You can then ask “Use the saved Top 20% STCA rule to screen this new candidate table.”

## 1 Learn rules and receive screening results

Upload `materials.csv` with structures and numeric property values—for example, your computed thermal-conductivity data—and ask:

```text
1. Learn high thermal-conductivity rules from this computed data, in W/(m K).
```

STCA asks only for unclear scientific meaning or column names. With percentages omitted, it immediately uses Top **10%, 20% and 30%** for high values, or Bottom **10%, 20% and 30%** for low values. It compares STCA and WRAcc within your data range, returns both methods separately, marks a primary and alternative for every tier, saves the outputs and returns to the main menu.

You may specify any percentages strictly between 0% and 100%, or add “Save as My high TC.” For example:

```text
Learn high-CO₂-permeability rules from this measured data, in Barrer, using 15% and 25%. Return both methods’ results and each tier’s numeric threshold, and recommend a method automatically.
```

Every tier shows its numeric cutoff on the original physical scale, the ≥ comparison for high targets or ≤ for low targets, and the unit. Log-transformed learning still returns the physical cutoff.

The recommendation uses **AS = (MCC + Precision + F1) / 3**. When both methods can be evaluated, WRAcc is primary only when its CV AS exceeds STCA by **more than 0.02**; otherwise STCA remains primary. Both methods’ scores, separate selections and the recommendation reason are returned. Say “Use the recommendation” or “Choose the method automatically” to apply the primary without another method-confirmation step; an explicitly named method takes precedence.

You receive:

- Both STCA and WRAcc rules, scores, primary/alternative status and recommendation reason for every tier, with numeric physical cutoffs, comparison signs, units and reusable models.
- Each method’s row-level screening results at every tier: original SMILES, selection decisions, every failed condition and uncomputable records.
- Complete bilingual generation prompts, a friendly saved name and a downloadable rule bundle.
- The main menu, where your newly saved rules can be reused in tasks 2 and 3.

Tier-by-tier screening results always cover the original uploaded table. If you also upload a separate `candidates.csv`, its results are delivered separately; add:

```text
Apply every tier to the separate candidates.csv I uploaded and return its screening results.
```

A tier with fewer than 20 positives is marked as having insufficient evaluation support; rules can still be learned and saved. Unavailable rules or uncomputable tiers retain their status and reason.

If you supply source/holdout roles or request extrapolation testing, STCA uses the corresponding independent-holdout workflow, choosing settings within source only. Default in-range evaluation groups repeat-unit structures; its scores are conditional on the automatically preprocessed data.

## 2 Screen candidates with existing rules

Upload your candidates, or try the [structure-only example CSV](../examples/candidates.csv). It contains no measured property labels. You can also say “Use the bundled candidate example for a first screening trial” without creating a CSV yourself.

```text
2
```

STCA automatically lists bundled rules and saved personal rules, with their source, property, direction, percentages, method and primary/alternative status. Then say:

```text
Use the author-archived high-Tg Top 20% rule to screen my uploaded candidates.
```

Open-data rules are bundled at Top 10%, 20% and 30%. You could also choose “the primary GAS high-CO₂-permeability Top 10% rule.” Accepting the recommendation uses the marked primary directly; an explicitly chosen STCA or WRAcc method is respected. Each rule set screens independently. The selected tier includes its numeric physical cutoff, comparison and unit. A requested percentage absent from the frozen catalog requires labelled data to learn that tier; the assistant does not interpolate rules or substitute a nearby percentage.

If you completed the preceding example, you can instead say:

```text
Screen this candidate table with the rules just saved.
```

The results preserve all original SMILES and identifiers, report selections, failed conditions and unknown records, then return to the main menu. With the five bundled example structures and this author-archived high-Tg Top 20% rule, two match and three do not. This demonstrates structural-rule checking; the example has no property labels.

## 3 Choose rules before generating

```text
3
```

STCA automatically shows **bundled rules and loaded personal rules** first, including methods and primary/alternative status. Choose the source, property, percentage and rule to use, then select one of two modes. You can also choose your newly saved rules.

**Preview and confirm.** Ask:

```text
Use the author-archived high-Tg Top 20% rule. Show me the complete prompt before generating 20 candidates.
```

The complete prompt appears, and generation waits for your confirmation. Adjust it in ordinary language, for example:

```text
Change the count to 10, prefer structures containing ether linkages, and show the revised prompt.
```

When satisfied, say:

```text
Confirm and generate.
```

The current LLM then uses the approved prompt to generate candidates and verify them. You can change the count, structural preferences and output format; changing the target or frozen rule conditions requires selecting and confirming the corresponding rule.

**Generate directly.** Ask:

```text
Use the author-archived high-Tg Top 20% rule to generate 20 candidates directly and verify them.
```

The current LLM starts generation with the selected rules immediately. No additional LLM API setup is needed. If you have not specified a mode, STCA offers both choices after rule selection.

Both modes retain every original proposal, star-containing SMILES, rule decisions and failed conditions. The number generated and the number passing are reported separately; the task finishes by returning to the main menu.

## Get only the generation prompt

After choosing a rule, ask:

```text
Give me only the complete English generation prompt for this rule. Do not generate structures yet.
```

Copy it into another LLM. Upload that LLM's candidate table and say **“Verify these candidates with the same rule.”**

## Continue in another session or platform

Download the rule bundle returned earlier. Upload it in the new session and ask:

```text
Load this rule bundle, add it to My rules and show the main menu.
```

Choose task 2 or 3 to reuse it without retraining. Returning to the menu preserves saved rules; take the bundle when moving between devices.

## Optional multi-objective screening

Upload candidates and ask:

```text
Screen with both the author-archived high-Tg Top 20% and low-electrical-conductivity Bottom 10% rules.
Return each objective's decision, every failed condition and the candidates passing both.
```

Choose each objective's percentage independently. STCA checks structural rules; actual property success depends on the relevant validation results.
