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

STCA works with polymer structure–property data and repeat units. After installation, say **“Start STCA”** or describe the task you want to complete. See the [natural-language examples](docs/USAGE.md) for complete conversations:

| Task | Goal | A short request |
|---|---|---|
| **Upload data and learn rules** | Learn rules and return their screening results | “Learn high thermal-conductivity rules from this data.” |
| **Screen with existing rules** | Use bundled rules or your saved rules | “Screen this candidate table with existing rules.” |
| **Generate with existing rules** | Choose rules, then preview and confirm the prompt or generate directly | “Generate 20 candidates directly with this rule.” |

STCA is a skill used by your AI assistant in the conversation. The task instructions are built in: describe what you need, attach your data when needed, and continue in natural language. The assistant reads files, offers relevant rules and asks only for missing information. When learning rules, omitted percentages use Top or Bottom **10%, 20% and 30%** automatically; you can specify any percentage strictly between 0% and 100%, such as **15% and 25%**. You do not enter rule IDs or manage Python. Calculations use a CPU and support Python 3.10 or later; generation uses your current AI assistant.

## Try a small example

**Screen with an existing rule.** Use the bundled [five-candidate CSV](examples/quick_start/candidates.csv?raw=true), or ask directly:

```text
Use the bundled fluorinated-candidate example. Screen it with the RadonPy high-density Top 30% STCA rule and show every unmet rule condition.
```

This example returns three structural-rule matches and two non-matches, preserving the original star-containing SMILES.

**Learn rules from open data.** Download [RadonPy’s PI1070 CSV](https://github.com/RadonPy/RadonPy/blob/db5732b7fdd0b656d9c06d89151066d1edfbe911/data/PI1070.csv), upload it and ask:

```text
Learn high-density rules from this RadonPy dataset, return the screening results and save the rules.
```

The assistant uses `smiles` for the polymer structures and `density` in g/cm³ for the calculated density. It prepares the data, chooses the data transform and scan step, and returns both methods’ rules and screening results for the default Top 10%, 20% and 30%. You can request other percentages.

## Save rules and continue

With your own data, STCA automatically cleans unusable records, chooses data transforms and scan settings, and compares **STCA and WRAcc within your data range**. It returns both methods separately and recommends one for each tier. The recommendation uses cross-validation: rules are repeatedly learned from part of the supplied data and evaluated on the remaining part. Its average screening score, introduced and validated in the author’s [STCA paper](https://doi.org/10.1038/s41524-026-02345-x), is the mean of the **Matthews correlation coefficient, precision and F1 score**; F1 combines precision and recall. The results explain the recommendation. Say “Use the recommended rule” to continue, or name either method. [Evaluation details](docs/USAGE.md).

After learning, it returns **both methods’ rules and corresponding screening results for every tier**: the percentage and its **numeric physical cutoff, ≥/≤ comparison and unit**, original SMILES, selection decisions, every unmet rule condition and uncomputable records. Cutoffs use the original physical scale even when learning uses log10. Results always cover the original uploaded table; a separate candidate table receives its own results.

The assistant saves the model, rules, physical cutoffs and complete bilingual generation prompts as files, and reports their names and locations. Continue by saying **“Use the rules you just saved to screen this table”** or **“Use the saved high-density rule to generate 20 repeat units.”** Download the rule bundle for use in a new session or on another platform; availability of local files depends on the current workspace.

![STCA workflow](assets/workflow.en.svg)

When you ask to generate with existing rules, STCA **shows the available rule catalog first**, including bundled rules and saved rule bundles loaded in the conversation. Choose a source, property and percentage, then choose how to generate:

- **Preview and confirm**: view the complete prompt, adjust the candidate count, structural preferences or output format, then say “Confirm and generate.” The current LLM generates only after your confirmation.
- **Generate directly**: the current LLM uses the selected rules immediately to generate candidates and verify every proposal.

Both modes return the original proposals and polymer SMILES, followed by the computed rule checks and unmet conditions. If calculation cannot run, the output identifies the proposals as awaiting verification. If your request already says “generate directly,” STCA uses that mode. Changes to the target or frozen rule conditions require choosing and confirming the corresponding rule. No additional LLM API setup is needed.

You can continue with another task directly, or say **“What can I do next?”** to see the available actions. To reuse saved rules on another device or platform, upload the rule bundle in the new conversation.

## Download and install

Choose your platform below. The [installation guide](docs/INSTALL.md) includes environment behavior and alternative installation paths.

| Platform | Installation route | Start |
|---|---|---|
| **Codex** | Install the GitHub skill folder or the [Codex ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-codex-0.1.0.zip?raw=true). | `Use $stca` |
| **DeepSeek Harness** | Add the GitHub repository as a plugin; use the npm package name after publication. | `/stca` |
| **WorkBuddy** | Import the [WorkBuddy ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-workbuddy-0.1.1.zip?raw=true). | “Start STCA” |
| **ChatGPT** | Import the [OpenAI skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-openai-skill-0.1.0.zip?raw=true) using a client with skill installation support. | Select STCA or ask to use it. |

### Codex

1. In Codex, send the installation request below.
2. After installation, type `$stca` to select STCA, or send “Use $stca to screen this candidate table.” Attach the table when needed.
3. For a manual installation, extract the Codex ZIP and put its complete `stca` folder at `~/.agents/skills/stca` (Windows: `%USERPROFILE%\.agents\skills\stca`). Keep `SKILL.md`, `scripts`, `references` and `assets` together.

```text
Use $skill-installer to install https://github.com/foukusa/stca-agent-skill/tree/main/skills/stca
```

### DeepSeek Harness

1. Open **Plugins → Add plugin**, enter `https://github.com/foukusa/stca-agent-skill.git`, then install and enable the plugin.
2. Enter `/stca` or say “Start STCA”. Describe your task and attach data where needed; continue in the same conversation.
3. After the npm package is published, the Add plugin field also accepts `dsh-plugin-stca`. Alternatively, download the [plugin TGZ](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/dsh-plugin-stca-0.1.0.tgz?raw=true) and enter its complete local path.

CLI installation with the `web` profile:

```bash
dsh plugin --profile web add github:foukusa/stca-agent-skill
```

After npm publication:

```bash
dsh plugin --profile web add dsh-plugin-stca
```

Replace `web` with the profile you use. A downloaded [DSH skill ZIP](https://github.com/foukusa/stca-agent-skill/blob/main/downloads/stca-deepseek-harness-0.1.0.zip?raw=true) is a different installation route: extract it and place the complete `stca` folder in your DSH skill root, normally `~/.dsh/skills/stca`, with the filesystem skill provider enabled. See the [DSH guide](README.DSH.md).

Plugin-center link: — (to be added after listing).

<!-- DSH_PLUGIN_CENTER_URL: add the actual listing URL after publication. -->

### WorkBuddy

1. Download `stca-workbuddy-0.1.1.zip` from the table above.
2. Open WorkBuddy’s skill management page and choose the action to add/upload a local skill package. Select the ZIP directly, complete import and enable **STCA Polymer Rules and Design**.
3. Say “Start STCA”, attach your file, then describe whether you want to learn rules, screen candidates or generate repeat units.

The marketplace installation link will be added after approval and publication.

### ChatGPT

1. Download `stca-openai-skill-0.1.0.zip` from the table above.
2. In a ChatGPT client that supports skill installation, use its import option or upload the package and ask to install the STCA skill.
3. Once STCA appears among the available skills, select it or say “Use STCA to screen this table.” Calculations require file access and code execution in that client. If skill installation is unavailable in your client, use one of the other platforms above.

### Downloading the files

The ZIP and TGZ links point to versioned files under the repository’s [`downloads` folder](https://github.com/foukusa/stca-agent-skill/tree/main/downloads). You can also open the [repository homepage](https://github.com/foukusa/stca-agent-skill), choose **Code → Download ZIP**, and extract it. The source contains `skills/stca`; platform packages are under `downloads` when included in that repository version. A source ZIP is extracted before folder-based installation; WorkBuddy’s upload accepts its platform ZIP directly.

At the first calculation, STCA looks for and checks a suitable local Python environment. You can use ordinary Python or a virtual environment; Conda is optional. The assistant needs access to your selected files, an output directory and local command execution. Preparing missing dependencies may access PyPI and the author’s public code repository; generation uses the current conversation’s LLM. See [environment behavior](docs/INSTALL.md#calculation-environment).

## Existing rules and generation prompts

The [rule and prompt directory](docs/RULE_LIBRARY.md) offers **source → property → percentage** choices. You can also load a rule bundle learned from your own data. The open-data library covers **12 tasks**, each with Top **10%, 20% and 30%** and primary/alternative rules from two methods. Frozen Tg and electrical-conductivity rules from the author’s STCA paper are also included.

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
