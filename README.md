<p align="center">
  <img src="assets/stca-logo.png" alt="STCA logo" width="104">
</p>

<h1 align="center">STCA Agent Skill</h1>

<p align="center">
  Interpretable polymer screening, rule extraction, and rule-guided candidate verification with Sliding Threshold Correlation Analysis.
</p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">简体中文</a>
</p>

> **Source repository and platform ZIPs are different things.** The GitHub `main` branch contains editable source code, including [`skills/stca/`](skills/stca/). Platform ZIPs are generated locally by the maintainer and may be attached to a GitHub Release or uploaded to a platform; they are not required in the source tree.

## Table of contents

- [What the skill does](#what-the-skill-does)
- [Quick start](#quick-start)
- [Identifiers and structure columns](#identifiers-and-structure-columns)
- [Install the skill](#install-the-skill)
  - [GitHub and skills.sh](#github-and-skillssh)
  - [ChatGPT and Codex](#chatgpt-and-codex)
  - [DeepSeek Harness](#deepseek-harness)
  - [WorkBuddy](#workbuddy)
- [How to invoke STCA](#how-to-invoke-stca)
- [Workflow 1: screen candidates with frozen rules](#workflow-1-screen-candidates-with-frozen-rules)
- [Workflow 2: extract rules from measured data](#workflow-2-extract-rules-from-measured-data)
- [Workflow 3: rule-guided candidate design](#workflow-3-rule-guided-candidate-design)
- [Command-line use](#command-line-use)
- [Scientific scope](#scientific-scope)
- [Citation and source](#citation-and-source)
- [License](#license)

## What the skill does

STCA Agent Skill wraps the original Sliding Threshold Correlation Analysis workflow for polymer repeat units. The host agent interprets the request, organizes files, invokes the scripts, and explains the outputs. The pinned `polymer-stca` implementation performs threshold scanning, substructure ranking, prefix-rule-family construction, frozen screening, and evaluation.

It supports three concrete workflows:

1. **Apply published STCA rules.** Screen repeat-unit candidates and report row-by-row pass/fail status, missing required MACCS keys, and forbidden keys that are unexpectedly present.
2. **Extract readable rules from measured data.** Run sliding-threshold analysis, retain the positive/negative prefix rule family, freeze a representative rule, and evaluate a separate holdout.
3. **Guide candidate design with frozen rules.** Export exact structural constraints, let the host agent propose candidates, and explicitly verify every proposal.

For multi-property requests, each property retains its own direction and tier. STCA does not force Tg, EC, TC, and other properties onto one numerical scale; it applies the corresponding rules separately and reports their same-candidate intersection.

## Quick start

### A. Screen a candidate CSV

A candidate file may use **any identifier column name and arbitrary text values**:

```csv
CandidateKey,SMILES
sample-A7,*c1ccc(cc1)C(=O)N*
42-blue,*Oc1ccc(cc1)O*
```

The identifier is bookkeeping only. It is never used as a model feature. You may also omit an identifier column entirely; the screening wrapper then generates stable receipt IDs such as `row-000001` without changing the source file.

Invoke the skill with a request such as:

```text
Use the STCA skill to screen candidates.csv for high Tg and bottom-5% electrical conductivity.
The identifier column is CandidateKey and the repeat-unit column is SMILES.
Keep the original star-containing SMILES in the final results, use H-cap only for MACCS calculation,
apply the frozen paper rules, report each failed condition, and save the outputs in out/screening.
```

### B. Extract rules from measured data

```text
Use the STCA skill on measured_tg.csv.
RecordKey is only a row identifier; SMILES contains the repeat unit and Tg_degC contains the measurement.
Audit duplicate structures and split overlap, extract the complete STCA rule family on the source set,
freeze the representative rule, and evaluate the independent holdout.
Do not assume the row identifier is a material grouping key.
```

### C. Propose and verify candidates

```text
Use the STCA skill to export structural constraints for high thermal stability and low EC.
Propose 20 repeat units with two connection points, retain every raw proposal,
use a temporary H-cap copy for MACCS calculation, and present the original star-containing structures
in the final pass/fail table. Do not describe rule compliance as measured-property confirmation.
```

## Identifiers and structure columns

### Identifier column

- `PID` is **not required**.
- Candidate identifiers can be arbitrary strings such as `CandidateKey`, `Name`, `RecordID`, or user-provided labels.
- The column name is supplied through `--id-column` or `id_column` in JSON.
- For candidate screening, the identifier must be nonempty and unique if a column is supplied.
- If no identifier column is supplied, `screen-candidates` and `joint-screen` generate receipt IDs from row order.
- Identifier values are never used as MACCS features or STCA variables.

### Row identifier versus split/group key

A random row identifier is not automatically a scientifically meaningful grouping key. When creating a leakage-controlled source/holdout split, use a separate group such as a canonical repeat-unit structure, a real material identity, or another defensible grouping variable. Do not use arbitrary random IDs to claim material-disjoint evaluation.

### H-cap and final structures

The original STCA representation uses H-cap before MACCS calculation. This skill therefore follows this sequence:

```text
original repeat-unit SMILES with *
        ↓ preserve unchanged
calculation-only H-cap copy
        ↓
MACCS and frozen STCA rules
        ↓
final results show the original star-containing SMILES
```

The skill does **not** attempt to infer connection points by reverse-converting an H-capped molecule; that information is lossy. Instead, the original input is retained from the beginning and restored as the primary presentation structure. The full audit file may also contain the H-cap calculation copy.

## Install the skill

### GitHub and skills.sh

Install directly from the public source repository:

```bash
npx skills add foukusa/stca-agent-skill --skill stca
```

This reads `skills/stca/` from the repository and does **not** require a ZIP in the `main` branch.

You can also clone and copy the skill directory into another Agent Skills host:

```bash
git clone https://github.com/foukusa/stca-agent-skill.git
cp -R stca-agent-skill/skills/stca /your/agent/skills/stca
```

### ChatGPT and Codex

**Users:** after the STCA plugin is published, install it from the Plugins directory. Start a new chat, type `@STCA`, attach the input file, and state the target property, direction, tier, and relevant columns.

**Maintainers:** build the OpenAI package locally:

```bash
python3 tools/build_packages.py --output-dir "$HOME/Desktop/STCA-release-0.1.0"
```

Upload this generated file to the OpenAI plugin portal:

```text
STCA-release-0.1.0/stca-openai-plugin-0.1.0.zip
```

The ZIP is a release artifact. It is not expected to exist in the GitHub source tree.

### DeepSeek Harness

Install directly from source on macOS:

```bash
git clone https://github.com/foukusa/stca-agent-skill.git
mkdir -p "$HOME/.dsh/skills"
rm -rf "$HOME/.dsh/skills/stca"
cp -R stca-agent-skill/skills/stca "$HOME/.dsh/skills/stca"
```

Invoke it in Harness with:

```text
/stca Screen candidates.csv with the paper low-EC 5% rule. Use CandidateKey as the identifier,
H-cap only for calculation, and return the original repeat-unit SMILES with each failed condition.
```

A maintainer may additionally attach `stca-deepseek-harness-0.1.0.zip` to a GitHub Release for users who prefer a ready-made package.

### WorkBuddy

**Users:** install the published STCA skill from the WorkBuddy skill market. For local testing, import the maintainer-built package through **Add skill → Upload skill**.

**Maintainers:** the same build command creates:

```text
STCA-release-0.1.0/stca-workbuddy-0.1.0.zip
```

After enabling it, invoke it explicitly in a task:

```text
Use the STCA skill to screen this polymer table for high Tg and low EC.
The identifier column is SampleName. Preserve the original SMILES in the final output and save all result files to the workspace.
```

## How to invoke STCA

| Host | Explicit invocation | Example |
| --- | --- | --- |
| ChatGPT / ChatGPT Work | Type `@STCA` and select the plugin or skill | `@STCA Screen the attached candidates with the low-EC 5% rule.` |
| Codex | Select or mention the installed STCA skill | `Use $stca to audit and screen candidates.csv.` |
| DeepSeek Harness | Type `/stca` | `/stca Extract and freeze rules from measured_td.csv.` |
| WorkBuddy | Enable STCA and name it in the task | `Use the STCA skill to verify these generated candidates.` |
| Other Agent Skills hosts | Explicitly request STCA | `Use STCA and follow the H-cap/frozen-rule workflow.` |

A useful request should identify:

- the input file;
- the original repeat-unit SMILES column;
- the optional identifier column, if present;
- property and direction, such as high Tg or low EC;
- tier or strictness, such as `0.05`, `strict`, or `extreme`;
- whether to apply published rules or learn rules from measured data;
- the desired output directory or report format.

## Workflow 1: screen candidates with frozen rules

**Input:** original repeat-unit SMILES or a validated 167-bit MACCS matrix.

**Processing:**

1. Preserve the original row and original repeat-unit SMILES.
2. H-cap supported terminal single-bond `*` connection points in a calculation-only copy.
3. Compute 167-bit RDKit MACCS with the K0 placeholder retained.
4. Load the selected frozen STCA profile and tier.
5. Evaluate all required-present and required-absent conditions.
6. Preserve invalid rows as unknown/error rows rather than treating them as true negatives.

**Primary output:** `results.csv`, which presents the original star-containing repeat-unit SMILES.

**Audit output:** `rows.csv`, which additionally records the H-cap calculation structure and representation details.

Published profiles:

- `tg-high`: tiers `0.30`, `0.20`, `0.10`;
- `ec-low`: tiers `0.20`, `0.15`, `0.10`, `0.05`;
- `ec-high`: tiers `0.20`, `0.15`, `0.10`, `0.05`.

## Workflow 2: extract rules from measured data

**Input:** structures, measured property, unit, data role, and optional row/group columns.

**Processing:**

1. Audit invalid structures, repeated measurements, representation collisions, and cross-set overlap.
2. Scan property thresholds on the source data.
3. Correlate each substructure-frequency trajectory with the moving threshold.
4. Rank positive and negative MACCS keys separately.
5. Construct the original positive-only, negative-only, and mixed prefix rule family.
6. Select and freeze a representative under the declared protocol.
7. Evaluate data that did not participate in rule selection.

**Output:** scan trajectories, rankings, the complete rule family, frozen `model.json`, selection diagnostics, and holdout metrics.

The row identifier column may be arbitrary or omitted. A separate scientifically meaningful group key must be used when group-disjoint splitting is required.

## Workflow 3: rule-guided candidate design

**Input:** frozen rules, candidate budget, connection-point format, allowed chemistry, and design objectives.

**Processing:**

1. Export exact structural constraints.
2. Let the host agent propose the requested number of repeat units.
3. Retain every raw proposal and original star-containing SMILES.
4. Create a temporary H-cap calculation structure.
5. Compute MACCS and verify every frozen rule.
6. Report pass/fail state and exact failure conditions.
7. For multiple objectives, evaluate each rule separately before computing the same-candidate intersection.

**Output:** original proposals, full audit records, per-rule results, failure conditions, and the final intersection. Rule compliance is not an experimental property measurement or a synthesis guarantee.

## Command-line use

The simplest single-rule candidate command accepts raw star-containing structures and automatically restores the original structure in `results.csv`:

```bash
export SKILL_DIR="$PWD/skills/stca"
export STCA_ENV_DIR="$HOME/.venvs/stca-0.1.0"

python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR" > stca-setup.json

STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"

"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --profile ec-low \
  --protocol paper \
  --tier 0.05 \
  --input candidates.csv \
  --id-column CandidateKey \
  --smiles-column SMILES \
  --output-dir out/ec-low-05
```

Omit `--id-column CandidateKey` when no identifier column is present; the wrapper generates receipt IDs. The original `SMILES` remains in `results.csv`; H-cap details are retained in `rows.csv`.

For multiple objectives, use an objective file whose identifier field is optional and whose structure field is the original repeat-unit column:

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "CandidateKey",
  "smiles_column": "SMILES",
  "hcap_before_maccs": true,
  "objectives": [
    {"property": "Tg", "direction": "high", "strictness": "standard"},
    {"property": "EC", "direction": "low", "strictness": "extreme"}
  ]
}
```

More commands and data contracts are documented in [`skills/stca/references/commands.md`](skills/stca/references/commands.md).

## Scientific scope

- STCA is a transparent screening and rule-extraction method, not a numerical property predictor.
- A structure that passes a frozen rule is **rule-compliant**, not experimentally confirmed.
- Multi-property screening is the intersection of separately defined structural rules. Joint measured-property performance requires paired labels under comparable conditions.
- The original STCA prefix-family construction is preserved; the skill does not replace it with arbitrary combinatorial or beam search.
- The paper protocol and source-locked external-evaluation protocol are reported separately.
- H-cap is a representation step for calculation; the original repeat-unit structure remains the authoritative output structure.

## Citation and source

- **Paper:** [Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design](https://doi.org/10.1038/s41524-026-02345-x)
- **Original implementation:** [foukusa/polymer-stca](https://github.com/foukusa/polymer-stca)
- **Software citation metadata:** [`CITATION.cff`](CITATION.cff)

## License

Read [`LICENSE`](LICENSE), [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), and [`PUBLISHER_LICENSE_NOTES.md`](PUBLISHER_LICENSE_NOTES.md) before redistribution. The agent-skill integration, original STCA implementation, logo, and any bundled data may have different applicable terms.
