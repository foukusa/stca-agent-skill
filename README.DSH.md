<p align="center"><img src="https://raw.githubusercontent.com/foukusa/stca-agent-skill/main/assets/stca-logo.png" alt="STCA logo" width="104"></p>

# STCA for DeepSeek Harness

Learn readable polymer structure–property rules, screen candidates, or generate polymer repeat units with the current AI assistant.

**DSH package: `dsh-plugin-stca` · Version 0.1.0** · [简体中文](https://github.com/foukusa/stca-agent-skill/blob/main/README.DSH.zh-CN.md)

## Contents

- [Install and start](#install-and-start)
- [Choose a task](#choose-a-task)
- [Try a screening example](#try-a-screening-example)
- [Runtime and permissions](#runtime-and-permissions)
- [License and sources](#license-and-sources)

## Install and start

1. Open **Plugins → Add plugin**.
2. Enter one of the sources below, complete installation and enable STCA.
3. Enter `/stca` and describe the task you want to perform.

| Source | Value |
|---|---|
| GitHub repository | `https://github.com/foukusa/stca-agent-skill.git` |
| npm package name | `dsh-plugin-stca` — available after npm publication |
| Plugin center | — (link will be added after listing) |

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

For the CLI, use your active profile. These commands use `web` as an example:

```bash
dsh plugin --profile web add github:foukusa/stca-agent-skill
```

After npm publication, the package-name command is:

```bash
dsh plugin --profile web add dsh-plugin-stca
```

From the [GitHub repository](https://github.com/foukusa/stca-agent-skill), **Code → Download ZIP** downloads the source; the DSH skill is at `skills/stca`. You can also download the [plugin TGZ](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz?raw=true) and enter its complete local path in Add plugin. The [skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip?raw=true) uses manual folder installation; see the [installation guide](https://github.com/foukusa/stca-agent-skill/blob/main/docs/INSTALL.md#deepseek-harness).

After enabling the plugin, enter **`/stca`** or say **“Start STCA.”**

## Choose a task

STCA works through the current LLM conversation. State a task directly; if you only say “Start STCA,” the assistant can explain the three available workflows. Describe the desired task in ordinary language.

| Choice | What you receive | Example request |
|---|---|---|
| **Learn from my data** | Saved STCA and WRAcc rules, their screening results, physical cutoffs and a recommendation | “Learn high thermal-conductivity rules from this polymer dataset and save them.” |
| **Screen with existing rules** | Decisions for every original candidate, unmet rule conditions and selected records | “Show the rule catalog and screen my candidates with the rule I choose.” |
| **Generate with existing rules** | Rule-guided proposals from the current LLM, followed by structural-rule verification | “Choose a rule, then directly generate and verify 20 polymer repeat units.” |

Complete task prompts are built in. Learning uses Top or Bottom **10%, 20% and 30%** when percentages are omitted; you may choose other valid percentages. Every tier reports its numeric cutoff, comparison and unit. Original SMILES and repeat-unit attachment points are preserved; H-cap is calculation-only.

When you have not selected a rule, the assistant shows the available rule catalog. Choose **preview and confirm** to inspect and adjust the prompt before generation, or **generate directly**. The assistant returns the saved rule files and their location. Continue with “Screen these candidates with the rules just saved” or “Generate with those rules.” See the [natural-language examples](https://github.com/foukusa/stca-agent-skill/blob/main/docs/USAGE.md) and [rule catalog](https://github.com/foukusa/stca-agent-skill/blob/main/docs/RULE_LIBRARY.md).

## Try a screening example

```text
Use the bundled fluorinated-candidate example. Screen it with the RadonPy high-density Top 30% STCA rule and show every unmet rule condition.
```

The [five predefined candidates](https://github.com/foukusa/stca-agent-skill/blob/main/examples/quick_start/candidates.csv) include **three matches** (PVDF, PTFE and PVF) and **two non-matches** (PE and PEO) for the frozen `K42=1` rule. This bundled example demonstrates structural-rule screening.

To learn your own rules, upload the [RadonPy PI1070 CSV](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv) and say: “Learn high-density rules from this computed data in g/cm³, return the screening results and save the rules.” The structure column is `smiles` and the target is `density`.

## Runtime and permissions

- Required DSH version: **`>=0.0.1-rc.3 <0.3.0`**.
- Calculations use a **CPU and Python 3.10+**. Screening and verification need RDKit; learning also uses the numerical stack. STCA automatically discovers and checks local interpreters, including ordinary Python, virtual environments and Conda environments. **Conda and manual Python-path entry are not required.** Compatible environments are reused; missing dependencies can be prepared in a separate user-cache environment.
- The DSH session needs permission to read the selected data, write the output directory and run local commands. Input files are retained and results are written separately. Rule lookup and reading saved prompts do not require RDKit. If the computation environment fails, proposals remain unverified; that failure does not mean their SMILES or rules failed.
- Dependency preparation can access PyPI; preparing the author implementation for learning can access GitHub and requires Git. Generation uses the model/provider already configured for the current DSH session, with no separate model API setup for STCA. Session and provider data policies still apply.

## License and sources

This is a community-developed STCA integration, with no official affiliation to DeepSeek AI. Source availability is governed by the **[STCA Agent Skill Academic Use License](https://github.com/foukusa/stca-agent-skill/blob/main/LICENSE)**: non-commercial academic research, education and scientific reproduction are permitted; commercial use and redistribution require prior written permission. Third-party components retain their [own notices and terms](https://github.com/foukusa/stca-agent-skill/blob/main/THIRD_PARTY_NOTICES.md).

**Weihao Wang** · [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) · [Original implementation](https://github.com/foukusa/polymer-stca) · [Full project README](https://github.com/foukusa/stca-agent-skill/blob/main/README.md) · [ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

<p align="center"><em>“Out of clutter, find simplicity.”</em><br><sub>— attributed to Albert Einstein</sub></p>
