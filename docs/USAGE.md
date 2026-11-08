# Use STCA after installation

**Version 0.1.0** · [简体中文](USAGE.zh-CN.md) · [Home](../README.md) · [Install](INSTALL.md)

STCA combines the skill's rules and calculation tools with your current LLM conversation. Upload a file and describe what you want; the assistant selects the tools and asks for any missing scientific information.

## Contents

- [Start a conversation](#start-a-conversation)
- [Try the open-data examples](#try-the-open-data-examples)
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

## Try the open-data examples

For a screening trial, use the bundled [five-candidate CSV](../examples/quick_start/candidates.csv?raw=true), or ask:

```text
Use the bundled fluorinated-candidate example. Screen it with the RadonPy high-density Top 30% STCA rule and show every unmet rule condition.
```

The supplied example has three structural-rule matches and two non-matches. Results preserve the original star-containing SMILES and identify each unmet condition.

To try learning, download the [RadonPy PI1070 CSV](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv), upload it and say:

```text
Learn high-density rules from this computed data in g/cm³. Automatically choose the data transform and scan step, return the screening results and save the rules.
```

The structure column is `smiles` and the density column is `density`. The assistant reports the chosen settings, both methods' rules and screening results, and the files saved. Continue with “Use the saved Top 30% STCA rule to screen this new candidate table.”

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

STCA and WRAcc are evaluated separately using cross-validation within the supplied data. Their recommendation uses the **average screening score** introduced in the [STCA paper](https://doi.org/10.1038/s41524-026-02345-x): the arithmetic mean of **Matthews correlation coefficient, precision and F1 score**. The software calls this Average Score (AS). When both methods are evaluable, WRAcc becomes the primary only if its cross-validation average screening score exceeds STCA's by more than 0.02; otherwise STCA remains primary. The assistant returns both methods' results and explains its recommendation. Say “Use the recommendation” or name either method.

You receive:

- Each tier's two methods, exact rules, evaluation scores, recommendation and reusable models.
- Row-level screening results for both methods: original identifiers and SMILES, selection decisions, unmet conditions and uncomputable records.
- Numeric physical cutoffs, comparison signs and units, plus complete English and Chinese generation prompts.
- Saved rule files, their actual location and a rule bundle for reuse.

The original uploaded table receives results for every requested tier. If you also upload a separate candidate table, add:

```text
Apply each tier to the separate candidates.csv I uploaded and return its screening results.
```

Limited evaluation support, unavailable rules and computation failures are reported with their own status. If you supply a source/holdout split or request extrapolation testing, settings are chosen within the source data before independent holdout evaluation.

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

Choose the source, property and percentage in the conversation. You may also use a saved rule.

**Preview and confirm:**

```text
Use the high-Tg Top 20% STCA-paper rule. Show me the complete prompt before generating 20 polymer repeat units.
```

The assistant shows the prompt and waits. Adjust it in ordinary language:

```text
Change the count to 10, prefer ether linkages, and show the revised prompt.
```

Then say **“Confirm and generate.”** The current LLM generates using the approved prompt, and STCA's calculation tools verify the proposals.

**Generate directly:**

```text
Use the high-Tg Top 20% STCA-paper rule to directly generate 20 polymer repeat units and verify them.
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
