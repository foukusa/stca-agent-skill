<p align="center"><img src="assets/stca-logo.png" alt="STCA logo" width="104"></p>
<h1 align="center">STCA Agent Skill</h1>
<p align="center">Learn polymer structure–property rules, screen candidates, or generate repeat units.</p>
<p align="center"><strong>0.1.0</strong> · English · <a href="README.zh-CN.md">简体中文</a></p>

## Contents

- [Start here](#start-here)
- [Try a small example](#try-a-small-example)
- [Save rules and continue](#save-rules-and-continue)
- [Natural-language examples after installation](docs/USAGE.md)
- [Download and install](#download-and-install)
- [DeepSeek Harness guide](README.DSH.md)
- [Existing rules and generation prompts](#existing-rules-and-generation-prompts)
- [Prepare your data](#prepare-your-data)
- [Paper and author](#paper-and-author)

## Start here

STCA works with polymer structure–property data and repeat units. After installation, say **“Start STCA”** and choose a task below. See the [natural-language examples](docs/USAGE.md) for complete conversations:

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

Both modes return the original proposals, molecular SMILES, passed/failed decisions and every unmet rule condition, then return to the main menu. If your request already says “generate directly,” STCA uses that mode. Changes to the target or frozen rule conditions require choosing and confirming the corresponding rule. No additional LLM API setup is needed.

Say **“Main menu”** or **“Back”** at any time. Returning preserves saved rules. To use them on another device or platform, download the rule bundle and upload it in the new session.

## Download and install

Install directly from GitHub or a downloaded package. Store listing links will be added after approval. See the [installation guide](docs/INSTALL.md) for the complete steps.

| Platform | Install | Start |
|---|---|---|
| **Codex** | Ask `$skill-installer` to install the [STCA skill folder](https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca), or download the [Codex skill ZIP](downloads/stca-codex-0.1.0.zip?raw=true). | `Use $stca` |
| **DeepSeek Harness** | Enter the GitHub URL in Add plugin, or use `dsh-plugin-stca` after its npm publication. See the plugin-center entry below. A [local skill ZIP](downloads/stca-deepseek-harness-0.1.0.zip?raw=true) is also available. | `/stca` |
| **WorkBuddy** | Import the [WorkBuddy ZIP](downloads/stca-workbuddy-0.1.1.zip?raw=true) as a local skill. | Select STCA and say “Start STCA”. |
| **ChatGPT desktop** | Use the [OpenAI skill ZIP](downloads/stca-openai-skill-0.1.0.zip?raw=true) with the skill installation options available in your app. | Select STCA. |

In Codex, send:

```text
Use $skill-installer to install https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

In DeepSeek Harness, open **Plugins → Add plugin** and choose an installation source:

| Source | Value or entry |
|---|---|
| **GitHub repository** | `https://github.com/foukusa/stca-agent-skill.git` |
| **npm package name** | `dsh-plugin-stca` (available after npm publication) |
| **Plugin center** | — (listing link will be added after publication) |

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

You can also download the [plugin TGZ](downloads/dsh-plugin-stca-0.1.0.tgz?raw=true) and enter its full local path in Add plugin. After installation and activation, enter `/stca`.

For GitHub installation with the DSH CLI and the `web` profile:

```bash
dsh plugin --profile web add github:foukusa/stca-agent-skill
```

After the npm package is published, install by package name:

```bash
dsh plugin --profile web add dsh-plugin-stca
```

`web` is an example profile; replace it with the profile you use. The [DSH guide](README.DSH.md) covers installation, first use, permissions and licensing. STCA needs access to the files you select, an output directory and local command execution. Dependency preparation can contact PyPI and the author's public code repository; generation uses the current DSH conversation's LLM. Conda is optional.

The first calculation automatically looks for and checks a suitable local Python environment. A Python path is an optional fallback, not an installation requirement. See [environment behavior](docs/INSTALL.md#calculation-environment). Codex can use the standalone skill immediately; a public OpenAI directory listing is a separate publication route.

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

Screening needs polymer repeat-unit SMILES; learning also needs numeric property values:

```csv
CandidateKey,SMILES
sample-A7,*CCO*
42-blue,*CC*
```

Identifiers are optional and may have any name. Original polymer SMILES and attachment points such as `*CCO*` are preserved; hydrogen capping applies only to a calculation copy. Already capped input is kept as supplied. Choose existing rules for their stated property and source, or learn new rules from your polymer data. The AI assistant reads the table and asks only about unclear targets, units, experimental/computed origin or direction. You can preserve an existing data split.

For example, with a polymer thermal-conductivity table, ask:

```text
Learn high-thermal-conductivity rules from this polymer dataset, return the screening results and save the rules. Then use the recommended rule to directly generate and verify 20 polymer repeat units.
```

## Paper and author

**Weihao Wang** — [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) · [Original implementation](https://github.com/foukusa/polymer-stca) · [Cite this software](CITATION.cff)

Try the [STCA simplified reproduction version on Code Ocean](https://doi.org/10.24433/CO.1601774.v1) to view the code and data and run the examples online.

[ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

The source is publicly available under the **STCA Agent Skill Academic Use License** for non-commercial academic research, education and scientific reproduction. Commercial use and redistribution require prior written permission. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

<p align="center"><em>“Out of clutter, find simplicity.”</em><br><sub>— attributed to Albert Einstein</sub></p>
