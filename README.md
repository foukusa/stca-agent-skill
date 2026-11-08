<p align="center"><img src="assets/stca-logo.png" alt="STCA logo" width="104"></p>
<h1 align="center">STCA Agent Skill</h1>
<p align="center">Choose polymer structure rules, learn new rules from your data, and turn them into prompts for molecular design.</p>
<p align="center"><strong>0.1.0</strong> · English · <a href="README.zh-CN.md">简体中文</a></p>

## Contents

- [77 ready-made rules and 154 generation prompts](docs/RULE_LIBRARY.md)
- [Choose your task](#choose-your-task)
- [Install and invoke](#install-and-invoke)
- [Prepare your input](#prepare-your-input)
- [1. Select built-in rules and screen candidates](#1-select-built-in-rules-and-screen-candidates)
- [2. Learn rules from your CSV](#2-learn-rules-from-your-csv)
- [3. Get a prompt for candidate generation](#3-get-a-prompt-for-candidate-generation)
- [What you receive](#what-you-receive)
- [More examples](#more-examples)
- [Paper and author](#paper-and-author)
- [License](#license)

## Choose your task

STCA — **Sliding Threshold Correlation Analysis** — turns polymer property data into readable substructure rules. This agent skill lets you use those rules through natural-language requests.

| I want to… | Provide | Ask STCA to… |
|---|---|---|
| Screen with an existing rule | Candidate CSV and your selected built-in rule | Return matching repeat units and each failed condition |
| Learn rules for my property | Labeled CSV, target, unit, direction and percentages | Automatically learn reusable rules and export a generation prompt |
| Design from rules | A built-in rule or one you just learned | Give you a copyable prompt for this LLM or another LLM, then verify the returned candidates |

The package includes **77 frozen rules and 154 English/Chinese generation prompts**: 11 paper rules, five tiers for each of 13 public-data property tasks (65 rules), and one author-supplied monomer-gap rule. Open the [ready-made rule and prompt directory](docs/RULE_LIBRARY.md) to choose a property and copy its prompt. RadonPy is a polymer molecular-simulation data source; ADEPT is an MD/DFT computational data source.

Every function can be requested in natural language: choose rules, screen candidates, learn new rules, export prompts, generate structures and verify them. The agent reuses or prepares the backend automatically. STCA calculations use a CPU, and generation uses the current host LLM; users do not configure Python, a GPU or a separate model deployment.

You can combine several rules on the same candidate file, with a separate direction and percentage for every property.

## Install and invoke

Get the files from [this GitHub repository](https://github.com/foukusa/stca-agent-skill): choose **Code → Download ZIP**, then double-click the downloaded ZIP in Mac Finder. Open the extracted repository and locate the [complete STCA skill](skills/stca) at `skills/stca`. A host that accepts local skill directories can load that complete `stca` folder.

If you received a platform-specific STCA distribution package, use that package in the host’s supported skill import entry. If an entry requires ZIP, Finder’s **Compress “stca”** creates a ZIP from the complete `stca` folder. Enable STCA after loading it; the host agent handles calculation dependencies and supporting tools.

In ChatGPT, select STCA directly if it is already installed. Personal-skill installation follows the interface available to your account or workspace. The ChatGPT plugin distribution package is a publication package; uploading it into an ordinary chat is not a personal-skill installation method.

| Platform | Start a request |
|---|---|
| ChatGPT with STCA installed | Select STCA, then write `Use STCA…` |
| Codex | Write `Use $stca…` |
| DeepSeek Harness, a skill-capable agent host | Load STCA, then write `/stca …` |
| WorkBuddy | Import and enable the STCA skill, then write `Use the STCA skill…` |

A generated text prompt can be used in any LLM. Learning rules and checking structures take place in a host with STCA enabled.

## Prepare your input

For screening, upload a CSV containing the original repeat-unit SMILES:

```csv
CandidateKey,SMILES
sample-A7,*CC*
42-blue,*CCO*
```

IDs are optional and may have any name or value. STCA keeps your original `*` connection points; hydrogen capping is only a temporary calculation step.

For learning, upload a CSV with a structure column and numeric property values, then tell the skill:

- The structure and property column names.
- The property unit and whether the labels are experimental or computed.
- Whether you want **high** or **low** values.
- Your percentage or percentage list, such as Top 10%, 15% and 20%.

`high/low` selects the direction; the percentage selects the target range. Each property has its own choices. If your table already has a training/test split, tell STCA the column and labels to preserve.

## 1. Select built-in rules and screen candidates

Start by asking for the rules actually included in your installed version:

```text
List STCA's built-in rule sets. For each, show the dataset, property,
high/low direction and available percentages, so I can choose one.
```

Choose a listed rule and upload your candidates. For example:

```text
Use STCA's published rules to screen my uploaded candidates.csv.
Select high Tg at Top 20% and low electrical conductivity at Bottom 10%.
The structure column is SMILES; CandidateKey is an optional identifier.
Return candidates satisfying both rules, each individual decision and every failed condition.
Keep the original star-containing SMILES and return the results as a file.
```

Published options include high Tg at Top 30%/20%/10%, low electrical conductivity at Bottom 20%/15%/10%/5%, and high electrical conductivity at Top 20%/15%/10%/5%. CO2, O2, RadonPy’s five properties and ADEPT’s six properties also come with high-value Top 10%/15%/20%/25%/30% rules. The [rule directory](docs/RULE_LIBRARY.md) provides every choice and its English/Chinese prompts. Use the next workflow to create a rule for a new target.

## 2. Learn rules from your CSV

Upload your property table and ask:

```text
Use STCA to learn rules from my uploaded permeability.csv.
The structure column is SMILES; the target is CO2Permeability in Barrer.
These are experimental measurements. I want high values.
Explore Top 10%, 15%, 20%, 25% and 30%.
Automatically prepare the data and select suitable scaling, scan step and rule settings.
Return all requested rule sets, their physical cutoffs, the recommended usable range,
a reusable model and a copyable candidate-generation prompt.
```

The skill manages automatic preparation, ECFP4-based data splitting and settings chosen from training data. The host manages calculation and model reuse. STCA preserves your original data and reports excluded records and any unavailable rules. Complete generation prompts are returned with the learned rules and model, without a separate export step.

To screen later, refer to the model by the task you just completed:

```text
Use the high-CO2-permeability rules we just learned, at Top 15%,
to screen my uploaded new_candidates.csv using its SMILES column.
Return original structures, matching candidates and every failed condition.
```

The percentage list is yours to choose. If a narrow range is unsuitable, STCA can inspect the other ranges you requested. For multiple properties, learn a model for each—for example, high thermal conductivity and low density—then request their intersection on the same candidates.

## 3. Get a prompt for candidate generation

You can start directly from an existing rule, without a new training CSV:

```text
Use STCA's high-Tg Top 20% rule and low-electrical-conductivity Bottom 10% rule.
Give me a complete prompt I can copy into another LLM to generate 20 polymer repeat units.
Include the actual structural conditions, two terminal * connection points,
and a CSV output format with CandidateKey and SMILES.
Return the generation prompt as text and as a downloadable file.
```

Or use a rule you just learned:

```text
Turn the high-CO2-permeability Top 15% rule we just learned into a generation prompt.
Ask for 20 candidate repeat units with two terminal * connection points.
Include every rule condition and the expected output format, ready to copy into another LLM.
```

Paste the prompt into the current LLM or another LLM. Bring the generated CSV back to the STCA-enabled host and ask:

```text
Check my uploaded generated_candidates.csv against the rules used in that generation prompt.
Verify each candidate, preserve the original SMILES, and return matching structures
with every passed and failed condition.
```

You can also generate and verify in the current host with one request:

```text
Use STCA's gas-co2-high-15 rule to generate 20 distinct polymer repeat units.
Prepare the generation prompt automatically and verify every proposal.
Return the original star-containing SMILES, passing candidates and every failed condition.
```

The LLM proposes structures, STCA checks rule compliance, and the agent handles the intermediate steps.

## What you receive

- A candidate table with original SMILES, rule decisions and failed conditions.
- Readable rules and the property cutoffs for your selected percentages.
- A reusable model when you learn rules from data.
- A complete generation prompt to copy or download.

The agent returns the files for the task you requested and can reuse the selected rules in follow-up requests.

## More examples

See [more application examples](examples/open_data/README.md) for available dataset rules, gas membranes, thermal, optical, density, specific-heat, dielectric and monomer-orbital-gap tasks. It also provides public data sources and fields for learning your own rules.

## Paper and author

**Weihao Wang** — [STCA paper](https://doi.org/10.1038/s41524-026-02345-x) · [Original implementation](https://github.com/foukusa/polymer-stca) · [Cite this software](CITATION.cff)

[ORCID](https://orcid.org/0009-0005-4445-7074) · [ResearchGate](https://www.researchgate.net/profile/Weihao-Wang-23) · [Google Scholar](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)

## License

See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
