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

## Contents

- [What STCA does](#what-stca-does)
- [Two operating modes](#two-operating-modes)
- [Published profiles and percentage tiers](#published-profiles-and-percentage-tiers)
- [Quick start](#quick-start)
- [Input conventions](#input-conventions)
- [Install and invoke](#install-and-invoke)
- [Workflow 1: apply published rules](#workflow-1-apply-published-rules)
- [Workflow 2: derive rules from your own data](#workflow-2-derive-rules-from-your-own-data)
- [Workflow 3: rule-guided candidate design](#workflow-3-rule-guided-candidate-design)
- [Command-line examples](#command-line-examples)
- [Outputs](#outputs)
- [Scientific scope](#scientific-scope)
- [Paper, source, and author profiles](#paper-source-and-author-profiles)
- [License](#license)

## What STCA does

STCA Agent Skill wraps the original Sliding Threshold Correlation Analysis workflow for polymer repeat units. The host agent interprets the request, organizes files, invokes the scripts, and explains the outputs. The pinned `polymer-stca` implementation performs threshold scanning, MACCS substructure ranking, prefix-rule-family construction, frozen screening, and evaluation.

The skill supports three functions:

1. **Apply published STCA rules** to a new candidate table and report row-by-row pass/fail results and failed structural conditions.
2. **Derive new readable rules from a user's measured dataset** using user-defined percentage thresholds.
3. **Guide candidate design with frozen rules**, then verify every proposed repeat unit explicitly.

## Two operating modes

### 1. Published-rule mode

Use the frozen conclusions reported in the STCA paper. These rules retain the provenance of the paper's **ECFP2-based interpolation/extrapolation split**. Applying a published rule to a new candidate library does not require re-splitting that library and does not retrain the rule.

Use this mode when the goal is:

- to apply the paper's existing Tg or EC structural rules to new candidates;
- to reproduce a published profile and percentage tier;
- to export a published rule as an executable design constraint.

### 2. Custom-data mode

Use a new measured dataset to derive a new STCA rule family. The user explicitly supplies:

- the measured property and unit;
- the target direction or EC regime;
- the percentage threshold or thresholds;
- the source and evaluation roles, when independent evaluation is required.

The resulting rules are **custom rules derived from that dataset**, not the frozen rules of the paper. A random row identifier is never treated as a scientific split variable.

## Published profiles and percentage tiers

The percentage tier is an explicit part of every published screening task. It is not replaced by vague labels such as “standard” or “extreme.”

| Published profile | Meaning | Available tiers |
| --- | --- | --- |
| `tg-high` | high-Tg branch | top 30%, top 20%, top 10% |
| `ec-low` | low-EC / insulation regime | bottom 20%, bottom 15%, bottom 10%, bottom 5% |
| `ec-high` | high-EC / conduction regime | top 20%, top 15%, top 10%, top 5% |

For the published profiles, Tg has a high-performance branch. The two-way **high/low distinction is mainly used for EC**, where `ec-low` denotes insulation and `ec-high` denotes conduction. The percentage tier is specified separately.

A 5% tier is therefore only one available EC tier. It is not the default and should only be used when the user explicitly selects it.

## Quick start

### A. Apply published rules to candidates

Example input:

```csv
CandidateKey,SMILES
sample-A7,*c1ccc(cc1)C(=O)N*
42-blue,*Oc1ccc(cc1)O*
```

Example request with independently chosen percentage tiers:

```text
Use STCA in published-rule mode to screen candidates.csv.
Apply the Tg top-20% rule and the low-EC bottom-10% rule.
CandidateKey is an optional row label and SMILES contains the original repeat unit.
Keep the original star-containing SMILES in the final results, use H-cap only for MACCS calculation,
report every failed rule condition, and save the outputs in out/screening.
```

### B. Derive rules from measured data

```text
Use STCA in custom-data mode on measured_ec.csv.
SMILES contains the repeat unit and EC_S_cm contains measured conductivity.
Derive low-EC rules for the user-defined bottom-20%, bottom-15%, and bottom-10% thresholds.
Use the source/evaluation roles already provided in the Role column, freeze each selected rule,
and report evaluation metrics separately. Do not treat the row identifier as a split variable.
```

### C. Propose and verify candidates

```text
Use STCA to export the published Tg top-20% and low-EC bottom-10% structural constraints.
Propose 20 repeat units with two connection points, retain every raw proposal,
create an H-cap calculation copy for MACCS, and return the original star-containing structures
with the pass/fail result and every failed condition.
```

## Input conventions

### Identifier column

- `PID` is not required.
- An identifier column is optional and may have any name, such as `CandidateKey`, `Name`, or `RecordID`.
- Identifier values are bookkeeping only. They are never used as MACCS features or STCA variables.
- If no identifier is supplied, the wrapper generates row receipts such as `row-000001` without modifying the source file.
- In custom-data mode, source/evaluation roles must be supplied explicitly; arbitrary identifiers do not define the split.

### H-cap and final structures

The original repeat-unit SMILES is preserved from the beginning. H-cap is created only as a calculation copy:

```text
original repeat-unit SMILES with *
        ├── retained unchanged for reporting
        └── temporary H-cap copy
                    ↓
                 MACCS
                    ↓
               STCA rule
                    ↓
final results show the original star-containing SMILES
```

The skill does not attempt to reconstruct connection points from an H-capped molecule. `results.csv` presents the original repeat unit; the audit output may additionally record the temporary H-cap structure.

## Install and invoke

### GitHub and skills.sh

Install directly from the repository:

```bash
npx skills add foukusa/stca-agent-skill --skill stca
```

Then invoke the installed skill explicitly in a compatible Agent Skills host:

```text
Use STCA in published-rule mode. Apply Tg top 20% and EC-low bottom 10% to candidates.csv.
```

### ChatGPT and Codex

After the STCA plugin is published, install it from the plugin directory.

- **ChatGPT:** start a new chat, type `@STCA`, attach the input file, and state the mode, property profile, and percentage tier.
- **Codex:** select the installed STCA skill or mention `$stca` explicitly.

Example:

```text
@STCA Apply the published Tg top-20% rule to the attached candidate table and list every failed condition.
```

### DeepSeek Harness

Clone the repository and copy the skill directory:

```bash
git clone https://github.com/foukusa/stca-agent-skill.git
mkdir -p "$HOME/.dsh/skills"
rm -rf "$HOME/.dsh/skills/stca"
cp -R stca-agent-skill/skills/stca "$HOME/.dsh/skills/stca"
```

Invoke it with `/stca`:

```text
/stca Apply the published EC-low bottom-10% rule to candidates.csv. Preserve the original repeat-unit SMILES and report failed conditions.
```

### WorkBuddy

Install STCA from the WorkBuddy skill market, enable it in the task, and name it explicitly:

```text
Use the STCA skill in custom-data mode to derive Tg rules at the top-30%, top-20%, and top-10% thresholds from measured_tg.csv.
```

## Workflow 1: apply published rules

**Input:** original repeat-unit SMILES or a validated 167-bit MACCS matrix.

**Required choices:**

- published profile: `tg-high`, `ec-low`, or `ec-high`;
- explicit percentage tier supported by that profile.

**Processing:**

1. Preserve the original row and original repeat-unit SMILES.
2. H-cap supported terminal single-bond `*` connection points in a calculation-only copy.
3. Compute 167-bit RDKit MACCS with the K0 placeholder retained.
4. Load the frozen paper rule for the selected profile and tier.
5. Evaluate every required-present and required-absent condition.
6. Preserve invalid structures as unknown/error rows rather than treating them as true negatives.

No new training split is created in this workflow. The rule is the frozen paper conclusion and is applied directly to the user's candidate set.

## Workflow 2: derive rules from your own data

**Input:** repeat-unit structures, measured property, unit, explicit percentage thresholds, and source/evaluation roles when evaluation is requested.

**Processing:**

1. Audit invalid structures, repeated measurements, representation collisions, and role overlap.
2. Scan the user-defined property thresholds on the source data.
3. Correlate each substructure-frequency trajectory with the moving threshold.
4. Rank positive and negative MACCS keys separately.
5. Construct the original positive-only, negative-only, and mixed prefix rule family.
6. Select and freeze a representative rule using only the declared source role.
7. Evaluate the frozen rule on the declared evaluation role.

The user may define any scientifically meaningful percentage thresholds supported by the data. These rules belong to the new dataset. They must not be presented as reproduction of the published ECFP2 split unless the original paper data roles are actually used.

## Workflow 3: rule-guided candidate design

**Input:** one or more frozen rules, explicit percentage tiers, candidate budget, connection-point format, and allowed chemistry.

**Processing:**

1. Export exact required-present and required-absent constraints.
2. Let the host agent propose the requested number of repeat units.
3. Retain every raw proposal and original star-containing SMILES.
4. Create a temporary H-cap calculation structure.
5. Compute MACCS and verify every frozen rule.
6. Report pass/fail state and exact failed conditions.
7. For multiple objectives, evaluate each rule separately before computing the same-candidate intersection.

Rule compliance is not an experimental property measurement or a synthesis guarantee.

## Command-line examples

### Apply one published rule

```bash
export SKILL_DIR="$PWD/skills/stca"
export STCA_ENV_DIR="$HOME/.venvs/stca-0.1.0"

python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR" > stca-setup.json

STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"

"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" screen-candidates \
  --profile tg-high \
  --protocol paper \
  --tier 0.20 \
  --input candidates.csv \
  --id-column CandidateKey \
  --smiles-column SMILES \
  --output-dir out/tg-top20
```

Omit `--id-column CandidateKey` when the table has no identifier column.

### Plan a multi-rule screen with explicit tiers

```json
{
  "schema": "stca-objectives-v1",
  "id_column": "CandidateKey",
  "smiles_column": "SMILES",
  "hcap_before_maccs": true,
  "objectives": [
    {"property": "Tg", "direction": "high", "tier": 0.20},
    {"property": "EC", "direction": "low", "tier": 0.10}
  ]
}
```

```bash
"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" plan-objectives \
  --objectives objectives.json \
  --output-dir out/objective-plan

"$STCA_PY" "$SKILL_DIR/scripts/stca_tools.py" joint-screen \
  --input candidates.csv \
  --config out/objective-plan/joint_config.json \
  --output-dir out/joint-screen
```

More commands are documented in [`skills/stca/references/commands.md`](skills/stca/references/commands.md).

## Outputs

| File | Purpose |
| --- | --- |
| `results.csv` | primary candidate results with the original repeat-unit SMILES |
| `rows.csv` | audit table including the calculation-only H-cap representation |
| `summary.json` | profiles, tiers, rule signatures, representation contract, and run metadata |
| `objective_plan.json` | explicit property/profile/tier routing for multi-rule tasks |
| `joint_config.json` | executable same-candidate multi-rule configuration |
| frozen `model.json` | custom or published structural rule artifact |

## Scientific scope

- STCA is a transparent screening and rule-extraction method, not a numerical property predictor.
- Passing a frozen rule means **structural rule compliance**, not experimental confirmation.
- Published-rule mode preserves the paper's ECFP2-split provenance and applies frozen conclusions directly.
- Custom-data mode allows user-defined percentage thresholds and user-supplied data roles; its outputs are new dataset-specific rules.
- Multi-property screening is the intersection of separately specified structural rules.
- The original STCA prefix-family construction is preserved; the skill does not replace it with arbitrary combinatorial or beam search.
- H-cap is a calculation representation; the original repeat-unit structure remains the authoritative output structure.

## Paper, source, and author profiles

- **Paper:** [Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design](https://doi.org/10.1038/s41524-026-02345-x)
- **Original implementation:** [foukusa/polymer-stca](https://github.com/foukusa/polymer-stca)
- **ORCID:** [0009-0005-4445-7074](https://orcid.org/0009-0005-4445-7074)
- **Google Scholar:** [Weihao Wang](https://scholar.google.com/citations?user=d9WIMyMAAAAJ)
- **ResearchGate:** [Weihao Wang](https://www.researchgate.net/profile/Weihao-Wang-23)
- **Software citation metadata:** [`CITATION.cff`](CITATION.cff)

## License

Read [`LICENSE`](LICENSE), [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), and [`PUBLISHER_LICENSE_NOTES.md`](PUBLISHER_LICENSE_NOTES.md) before redistribution. The agent-skill integration, original STCA implementation, logo, and any bundled data may have different applicable terms.
