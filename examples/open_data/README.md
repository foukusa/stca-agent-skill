# More application examples

[简体中文](README.zh-CN.md) · [Main guide](../../README.md) · Version **0.1.0**

## Contents

- [Start with a built-in task](#start-with-a-built-in-task)
- [Choose a rule and method](#choose-a-rule-and-method)
- [Try a short request](#try-a-short-request)
- [Data sources and fields](#data-sources-and-fields)
- [Learn, save and continue](#learn-save-and-continue)

## Start with a built-in task

Enable STCA and say **“Start STCA”**, or state your goal directly:

1. **Upload data and learn rules**: provide structures and numeric property values. Specify the direction and any percentages you want; omitted percentages use 10%, 20% and 30%.
2. **Screen with existing rules**: upload candidates and choose bundled rules or your saved rules.
3. **Generate with existing rules**: view the catalog, choose your rules, then preview and confirm the prompt or generate directly.

The complete task prompts are built in. The AI assistant reads the headers, offers available sources and asks only for essential missing information. You do not need rule IDs or technical commands.

## Choose a rule and method

The [rule and generation-prompt directory](../../docs/RULE_LIBRARY.md) includes **13 public-data property tasks**: two measured GAS tasks, five RadonPy computed tasks, five ADEPT computed tasks and OpenPoly water contact angle. Their source-trained frozen rules target **high values at Top 10%, 20% and 30%**.

Each source, property and percentage reports **STCA and WRAcc separately, including rule availability**. Choose an available rule or accept the recommendation; the catalog gives scores and the reason for each recommendation. All conditions within a selected rule must hold.

Rule availability follows the current calculation for each method and tier. A missing rule retains its reason; it is not represented as an empty rule that selects every structure.

See the [current rules and screening scores](current_rule_metrics.csv) for each task and percentage. New rules are learned from source data after a strict **ECFP4 Morgan-distance split**; every outer holdout structure has nearest-source Tanimoto distance **≥ 0.5**. A separate source-inner Morgan validation determines the method recommendation before outer evaluation. Recommendations use the average screening score introduced in the [STCA paper](https://doi.org/10.1038/s41524-026-02345-x). Say “Use the recommended method” or select STCA or WRAcc. See [evaluation details](../../docs/MORGAN_EVALUATION.md).

When learning from your own data, WRAcc selects its condition-count limit within training data by default. You can also request “at most 10 conditions” or “no condition-count limit.”

To use another direction or a percentage such as **15% or 25%**, upload suitable labelled data and learn new rules. For example: “Learn high-refractive-index Top 15% and 25% rules from this computed table.”

## Try a short request

Upload your candidate table, then use one of these requests:

| Goal | A request to start with |
|---|---|
| High CO₂ permeability | “Use the recommended measured GAS high-CO₂-permeability Top 10% rule to screen this table.” |
| High O₂ permeability | “Screen these candidates with the recommended measured GAS high-O₂-permeability Top 10% rule.” |
| High water contact angle | “Use the existing OpenPoly high-water-contact-angle Top 30% rule to screen these candidates.” |
| High specific heat | “Use RadonPy's recommended high-specific-heat Top 10% rule to screen my candidates.” |
| High dielectric constant | “Use ADEPT's recommended high-dielectric-constant Top 20% rule to screen this table.” |

The catalog supplies the current recommendation for the selected task. Ask to see both methods' scores if you want to choose yourself. High and low dielectric constant are different objectives; learn from your own data if you need the low direction.

For generation, ask to see the available rules, or specify the source, property, percentage and method directly. For example: “Use the recommended ADEPT high-dielectric-constant Top 20% rule; generate 20 candidates directly and verify them.” To review first, say “Show me the complete prompt before generating”; you can adjust it, then say “Confirm and generate.” The current LLM generates the candidates in either mode.

## Data sources and fields

STCA learns readable screening rules and evaluates their transfer to structurally distant polymers across these 13 public-data tasks. The source datasets and label types are:

| Source | Data and original study | Labels used |
|---|---|---|
| GAS | [Dataset A](https://github.com/jsunn-y/PolymerGasMembraneML/blob/30981d71e1e3f12a057e009cd79f119bc659c7f5/datasets/datasetA_imputed_all.csv) · [source paper](https://doi.org/10.1126/sciadv.abn9545) | Measured CO₂ and O₂ permeability |
| RadonPy | [PI1070](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv) · [source paper](https://doi.org/10.1038/s41524-022-00906-4) | Molecular-dynamics properties |
| ADEPT | [PolyGraphMT data](https://github.com/sobinalosious/PolyGraphMT/tree/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw) · [source paper](https://doi.org/10.1039/D6DD00206D) | MD properties and DFT isolated-monomer gap |
| OpenPoly | [Original property table](https://github.com/WangGroupFDU/Openpoly_benchmark/blob/ccaa66900747bfc576ef935e3d5f220b6c9b1f85/data/final_polymer_properties_fromliterature.csv) · [source paper](https://doi.org/10.1007/s10118-025-3402-y) | Literature-reported water contact angle |

GAS rules use the original measured `CO2` and `O2` values. Missing values are excluded from learning; Bayesian and Etree imputed columns are not substituted for measured labels.

Use the original columns when uploading these source files:

| Property | Data file | Structure column | Property column | Unit |
|---|---|---|---|---|
| CO₂ permeability | Dataset A: `datasetA_imputed_all.csv` | `Smiles` | `CO2` | Barrer |
| O₂ permeability | Dataset A: `datasetA_imputed_all.csv` | `Smiles` | `O2` | Barrer |
| Thermal conductivity | RadonPy: `PI1070.csv` | `smiles` | `thermal_conductivity` | W/(m K) |
| Refractive index | RadonPy: `PI1070.csv` | `smiles` | `refractive_index` | dimensionless |
| Density | RadonPy: `PI1070.csv` | `smiles` | `density` | g/cm³ |
| Specific heat | RadonPy: `PI1070.csv` | `smiles` | `Cp` | J/(kg K) |
| Dielectric constant | RadonPy: `PI1070.csv` | `smiles` | `dielectric_const_dc` | dimensionless |
| Thermal conductivity | ADEPT: `TC_MD.csv` | `SMILES` | `TC` | W/(m K) |
| Density | ADEPT: `RHO_MD.csv` | `SMILES` | `RHO` | g/cm³ |
| Isolated-monomer HOMO–LUMO gap | ADEPT: `BANDGAP_DFT.csv` | `SMILES` | `BANDGAP` | eV |
| Dielectric constant | ADEPT: `DC_MD.csv` | `SMILES` | `DC` | dimensionless |
| Refractive index | ADEPT: `RI_MD.csv` | `SMILES` | `RI` | dimensionless |
| Water contact angle | OpenPoly: [`OpenPoly.csv`](../water_contact_angle/OpenPoly.csv) | `PSMILES` | `Water Contact Angle (deg)` | degrees |

The [water-contact-angle example](../water_contact_angle/README.md) includes the original OpenPoly table, exact column binding and natural-language requests. A 0° contact angle is valid and retained. OpenPoly measurement conditions are not supplied in the property table.

The ADEPT gap is the DFT HOMO–LUMO gap of a hydrogen-capped isolated monomer. The [source and field index](dataset_registry.csv) provides dataset links, original columns, units and licence information. Cite the original sources when using their data.

Your own learning data needs structures and numeric property values. Supply units, experimental/computed origin and any existing split when needed. Identifiers are optional and may have any name.

Learning requires an explicitly bound **structure column, numeric property column and unit**. You can name them in your request. For a recognized source such as the RadonPy example below, the mapping is already supplied; otherwise the assistant reads the headers and displays the columns, target meaning and unit it will use before learning. If more than one column could mean the target—such as measured versus calculated density, different temperatures, or a mean versus a minimum/maximum—it asks you to choose first. Your explicit column names take precedence. Numeric ranges alone do not establish a column's meaning. Screening with an existing rule needs the structure column, without property labels for the candidates.

Upload the original repeat-unit SMILES **with their `*` attachment points retained**. STCA keeps that original text and creates a separate calculation copy: supported terminal single-bond attachment atoms are capped with hydrogen (**H-cap**) before fingerprints are calculated. Results return the preserved original SMILES with the same `*` positions. This is not a text replacement or an attempt to infer attachment positions from the capped molecule. Already capped inputs remain as supplied; attachment points are not invented. Different original attachment patterns remain separate records even when their H-cap calculation copies coincide.

| Uploaded original | H-cap calculation copy | Returned structure |
|---|---|---|
| `*CCO*` | `CCO` | `*CCO*` |

## Learn, save and continue

First split structures, then independently select preparation and scan settings for each percentage using source data only. With the same input, version and settings, requesting a percentage alone or together with others gives the same result for that percentage.

After learning, STCA returns rules, physical cutoffs and **a separate screening result for each method at every requested tier**. The original uploaded table is screened by default. If you also upload an independent candidate table, its screening results are returned separately.

Every screening table preserves original star-containing SMILES and identifiers, with selection decisions, each unmet rule condition and uncomputable records. A method or tier without a valid rule retains its status and reason. Empty conditions do not mean all structures pass.

Models, rules and complete bilingual generation prompts are saved as reusable files. The assistant reports their actual location and provides a rule bundle. Continue with “Screen this table with the rules just saved” or “Generate with those rules.” Upload the saved bundle to reuse it in another conversation or platform.

After selecting the rules, choose **Preview and confirm** or **Generate directly**. Both return every proposal and its verification results, including unmet rule conditions, and let you continue the conversation. No additional LLM API setup is needed. To use another LLM instead, ask **“Give me only the complete generation prompt”**, copy it there, then upload its candidate table and say **“Verify these candidates with the same rules.”** Structural rule compliance and actual property validation are reported separately. See [installation instructions](../../docs/INSTALL.md) and the [natural-language usage guide](../../docs/USAGE.md).
