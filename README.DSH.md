<p align="center"><img src="https://raw.githubusercontent.com/foukusa/stca-agent-skill/main/assets/stca-logo.png" alt="STCA logo" width="104"></p>

# STCA for DeepSeek Harness

Bring STCA into your DeepSeek Harness conversation: learn and save readable polymer rules, screen candidates, and generate and verify repeat units with the current AI assistant.

**Version 0.1.0** · [简体中文](https://github.com/foukusa/stca-agent-skill/blob/main/README.DSH.zh-CN.md)

[STCA paper](https://doi.org/10.1038/s41524-026-02345-x) · [Python library](https://github.com/foukusa/polymer-stca) · [All platforms](https://github.com/foukusa/stca-agent-skill#download-and-install)

## Contents

- [Why STCA](#why-stca)
- [Install and start](#install-and-start)
- [Choose a task](#choose-a-task)
- [Data columns and attachment points](#data-columns-and-attachment-points)
- [Try RadonPy density](#try-radonpy-density)
- [Try water contact angle](#try-water-contact-angle)
- [Runtime and permissions](#runtime-and-permissions)
- [License and sources](#license-and-sources)

## Why STCA

**STCA — Sliding Threshold Correlation Analysis — turns polymer structure–property data into readable structural rules.** It follows substructure associations across property thresholds and expresses the target as conditions that a repeat unit must satisfy together. You can inspect and reuse the same rules to screen candidates or guide the current LLM in designing and verifying new repeat units. The skill handles the calculations through ordinary conversation and compares STCA with WRAcc for your data.

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

Learning requires an explicitly bound **structure column, numeric property column and unit**. You can name them in your request. For a recognized source such as the RadonPy example below, the mapping is already supplied; otherwise the assistant reads the headers and displays the columns, target meaning and unit it will use before learning. If more than one column could mean the target—such as measured versus calculated density, different temperatures, or a mean versus a minimum/maximum—it asks you to choose first. Your explicit column names take precedence. Numeric ranges alone do not establish a column's meaning. Screening with an existing rule needs the structure column, without property labels for the candidates.

Upload the original repeat-unit SMILES **with their `*` attachment points retained**. STCA keeps that original text and creates a separate calculation copy: supported terminal single-bond attachment atoms are capped with hydrogen (**H-cap**) before fingerprints are calculated. ECFP4 defines structural distance; MACCS167 encodes the rule conditions. Results return the preserved original SMILES with the same `*` positions. This is not a text replacement or an attempt to infer attachment positions from the capped molecule. Already capped inputs remain as supplied; attachment points are not invented.

| Uploaded original | H-cap calculation copy | Returned structure |
|---|---|---|
| `*CCO*` | `CCO` | `*CCO*` |

## Try RadonPy density

Download [RadonPy `PI1070.csv`](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv) from its GitHub file page and upload it in DSH. Use all **1,077 records**: row 1 is the header and rows 2–1078 are data. Select `smiles` (B / column 2) for structures and `density` (AA / column 27), in g/cm³, for the molecular-dynamics target. `monomer_ID` (A / column 1) is an optional identifier. The assistant reads column names; you do not need to extract cells. Other density statistics are not the target.

**Existing-rule screening:**

```text
Use the recommended RadonPy high-density Top 30% rule to screen this dataset.
```

The assistant shows the rule, its **numeric density cutoff in g/cm³**, and both methods’ screening results. Top 30% describes the property target in the rule’s training data; it does not require exactly 30% of candidate structures to match.

**Learning, screening and saving:**

```text
Learn high-density Top 30% rules from all rows of this RadonPy file. Use smiles for structures and density for the target, in g/cm³. Return screening results, compare them with the existing rule and save the new rules.
```

Each percentage is prepared and fitted independently within the training part. The assistant returns STCA and WRAcc, independent Morgan-distance extrapolation results, and screening results for every original row. To reuse the recommendation, say “Reload the recommended Top 30% rule just saved and screen the same dataset again.” Every row must match its earlier decision.

**Generation:**

```text
Use the high-density Top 30% STCA rule just saved to directly generate and verify five polymer repeat units.
```

Or ask to see the complete prompt first, adjust it, then say “Confirm and generate.” The current DSH LLM generates; STCA performs the structural checks. See the [complete RadonPy case](https://github.com/foukusa/stca-agent-skill/blob/main/examples/radonpy_density/README.md).

See [five actual generated proposals and their verification](https://github.com/foukusa/stca-agent-skill/blob/main/examples/radonpy_density/generated_examples.csv).

## Try water contact angle

The [OpenPoly example](https://github.com/foukusa/stca-agent-skill/blob/main/examples/water_contact_angle/README.md) extends the same workflow to measured water contact angle. Upload its source CSV and say:

```text
/stca Learn high water-contact-angle Top 30% rules from this OpenPoly file. Use PSMILES for structures and Water Contact Angle (deg) for the property, in degrees. Return both methods, extrapolation results and screening results, then save the rules.
```

Records with usable labels support learning; the remaining structures can be screened as candidates. You can also choose an existing water-contact-angle rule from the catalog, or ask the current DSH LLM to generate and verify repeat units with it. The example includes the public data source, column mapping and computed results.

## Runtime and permissions

- Required DSH version: **`>=0.0.1-rc.3 <0.3.0`**.
- Calculations use a **CPU and Python 3.10+**. Screening and verification need RDKit; learning also uses the numerical stack. STCA automatically discovers and checks local interpreters, including ordinary Python, virtual environments and Conda environments. **Conda and manual Python-path entry are not required.** Compatible environments are reused; missing dependencies can be prepared in a separate user-cache environment.
- The DSH session needs permission to read the selected data, write the output directory and run local commands. Input files are retained and results are written separately. Rule lookup and reading saved prompts do not require RDKit. If the computation environment fails, proposals remain unverified; that failure does not mean their SMILES or rules failed.
- The checked author implementation is bundled, so ordinary calculations do not require Git or clone source. Preparing missing Python dependencies can access PyPI. Generation uses the model/provider already configured for the current DSH session, with no separate model API setup for STCA. Session and provider data policies still apply.

## License and sources

This is a community-developed STCA integration, with no official affiliation to DeepSeek AI. Source availability is governed by the **[STCA Agent Skill Academic Use License](https://github.com/foukusa/stca-agent-skill/blob/main/LICENSE)**: non-commercial academic research, education and scientific reproduction are permitted; commercial use and redistribution require prior written permission. Third-party components retain their [own notices and terms](https://github.com/foukusa/stca-agent-skill/blob/main/THIRD_PARTY_NOTICES.md).

**Weihao Wang** · [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) · [Original implementation](https://github.com/foukusa/polymer-stca) · [Full project README](https://github.com/foukusa/stca-agent-skill/blob/main/README.md) · [ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

<p align="center"><em>“Out of clutter, find simplicity.”</em><br><sub>— attributed to Albert Einstein</sub></p>
