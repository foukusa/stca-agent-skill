# STCA ready-made rules and generation prompts

**Version 0.1.0** · [简体中文](RULE_LIBRARY.zh-CN.md) · [Home](../README.md) · [Machine-readable catalog](../skills/stca/assets/rule_library/catalog.json)

Choose an existing rule by data source, property, direction and percentage. This directory offers 77 frozen rule choices, each with a complete English generation prompt to copy and an exact constraints JSON file.

## Contents

- [Choose and invoke a rule](#choose-and-invoke-a-rule)
- [STCA paper: high Tg, high and low electrical conductivity](#stca-paper-high-tg-high-and-low-electrical-conductivity)
- [GAS: measured gas permeability](#gas-measured-gas-permeability)
- [RadonPy: five computed properties](#radonpy-five-computed-properties)
- [ADEPT: six computed properties](#adept-six-computed-properties)
- [AD_GAP: author default and more options](#ad_gap-author-default-and-more-options)

## Choose and invoke a rule

1. Choose the data source and property, then the high/low direction and percentage. Each percentage link opens the complete English prompt for that rule; its adjacent JSON link opens the exact constraints.
2. Copy the whole prompt into the current LLM or another LLM. Add your candidate count, chemical preferences and exclusions while keeping the rule ID, bit conditions and AND relationships intact.
3. To screen existing candidates or check generated structures, upload a CSV in a host with STCA enabled and name the selected rule ID. The ID appears under “rule source” in the prompt and is also its directory name.

For example, after choosing GAS high-CO₂-permeability Top 15%, ask:

```text
Use STCA's ready-made rule gas-co2-high-15 to screen my uploaded candidates.csv.
The structure column is SMILES; CandidateKey is an optional identifier.
Keep the original star-containing repeat units and return every candidate's
rule decision and all failed conditions.
```

For multiple goals, specify a separate ID for each, such as `paper-tg-high-20` and `paper-ec-low-10`, and require every rule to hold for the same candidate.

Top/Bottom percentages describe the target tail of the source dataset; they do not prescribe the fraction of new or generated candidates that pass. A physical cutoff in a prompt is the frozen training-label boundary. Confirm property values through measurement or calculation; matching structural rules alone does not establish them. Keep the source and unit when choosing between datasets for the same property.

## STCA paper: high Tg, high and low electrical conductivity

These choices use the STCA paper's frozen rules. Tg has a high-value direction; electrical conductivity (EC) has separate high- and low-value directions.

| Property and direction | Unit | Available percentages: open English prompt / constraints |
|---|---|---|
| High glass-transition temperature (Tg) | degC | [Top 10%](../skills/stca/assets/rule_library/entries/paper-tg-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-tg-high-10/constraints.json); [Top 20%](../skills/stca/assets/rule_library/entries/paper-tg-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-tg-high-20/constraints.json); [Top 30%](../skills/stca/assets/rule_library/entries/paper-tg-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-tg-high-30/constraints.json) |
| High electrical conductivity (EC) | S/cm | [Top 5%](../skills/stca/assets/rule_library/entries/paper-ec-high-5/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-ec-high-5/constraints.json); [Top 10%](../skills/stca/assets/rule_library/entries/paper-ec-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-ec-high-10/constraints.json); [Top 15%](../skills/stca/assets/rule_library/entries/paper-ec-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-ec-high-15/constraints.json); [Top 20%](../skills/stca/assets/rule_library/entries/paper-ec-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-ec-high-20/constraints.json) |
| Low electrical conductivity (EC) | S/cm | [Bottom 5%](../skills/stca/assets/rule_library/entries/paper-ec-low-5/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-ec-low-5/constraints.json); [Bottom 10%](../skills/stca/assets/rule_library/entries/paper-ec-low-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-ec-low-10/constraints.json); [Bottom 15%](../skills/stca/assets/rule_library/entries/paper-ec-low-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-ec-low-15/constraints.json); [Bottom 20%](../skills/stca/assets/rule_library/entries/paper-ec-low-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/paper-ec-low-20/constraints.json) |

## GAS: measured gas permeability

GAS supplies rules from measured CO₂ and O₂ permeability. Both use the high direction, with Top 10%, 15%, 20%, 25% and 30% choices.

| Dataset | Property | Unit | Top 10% | Top 15% | Top 20% | Top 25% | Top 30% |
|---|---|---|---|---|---|---|---|
| `GAS_CO2` | CO2 permeability | Barrer | [10%](../skills/stca/assets/rule_library/entries/gas-co2-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/gas-co2-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/gas-co2-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/gas-co2-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/gas-co2-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-co2-high-30/constraints.json) |
| `GAS_O2` | O2 permeability | Barrer | [10%](../skills/stca/assets/rule_library/entries/gas-o2-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/gas-o2-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/gas-o2-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/gas-o2-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/gas-o2-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/gas-o2-high-30/constraints.json) |

## RadonPy: five computed properties

The RadonPy data supplies five computed properties: thermal conductivity, refractive index, density, specific heat and dielectric constant. All choices below use the high direction. `dimensionless` denotes a unitless property.

| Dataset | Property | Unit | Top 10% | Top 15% | Top 20% | Top 25% | Top 30% |
|---|---|---|---|---|---|---|---|
| `PI_TC` | Thermal conductivity | W/(m K) | [10%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-tc-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-tc-high-30/constraints.json) |
| `PI_RI` | Refractive index | dimensionless | [10%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-ri-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-ri-high-30/constraints.json) |
| `PI_RHO` | Density | g/cm3 | [10%](../skills/stca/assets/rule_library/entries/radonpy-density-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-density-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-density-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-density-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-density-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-density-high-30/constraints.json) |
| `PI_CP` | Specific heat | J/(kg K) | [10%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-cp-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-cp-high-30/constraints.json) |
| `PI_DC` | Dielectric constant | dimensionless | [10%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/radonpy-dc-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/radonpy-dc-high-30/constraints.json) |

## ADEPT: six computed properties

The ADEPT data supplies six computed properties: thermal conductivity, density, isolated-monomer HOMO–LUMO gap, dielectric constant, refractive index and glass-transition temperature. The five properties below each offer high-value Top 10%, 15%, 20%, 25% and 30% rules. Gap choices have their own section next. Unit `1` denotes a unitless property.

| Dataset | Property | Unit | Top 10% | Top 15% | Top 20% | Top 25% | Top 30% |
|---|---|---|---|---|---|---|---|
| `AD_TC` | Thermal conductivity | W/(m K) | [10%](../skills/stca/assets/rule_library/entries/adept-tc-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-tc-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-tc-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-tc-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-tc-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tc-high-30/constraints.json) |
| `AD_RHO` | Density | g/cm3 | [10%](../skills/stca/assets/rule_library/entries/adept-density-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-density-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-density-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-density-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-density-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-density-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-density-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-density-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-density-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-density-high-30/constraints.json) |
| `AD_DC` | Dielectric constant | 1 | [10%](../skills/stca/assets/rule_library/entries/adept-dc-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-dc-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-dc-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-dc-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-dc-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-dc-high-30/constraints.json) |
| `AD_RI` | Refractive index | 1 | [10%](../skills/stca/assets/rule_library/entries/adept-ri-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-ri-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-ri-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-ri-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-ri-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-ri-high-30/constraints.json) |
| `AD_TG` | Glass-transition temperature | K | [10%](../skills/stca/assets/rule_library/entries/adept-tg-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-10/constraints.json) | [15%](../skills/stca/assets/rule_library/entries/adept-tg-high-15/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-15/constraints.json) | [20%](../skills/stca/assets/rule_library/entries/adept-tg-high-20/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-20/constraints.json) | [25%](../skills/stca/assets/rule_library/entries/adept-tg-high-25/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-25/constraints.json) | [30%](../skills/stca/assets/rule_library/entries/adept-tg-high-30/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-tg-high-30/constraints.json) |

## AD_GAP: author default and more options

The `AD_GAP` target is the **isolated-monomer HOMO–LUMO gap**, in eV. For Top 10%, use the author-supplied frozen representative `adept-gap-author-high-10` by default. Top 15%, 20%, 25% and 30% each use their own dataset rule.

| Option | Percentage | English prompt | Exact constraints |
|---|---|---|---|
| Author-supplied frozen representative (default) | Top 10% | [Copy prompt](../skills/stca/assets/rule_library/entries/adept-gap-author-high-10/prompt.en.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-author-high-10/constraints.json) |
| Dataset rule | Top 15% | [Copy prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-15/prompt.en.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-15/constraints.json) |
| Dataset rule | Top 20% | [Copy prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-20/prompt.en.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-20/constraints.json) |
| Dataset rule | Top 25% | [Copy prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-25/prompt.en.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-25/constraints.json) |
| Dataset rule | Top 30% | [Copy prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-30/prompt.en.md) | [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-30/constraints.json) |

<details>
<summary>More options: another AD_GAP Top 10% rule</summary>

`adept-gap-high-10` is another frozen Top 10% rule learned from the public data and marked as a nondefault choice in the catalog. To select this variant explicitly, open:

- [Top 10% variant English prompt](../skills/stca/assets/rule_library/entries/adept-gap-high-10/prompt.en.md) · [JSON](../skills/stca/assets/rule_library/entries/adept-gap-high-10/constraints.json)

It has a different rule ID from the author default. Keep the chosen ID and every condition from its prompt when invoking or checking it.

</details>
