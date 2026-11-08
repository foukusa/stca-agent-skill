# More application examples

[简体中文](README.zh-CN.md) · [Main guide](../../README.md) · Version **0.1.0**

## Contents

- [Start with a built-in task](#start-with-a-built-in-task)
- [Choose a rule and method](#choose-a-rule-and-method)
- [Try a short request](#try-a-short-request)
- [Data sources and fields](#data-sources-and-fields)
- [Learn, save and continue](#learn-save-and-continue)

## Start with a built-in task

Enable STCA and say **“Start STCA”**, then choose:

1. **Upload data and learn rules**: provide structures and numeric property values, then choose the direction and percentages.
2. **Screen with existing rules**: upload candidates and choose bundled rules or My rules.
3. **Generate with existing rules**: view the catalog, choose your rules, then preview and confirm the prompt or generate directly.

The complete task prompts are built in. The AI assistant reads the headers, offers available sources, percentages and methods, and asks only for essential missing information. You do not need rule IDs or technical commands.

## Choose a rule and method

The [rule and generation-prompt directory](../../docs/RULE_LIBRARY.md) includes **12 public-data property tasks**: two measured GAS tasks, five RadonPy computed tasks and five ADEPT computed tasks. Their frozen rules target **high values at Top 10%, 20% and 30%**.

Each source, property and percentage has **two separately usable rules: STCA and WRAcc**. The catalog identifies the primary and alternative methods; ask for their evaluation scores when needed. The primary method is selected by default; you can choose the alternative instead. **Choose one method for each tier; the two rules are not combined with OR.** All conditions within the chosen rule must hold.

The primary method is chosen using grouped cross-validation AS, the mean of Precision, F1 and MCC. STCA is retained when the two AS scores differ by no more than 0.02. These scores describe evaluation within the source data; they do not guarantee a new candidate's property value.

To use another direction or a percentage such as **15% or 25%**, upload suitable labelled data and learn new rules. For example: “Learn high-refractive-index Top 15% and 25% rules from this computed table.”

## Try a short request

Upload your candidate table, then use one of these requests:

| Goal | A request to start with |
|---|---|
| High CO₂ permeability | “Use the measured GAS high-CO₂-permeability Top 10% rule, with the primary STCA method, to screen this table.” |
| High O₂ permeability | “Screen these candidates with the measured GAS high-O₂-permeability Top 10% STCA rule.” |
| High specific heat | “Use RadonPy's high-specific-heat Top 10% STCA rule to screen my candidates.” |
| High dielectric constant | “Use ADEPT's high-dielectric-constant Top 20% WRAcc rule to screen this table.” |

STCA is primary for the first three examples; WRAcc is primary for the ADEPT dielectric example. You can ask to see both methods' scores before choosing. High and low dielectric constant are different objectives; learn from your own data if you need the low direction.

For generation, first say **“3”**. After the catalog appears, choose a source, property, percentage and method. For example: “Choose ADEPT high dielectric constant, Top 20%, WRAcc; generate 20 candidates directly and verify them.” To review first, say “Show me the complete prompt before generating”; you can adjust it, then say “Confirm and generate.” The current LLM generates the candidates in either mode.

## Data sources and fields

The original sources are [Dataset A](https://github.com/jsunn-y/PolymerGasMembraneML/blob/main/datasets/datasetA_imputed_all.csv), [RadonPy PI1070](https://github.com/RadonPy/RadonPy/blob/develop/data/PI1070.csv) and [ADEPT / PolyGraphMT](https://github.com/sobinalosious/PolyGraphMT/tree/main/data/raw). GAS rules use measured `CO2` and `O2` values, excluding missing values and imputed substitutes. RadonPy labels are molecular-simulation results; ADEPT labels are MD results except for the DFT monomer gap.

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

The ADEPT gap is the DFT HOMO–LUMO gap of a hydrogen-capped isolated monomer. The [source and field index](dataset_registry.csv) provides source links and licence notes; cite the original sources when using their data. ADEPT's source repository does not supply an explicit redistribution licence, so its individual data records are not bundled here.

Your own learning data needs structures and numeric property values. Supply units, experimental/computed origin and any existing split when needed. Identifiers are optional and may have any name. Candidate-only screening needs structures, with no property labels required.

## Learn, save and continue

After learning, STCA returns rules, physical cutoffs and **a separate screening result for each method at every requested tier**. The original uploaded table is screened by default. If you also upload an independent candidate table, its screening results are returned separately.

Every screening table preserves original star-containing SMILES and identifiers, with selection decisions, each failed condition and uncomputable records. A method or tier without a valid rule retains its status and reason. Empty conditions do not mean all structures pass.

The model, rules and complete bilingual generation prompts are saved under **My rules**. STCA shows the saved name and returns to the main menu; choose task **2** or **3** to reuse them. “Main menu” or “Back” preserves saved rules. To continue in another session or platform, download the rule bundle and upload it in the new session.

Task **3** offers **Preview and confirm** and **Generate directly** after rule selection. Both return every proposal and its verification results, including failed conditions, then return to the main menu. No additional LLM API setup is needed. To use another LLM instead, ask **“Give me only the complete generation prompt”**, copy it there, then upload its candidate table and say **“Verify these candidates with the same rules.”** Structural rule compliance and actual property validation are reported separately. See [Mac installation](../../docs/INSTALL.md) and the [natural-language usage guide](../../docs/USAGE.md).
