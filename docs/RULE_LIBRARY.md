# STCA rules and generation prompts

**Version 0.1.0** · [简体中文](RULE_LIBRARY.zh-CN.md) · [Home](../README.md)

Say **“Start STCA”** and ask to screen or generate with the chosen rules to open the catalog automatically. Select a source, property, percentage and rule; the AI assistant loads every condition. You do not need rule IDs. Click a method below to get its complete English generation prompt directly.

## Contents

- [How to choose](#how-to-choose)
- [STCA paper rules](#stca-paper-rules)
- [GAS: measured gas permeability](#gas-measured-gas-permeability)
- [RadonPy: five computed properties](#radonpy-five-computed-properties)
- [ADEPT: five computed properties](#adept-five-computed-properties)
- [Use your own data](#use-your-own-data)

## How to choose

Bundled rules and scores retain the settings used to create them. New learning selects the WRAcc condition-count limit inside the training partition by default; a fixed limit or no limit can also be requested. This does not rewrite bundled rules or their catalog scores.

The open-data catalog covers **12 tasks**, all in the high-value direction at Top **10%, 20% and 30%**. Each tier offers complete **STCA and WRAcc** rules, marked primary and alternative. Accept the recommendation to use the primary directly, or explicitly choose either method. The methods have separate rules and screening results; a comparison returns both.

For example: “Screen this table with the primary GAS high-CO₂-permeability Top 10% rule,” or “Generate 20 candidates directly with the ADEPT high-dielectric-constant Top 20% WRAcc rule.”

For generation, choose **Preview and confirm** or **Generate directly** after selecting the rule. Preview mode displays the complete prompt for your edits and waits for “Confirm and generate”; direct mode invokes the current LLM immediately. Both generate actual candidates and verify every proposal against the selected rules. Ask for “the complete prompt only” if you want to use another LLM instead.

Each selected tier and complete prompt includes the **numeric physical cutoff, ≥/≤ comparison, unit** and all structural conditions. Percentages describe the target range in the original data, rather than a quota for selected candidates. Screening preserves original SMILES and returns decisions and every unmet rule condition. For multiple objectives, select a rule for each and report candidates satisfying all of them.

AS (Average Score) is introduced and defined in the [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) and validated through its polymer-screening evaluations. This skill uses the same arithmetic mean of Matthews correlation coefficient (MCC), precision and F1 score.

The primary is chosen using in-range, structure-grouped 5-fold evaluation repeated 3 times. **AS = (MCC + Precision + F1) / 3**; when both methods can be evaluated, WRAcc is primary only when its AS exceeds STCA by **more than 0.02**, otherwise STCA is retained. Each tier reports both methods’ scores and the recommendation reason. Scores are conditional on the automatically preprocessed data. Screening the original table shows the frozen rule’s selections within that table.

## STCA paper rules

These frozen Tg and electrical-conductivity rules implement the structural screening and generation tasks presented in the author’s [STCA paper](https://doi.org/10.1038/s41524-026-02345-x). Select a property and percentage below to use the complete rule-guided prompt.

| Property and direction | Unit | Complete prompts |
|---|---|---|
| High Tg | °C | [Top 10%](../skills/stca/assets/rule_library/entries/paper-tg-high-10/prompt.en.md) · [Top 20%](../skills/stca/assets/rule_library/entries/paper-tg-high-20/prompt.en.md) · [Top 30%](../skills/stca/assets/rule_library/entries/paper-tg-high-30/prompt.en.md) |
| Low electrical conductivity | S/cm | [Bottom 5%](../skills/stca/assets/rule_library/entries/paper-ec-low-5/prompt.en.md) · [Bottom 10%](../skills/stca/assets/rule_library/entries/paper-ec-low-10/prompt.en.md) · [Bottom 15%](../skills/stca/assets/rule_library/entries/paper-ec-low-15/prompt.en.md) · [Bottom 20%](../skills/stca/assets/rule_library/entries/paper-ec-low-20/prompt.en.md) |
| High electrical conductivity | S/cm | [Top 5%](../skills/stca/assets/rule_library/entries/paper-ec-high-5/prompt.en.md) · [Top 10%](../skills/stca/assets/rule_library/entries/paper-ec-high-10/prompt.en.md) · [Top 15%](../skills/stca/assets/rule_library/entries/paper-ec-high-15/prompt.en.md) · [Top 20%](../skills/stca/assets/rule_library/entries/paper-ec-high-20/prompt.en.md) |

## GAS: measured gas permeability

Source: [PolymerGasMembraneML Dataset A](https://github.com/jsunn-y/PolymerGasMembraneML), associated with the [gas-permeability study](https://doi.org/10.1126/sciadv.abn9545). CO₂ and O₂ labels are experimental measurements. STCA has been applied to these data for rule extraction and screening validation.

| Property | Unit | Top 10% | Top 20% | Top 30% |
|---|---|---|---|---|
| CO2 permeability | Barrer | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-gas-co2-stca-high-10/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-gas-co2-wracc-high-10/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-gas-co2-stca-high-20/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-gas-co2-wracc-high-20/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-gas-co2-stca-high-30/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-gas-co2-wracc-high-30/prompt.en.md) |
| O2 permeability | Barrer | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-gas-o2-stca-high-10/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-gas-o2-wracc-high-10/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-gas-o2-stca-high-20/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-gas-o2-wracc-high-20/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-gas-o2-stca-high-30/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-gas-o2-wracc-high-30/prompt.en.md) |

## RadonPy: five computed properties

Source: [RadonPy PI1070](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv), associated with the [RadonPy study](https://doi.org/10.1038/s41524-022-00906-4). These labels come from polymer molecular-dynamics calculations and have been used with STCA for rule extraction and screening validation.

| Property | Unit | Top 10% | Top 20% | Top 30% |
|---|---|---|---|---|
| Thermal conductivity | W/(m K) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-pi-tc-stca-high-10/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-tc-wracc-high-10/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-pi-tc-stca-high-20/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-tc-wracc-high-20/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-pi-tc-stca-high-30/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-tc-wracc-high-30/prompt.en.md) |
| Refractive index | dimensionless | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-ri-wracc-high-10/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-ri-stca-high-10/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-ri-wracc-high-20/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-ri-stca-high-20/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-ri-wracc-high-30/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-ri-stca-high-30/prompt.en.md) |
| Density | g/cm³ | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-rho-wracc-high-10/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-rho-stca-high-10/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-pi-rho-stca-high-20/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-rho-wracc-high-20/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-rho-wracc-high-30/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-rho-stca-high-30/prompt.en.md) |
| Specific heat | J/(kg K) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-pi-cp-stca-high-10/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-cp-wracc-high-10/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-cp-wracc-high-20/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-cp-stca-high-20/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-cp-wracc-high-30/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-cp-stca-high-30/prompt.en.md) |
| Dielectric constant | dimensionless | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-dc-wracc-high-10/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-dc-stca-high-10/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-dc-wracc-high-20/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-dc-stca-high-20/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-pi-dc-wracc-high-30/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-pi-dc-stca-high-30/prompt.en.md) |

## ADEPT: five computed properties

Source: [ADEPT data distributed with PolyGraphMT](https://github.com/sobinalosious/PolyGraphMT/tree/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw), associated with the [ADEPT study](https://doi.org/10.1039/D6DD00206D). These MD/DFT property tasks have been used with STCA for rule extraction and screening validation. The gap is the HOMO–LUMO gap of a hydrogen-capped isolated monomer.

| Property | Unit | Top 10% | Top 20% | Top 30% |
|---|---|---|---|---|
| Thermal conductivity | W/(m K) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-tc-wracc-high-10/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-tc-stca-high-10/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-tc-wracc-high-20/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-tc-stca-high-20/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-tc-wracc-high-30/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-tc-stca-high-30/prompt.en.md) |
| Density | g/cm³ | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-ad-rho-stca-high-10/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-rho-wracc-high-10/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-ad-rho-stca-high-20/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-rho-wracc-high-20/prompt.en.md) | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-ad-rho-stca-high-30/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-rho-wracc-high-30/prompt.en.md) |
| Isolated-monomer HOMO-LUMO gap | eV | Primary [STCA](../skills/stca/assets/rule_library/entries/latest-ad-gap-stca-high-10/prompt.en.md) · Alternative [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-gap-wracc-high-10/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-gap-wracc-high-20/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-gap-stca-high-20/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-gap-wracc-high-30/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-gap-stca-high-30/prompt.en.md) |
| Dielectric constant | dimensionless | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-dc-wracc-high-10/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-dc-stca-high-10/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-dc-wracc-high-20/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-dc-stca-high-20/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-dc-wracc-high-30/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-dc-stca-high-30/prompt.en.md) |
| Refractive index | dimensionless | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-ri-wracc-high-10/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-ri-stca-high-10/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-ri-wracc-high-20/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-ri-stca-high-20/prompt.en.md) | Primary [WRAcc](../skills/stca/assets/rule_library/entries/latest-ad-ri-wracc-high-30/prompt.en.md) · Alternative [STCA](../skills/stca/assets/rule_library/entries/latest-ad-ri-stca-high-30/prompt.en.md) |

## Use your own data

To use a percentage absent from the frozen catalog, a new direction such as low density, or your own data conditions, ask the assistant to learn rules from your uploaded data. You may request any percentages strictly between 0% and 100%, such as 15% and 25%. With none specified, learning immediately uses Top or Bottom **10%, 20% and 30%**. A missing frozen tier is never interpolated or replaced by a nearby tier. The AI assistant learns both methods, returns separate original-table screening results and numeric physical cutoffs with comparison signs and units for every tier, marks the primary and explains why, saves complete rules, models and bilingual prompts and reports their actual file locations. Continue by asking to screen or generate with the saved rules; upload the portable rule bundle when starting a new session.

See the [natural-language examples](USAGE.md) and [open-data applications](../examples/open_data/README.md). Rule versions, exact conditions and method information are stored in the [machine-readable catalog](../skills/stca/assets/rule_library/catalog.json).
