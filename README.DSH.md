<p align="center"><img src="https://raw.githubusercontent.com/foukusa/stca-agent-skill/main/assets/stca-logo.png" alt="STCA logo" width="104"></p>

# STCA for DeepSeek Harness

Learn rules from data, screen with existing rules, or generate new structures

**Version 0.1.0** · [简体中文](https://github.com/foukusa/stca-agent-skill/blob/main/README.DSH.zh-CN.md)

[STCA paper](https://doi.org/10.1038/s41524-026-02345-x) · [Python library](https://github.com/foukusa/polymer-stca) · [All platforms](https://github.com/foukusa/stca-agent-skill#download-and-install)

## Contents

- [Install and start](#install-and-start)
- [Choose a task](#choose-a-task)
- [Data columns and attachment points](#data-columns-and-attachment-points)
- [Data splitting and evaluation](#data-splitting-and-evaluation)
- [Try an example](#try-an-example)
- [Existing rules and supported properties](#existing-rules-and-supported-properties)
- [Runtime and permissions](#runtime-and-permissions)
- [License and sources](#license-and-sources)

## Install and start

1. In DSH, open **Plugins → Add plugin**.
2. In the field for a package name, GitHub repository URL or local directory, enter:

```text
github:foukusa/stca-agent-skill
```

3. Click Install, enable STCA, then enter `/stca` or say “Start STCA”.

Alternatively, install from the terminal with the DSH CLI:

```bash
dsh plugin --profile web add github:foukusa/stca-agent-skill
```

**This installs the plugin from GitHub; npm publication is not required.** The repository supplies `package.json`, the plugin entry and complete skill resources. Do not paste a `dsh plugin ...` command into this graphical input field.

| Route | Value for Add plugin |
|---|---|
| **GitHub repository, recommended now** | `github:foukusa/stca-agent-skill` |
| Downloaded plugin ZIP | Full path to the extracted [plugin ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.zip) directory that directly contains `package.json` |
| npm name, after publication | `dsh-plugin-stca` |
| Plugin center | — (link to be added after listing) |

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

Use the `github:` address above in Add plugin. If a previous HTTPS installation reported “Unable to determine the installed package from dependency changes,” retry with this address. If STCA is already listed, check and enable that entry; preserve your data, results and saved rules when replacing an old copy. See the [installation guide](https://github.com/foukusa/stca-agent-skill/blob/main/docs/INSTALL.md#deepseek-harness) for installation errors and optional CLI use.

Local-directory installation is a fallback: open the plugin ZIP page, click **Download raw file**, extract it, then enter the full plugin-directory path. The separate [standalone skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip) is for manually placing the complete `stca` folder containing `SKILL.md`; it uses a different installation route from a plugin directory.

## Choose a task

STCA works through the current LLM conversation. State a task directly; if you only say “Start STCA,” the assistant can explain the three available workflows. Describe the desired task in ordinary language.

| Choice | What you receive | Example request |
|---|---|---|
| **Learn from my data** | Both methods’ results and availability, saved rules, physical cutoffs and a recommendation | “Learn high thermal-conductivity rules from this polymer dataset and save them.” |
| **Screen with existing rules** | Decisions for every original candidate, unmet rule conditions and selected records | “Show the rule catalog and screen my candidates with the rule I choose.” |
| **Generate with existing rules** | Rule-guided proposals from the current LLM, followed by structural-rule verification | “Choose a rule, then directly generate and verify 20 polymer repeat units.” |

Complete task prompts are built in. Learning uses Top or Bottom **10%, 20% and 30%** when percentages are omitted; you may choose other valid percentages. Every tier reports its numeric cutoff, comparison and unit. WRAcc chooses rule length within the training data; you can instead request “At most 10 WRAcc conditions” or “No WRAcc condition-count limit.” Both methods and their recommendation are returned separately. Original SMILES and repeat-unit attachment points are preserved; H-cap is calculation-only.

Learning defaults to **Morgan-distance extrapolation evaluation**: ECFP4 (radius 2, 2,048 bits) separates distant evaluation structures from training structures with a nearest-training Tanimoto distance **≥ 0.5**. Data transforms, scan settings, rule selection and the method recommendation use training data only. Similarity-buffer records stay out of both training and evaluation, while screening results still cover the original table. The assistant reports both methods’ extrapolation performance and each percentage’s training-defined physical cutoff.

When you have not selected a rule, the assistant shows the available rule catalog. Choose **preview and confirm** to inspect and adjust the prompt before generation, or **generate directly**. The assistant returns the saved rule files and their location. Continue with “Screen these candidates with the rules just saved” or “Generate with those rules.” See the [natural-language examples](https://github.com/foukusa/stca-agent-skill/blob/main/docs/USAGE.md) and [rule catalog](https://github.com/foukusa/stca-agent-skill/blob/main/docs/RULE_LIBRARY.md).

## Data columns and attachment points

Learning requires an explicitly bound **structure column, numeric property column and unit**. You can name them in your request. For a recognized source such as the ADEPT example below, the mapping is already supplied; otherwise the assistant reads the headers and displays the columns, target meaning and unit it will use before learning. If more than one column could mean the target—such as measured versus calculated density, different temperatures, or a mean versus a minimum/maximum—it asks you to choose first. Your explicit column names take precedence. Numeric ranges alone do not establish a column's meaning. Screening with an existing rule needs the structure column, without property labels for the candidates.

Upload the original repeat-unit SMILES **with their `*` attachment points retained**. STCA keeps that original text and creates a separate calculation copy: supported terminal single-bond attachment atoms are capped with hydrogen (**H-cap**) before fingerprints are calculated. ECFP4 defines structural distance; MACCS167 encodes the rule conditions. Results return the preserved original SMILES with the same `*` positions. This is not a text replacement or an attempt to infer attachment positions from the capped molecule. Already capped inputs remain as supplied; attachment points are not invented.

| Uploaded original | H-cap calculation copy | Returned structure |
|---|---|---|
| `*CCO*` | `CCO` | `*CCO*` |

## Data splitting and evaluation

Structural distance uses **ECFP4**: radius=2, 2,048-bit Morgan fingerprints of H-capped calculation copies, with **distance = 1 − Tanimoto similarity**. Identical original structures and identical H-capped copies stay in the same protected group.

| Partition or evaluation | What happens |
|---|---|
| **Interpolation region** | Learn rules and choose data transforms, scan steps and support in this region. |
| **Extrapolation region** | Select a peripheral structural neighborhood, targeting 20% of structurally valid records, before using property labels. Every extrapolation structure has nearest-neighbour distance **≥0.5** from the interpolation region. |
| **Similarity buffer** | Keep other groups closer than 0.5 to the extrapolation region out of training and evaluation. They remain in the returned screening table. |
| **Evaluation within the interpolation region** | Protected-group 5-fold cross-validation, repeated three times. This diagnostic uses the region's data preparation; it is not a separate independent interpolation test set. |

This design keeps identical and nearby structures from crossing the interpolation–extrapolation boundary and tests whether rules transfer to structurally different polymers. A further Morgan-distance validation **inside the interpolation region** selects the recommended method before the extrapolation region is evaluated. Frozen thresholds and rules are then applied unchanged. See [evaluation details](https://github.com/foukusa/stca-agent-skill/blob/main/docs/MORGAN_EVALUATION.md).

## Try an example

Download [ADEPT `BANDGAP_DFT.csv`](https://github.com/sobinalosious/PolyGraphMT/blob/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw/BANDGAP_DFT.csv) and upload it to the conversation. This file has **2,916 records and two columns**. The target is the **DFT HOMO–LUMO gap of a hydrogen-capped isolated monomer**, in eV.

| Use | Column | Spreadsheet position |
|---|---|---|
| Repeat-unit structure | `SMILES` | A · column 1 |
| Isolated-monomer gap | `BANDGAP` | B · column 2 |

Row 1 is the header; rows **2–2917** contain data. Use all rows as input. No identifier column is required.

**Screen with the existing STCA rule:**

```text
Use the existing ADEPT high isolated-monomer HOMO–LUMO gap Top 30% STCA rule to screen this file.
```

The frozen target is **gap ≥ 11.914537535 eV**. This file produces **976 matches, 1,940 non-matches and no unknowns**. On 584 independent Morgan-distance extrapolation records, the STCA rule has **precision 0.7500, recall 0.7784, F1 0.7639 and Matthews correlation coefficient 0.6517**. Full-table matches and independent evaluation are reported separately.

**Learn rules, screen and save:**

```text
Learn high isolated-monomer HOMO–LUMO gap Top 30% rules from this ADEPT file. Use SMILES for structures and BANDGAP for the target, in eV. Use all input rows, return both methods, extrapolation evaluation and screening results, and save the rules.
```

The assistant learns STCA and WRAcc from the training partition and returns both results. Continue with **“Reload the Top 30% STCA rule just saved and screen the same file.”** Every row must match its previous decision.

**Generate with the selected rule:**

```text
Use the Top 30% STCA rule just saved to directly generate and verify five polymer repeat units.
```

To adjust the prompt first, say **“Show the complete generation prompt before generating.”** After your edits, say **“Confirm and generate.”** The current LLM proposes candidates and STCA verifies their exact structural conditions. See the [complete ADEPT example](https://github.com/foukusa/stca-agent-skill/blob/main/examples/adept_gap/README.md) and [generated proposals](https://github.com/foukusa/stca-agent-skill/blob/main/examples/adept_gap/generated_examples.csv).

## Existing rules and supported properties

The [rule catalog](https://github.com/foukusa/stca-agent-skill/blob/main/docs/RULE_LIBRARY.md) includes the paper Tg/conductivity rules, gas permeability, RadonPy and ADEPT properties, and **OpenPoly water-contact-angle Top10%,20%,30%** rules. Choose a source, property, percentage and method to screen candidates; the catalog provides each tier’s thresholds, structural conditions and screening evaluation.

## Runtime and permissions

- Required DSH version: **`>=0.0.1-rc.3 <0.3.0`**.
- Calculations use a **CPU and Python 3.10+**. Screening and verification need RDKit; learning also uses the numerical stack. STCA automatically discovers and checks local interpreters, including ordinary Python, virtual environments and Conda environments. **Conda and manual Python-path entry are not required.** Compatible environments are reused; missing dependencies can be prepared in a separate user-cache environment.
- The DSH session needs permission to read the selected data, write the output directory and run local commands. Input files are retained and results are written separately. Rule lookup and reading saved prompts do not require RDKit. If the computation environment fails, proposals remain unverified; that failure does not mean their SMILES or rules failed.
- The checked author implementation is bundled, so ordinary calculations do not require Git or clone source. Preparing missing Python dependencies can access PyPI. Generation uses the model/provider already configured for the current DSH session, with no separate model API setup for STCA. Session and provider data policies still apply.

## License and sources

This is a community-developed STCA integration, with no official affiliation to DeepSeek AI. Source availability is governed by the **[STCA Agent Skill Academic Use License](https://github.com/foukusa/stca-agent-skill/blob/main/LICENSE)**: non-commercial academic research, education and scientific reproduction are permitted; commercial use and redistribution require prior written permission. Third-party components retain their [own notices and terms](https://github.com/foukusa/stca-agent-skill/blob/main/THIRD_PARTY_NOTICES.md).

**Weihao Wang** · [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) · [Original implementation](https://github.com/foukusa/polymer-stca) · [Full project README](https://github.com/foukusa/stca-agent-skill/blob/main/README.md) · [ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

<p align="center"><em>“Out of clutter, find simplicity.”</em><br><sub>— attributed to Albert Einstein</sub></p>
