<p align="center"><img src="assets/stca-logo.png" alt="STCA logo" width="104"></p>
<h1 align="center">STCA Agent Skill</h1>
<p align="center">Learn rules from data, screen with existing rules, or generate new structures.</p>
<p align="center"><strong>0.1.0</strong> · English · <a href="README.zh-CN.md">简体中文</a></p>

## Contents

- [Start here](#start-here)
- [Try a small example](#try-a-small-example)
- [Save rules and continue](#save-rules-and-continue)
- [Natural-language examples after installation](docs/USAGE.md)
- [Download and install](#download-and-install)
- [Existing rules and generation prompts](#existing-rules-and-generation-prompts)
- [Prepare your data](#prepare-your-data)
- [Paper and author](#paper-and-author)

## Start here

After installation, say **“Start STCA”** and choose a task below. See the [natural-language examples](docs/USAGE.md) for complete conversations:

| Choice | Goal | A short request |
|---|---|---|
| **1 · Upload data and learn rules** | Learn rules and return their screening results | “Learn high thermal-conductivity rules from this data.” |
| **2 · Screen with existing rules** | Use bundled rules or your saved rules | “Screen this candidate table with existing rules.” |
| **3 · Generate with existing rules** | Choose rules, then preview and confirm the prompt or generate directly | “Generate 20 candidates directly with this rule.” |

The complete task prompts are built in. The AI assistant reads files, offers relevant sources and asks only for missing information. When learning rules, omitted percentages use Top or Bottom **10%, 20% and 30%** automatically; you can specify any percentage strictly between 0% and 100%, such as **15% and 25%**. You do not enter rule IDs or manage Python. Calculations use a CPU and support Python 3.10 or later; generation uses your current AI assistant.

## Try a small example

**Screen with an existing rule.** Use the bundled [five-candidate CSV](examples/quick_start/candidates.csv?raw=true), or ask directly:

```text
Use the bundled fluorinated-candidate example. Screen it with the RadonPy high-density Top 30% STCA rule and show every unmet rule condition.
```

This example returns three structural-rule matches and two non-matches, preserving the original star-containing SMILES.

**Learn rules from open data.** Download the [GAS Dataset A CSV](https://github.com/jsunn-y/PolymerGasMembraneML/blob/30981d71e1e3f12a057e009cd79f119bc659c7f5/datasets/datasetA_imputed_all.csv), upload it and ask:

```text
Learn high-CO₂-permeability rules from this measured data, in Barrer, for Top 10%, 20% and 30%. Automatically choose the data transform and scan step, return each tier's screening results and save the rules.
```

The assistant uses the original measured `CO2` column, prepares the data, returns rules and screening results, then saves them under My rules. The Bayesian and Etree imputed columns are not used as measured labels.

## Save rules and continue

With your own data, STCA automatically cleans unusable records, chooses data transforms and scan settings, and compares **STCA and WRAcc within your data range**. It returns both methods separately and names a primary and alternative for each tier, with the reason. The comparison uses **AS (Average Score), introduced and validated for screening evaluation in the author's [STCA paper](https://doi.org/10.1038/s41524-026-02345-x)**: `AS = (MCC + Precision + F1) / 3`. For evaluable comparisons, WRAcc becomes primary only when its CV AS exceeds STCA by more than 0.02. Say “Use the recommendation” to continue automatically, or specify either method.

After learning, it returns **both methods’ rules and corresponding screening results for every tier**: the percentage and its **numeric physical cutoff, ≥/≤ comparison and unit**, original SMILES, selection decisions, every unmet rule condition and uncomputable records. Cutoffs use the original physical scale even when learning uses log10. Results always cover the original uploaded table; a separate candidate table receives its own results.

The model, rules, physical cutoffs and complete bilingual generation prompts are saved under My rules. STCA shows the saved name and returns to the main menu. Choose **2** or **3** to reuse them.

![STCA workflow](assets/workflow.en.svg)

After you choose **3**, STCA **shows the available rule catalog first**, including bundled and loaded personal rules. Choose a source, property and percentage, then choose how to generate:

- **Preview and confirm**: view the complete prompt, adjust the candidate count, structural preferences or output format, then say “Confirm and generate.” The current LLM generates only after your confirmation.
- **Generate directly**: the current LLM uses the selected rules immediately to generate candidates and verify every proposal.

Both modes return the original proposals, star-containing SMILES, passed/failed decisions and every unmet rule condition, then return to the main menu. If your request already says “generate directly,” STCA uses that mode. Changes to the target or frozen rule conditions require choosing and confirming the corresponding rule. No additional LLM API setup is needed.

Say **“Main menu”** or **“Back”** at any time. Returning preserves saved rules. To use them on another device or platform, download the rule bundle and upload it in the new session.

## Download and install

ChatGPT and Codex use the same standalone skill package. See the [installation guide](docs/INSTALL.md).

| Platform | Download | Official guidance and invocation |
|---|---|---|
| **ChatGPT + Codex** | [OpenAI skill ZIP](downloads/stca-openai-skill-0.1.0.zip?raw=true) | [ChatGPT Skills help](https://help.openai.com/en/articles/20001066-skills-in-chatgpt/) · [Codex skill guide](https://learn.chatgpt.com/docs/build-skills). Select STCA in ChatGPT; say “Use $stca” in Codex. |
| **DeepSeek Harness** | [DeepSeek ZIP](downloads/stca-deepseek-harness-0.1.0.zip?raw=true) | [Product](https://www.deepseek.com/harness/) · [Install](docs/INSTALL.md#deepseek-harness). Enter `/stca`. |
| **WorkBuddy** | [WorkBuddy ZIP](downloads/stca-workbuddy-0.1.0.zip?raw=true) | [Official skill management](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market). Select STCA and describe the task. |

You can also ask Codex:

```text
Use $skill-installer to install https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

ChatGPT creation and import depend on account and workspace access. ChatGPT and Codex use the same skill contents; load them with the installation method supported by each client.

## Existing rules and generation prompts

The [rule and prompt directory](docs/RULE_LIBRARY.md) offers **source → property → percentage** choices. My rules contains the results learned from your own data. The open-data library covers **12 tasks**, each with Top **10%, 20% and 30%** and primary/alternative rules from two methods. Frozen Tg and electrical-conductivity rules from the author’s STCA paper are also included.

| Source | Properties |
|---|---|
| [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) | High Tg, low electrical conductivity, high electrical conductivity |
| [GAS measured data](https://github.com/jsunn-y/PolymerGasMembraneML) | CO₂ and O₂ permeability |
| [RadonPy computed data](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv) | Thermal conductivity, refractive index, density, specific heat, dielectric constant |
| [ADEPT computed data](https://github.com/sobinalosious/PolyGraphMT/tree/1c51a8578b6d23bd45bae7f7e175516dc22a3ed9/data/raw) | Thermal conductivity, density, isolated-monomer HOMO–LUMO gap, dielectric constant, refractive index |

The catalog shows each tier’s **method, primary/alternative status and numeric physical cutoff with its comparison and unit**. Accept the recommendation to use the primary directly, or specify either method; the two rule sets are applied separately. A percentage absent from the selected frozen catalog, such as 15% or 25% in the open-data library, requires labelled data to learn a new rule. Existing percentages are never interpolated or substituted. If you only want a prompt for another LLM, ask for the complete prompt without generation.

The Tg and electrical-conductivity rules implement the experimental-property screening tasks presented in the author’s STCA paper. STCA has also been used with the GAS, RadonPy and ADEPT datasets for rule extraction and screening validation across the 12 open-data tasks. Choose rules matching your objective, or learn from your own data. See the [rule directory](docs/RULE_LIBRARY.md#stca-paper-rules), [dataset sources](examples/open_data/dataset_registry.csv) and [application examples](examples/open_data/README.md).

## Prepare your data

Screening needs repeat-unit SMILES; learning also needs numeric property values:

```csv
CandidateKey,SMILES
sample-A7,*CC*
42-blue,*CCO*
```

Identifiers are optional and may have any name. Original `*` connection points are preserved; hydrogen capping is calculation-only. The AI assistant reads the table and asks only about unclear targets, units, experimental/computed origin or direction. You can preserve an existing data split.

## Paper and author

**Weihao Wang** — [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) · [Original implementation](https://github.com/foukusa/polymer-stca) · [Cite this software](CITATION.cff)

Try the [STCA simplified reproduction version on Code Ocean](https://doi.org/10.24433/CO.1601774.v1) to view the code and data and run the examples online.

[ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

<p align="center"><em>化繁为简，拨云见日</em></p>
