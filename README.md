# STCA Agent Skill

![STCA logo](assets/stca-logo.png)

**Interpretable polymer screening, measured-data rule extraction, and rule-guided candidate design.**

STCA Agent Skill lets a coding agent use Weihao Wang's original Sliding Threshold Correlation Analysis (STCA). It runs the pinned author implementation, preserves readable presence/absence rules, and returns computed screening results with provenance. Package version **0.1.0** describes the agent integration; the underlying author package is **polymer-stca 1.0**.

中文：本技能支持“已发表规则筛选、实测数据提取规则、规则引导候选生成与核验”三种工作流。原 STCA 输入采用 **H-cap 后的 MACCS**。原低 EC 5% 的 `paper` 流程已复现为 **61/172**；随包 10 个无标签候选在 H-cap 后有 **9 个通过结构规则**。逐平台发布操作见发行资料中的 `PUBLISH_STEPS.zh-CN.md`。

## Three workflows

| Workflow | Input | Computed output |
| --- | --- | --- |
| Apply published rules | Candidate repeat-unit SMILES, profile and tier | Validity, selected/rejected status, failed literals, rule signature and execution receipt |
| Derive and freeze rules | Measured properties, explicit units, source data and evaluation roles | Threshold scans, original STCA rule families, selected representative, frozen model and evaluation metrics |
| Propose and verify candidates | Frozen constraints, generation goal and candidate budget | Host-agent proposals, H-capped calculation structures, per-rule checks and same-candidate intersections |

The host LLM proposes candidates in the third workflow. STCA supplies the constraints and deterministic verification; this package does not contain a separately trained molecular generator.

## Scientific contract

- For the original SMILES workflow, replace **terminal, single-bonded connection-point dummy atoms with hydrogen before generating MACCS**. Keep the original SMILES in its own column. The adapter writes a separate `SMILES_hcap` column. Already prepared, star-free rows remain unchanged; precomputed fingerprints are not capped again.
- Preserve 167 MACCS positions, including the unused K0 position. Use the complete RDKit MACCS generator, including count and special keys.
- Use `paper` to reproduce and apply the published representative rules. Use `source_locked` only when the task calls for choosing a representative from source labels alone. These protocols can select different members of the same rule family.
- A tier such as `0.05` specifies a target property tail; it does **not** prescribe selecting 5% of a candidate table.
- `selected=True` means that all frozen structural conditions match. It is not a measured property, a success probability, a synthesis assessment or proof of novelty.
- For evaluation, keep the property unit, numerical cutoff and label convention explicit. Historical `paper` selection data are not an untouched test set.
- H-cap collisions are representation collisions. Do not silently merge different original connection graphs.

The original signed ranking-prefix search and author rule families are retained. C-STCA, SC-SHAP, Auto-Select, GSP and PolymerLLM are separate methods.

## Files

| Path | Purpose |
| --- | --- |
| `skills/stca/SKILL.md` | Agent instructions and workflow routing |
| `skills/stca/scripts/` | Author-runtime adapter, H-cap preparation, CSV audit and rule tools |
| `skills/stca/scripts/setup_locked_environment.py` | Fresh CPython 3.12 environment and pinned-source setup |
| `skills/stca/assets/requirements-py312.txt` | Exact versions of the nine active Python dependencies |
| `skills/stca/assets/requirements-py312-linux-x86_64.lock` | SHA256-verified Linux x86-64 / CPython 3.12 dependency wheels |
| `skills/stca/references/` | Algorithm, commands, provenance and validated scope |
| `examples/candidates_10.csv` | Ten original agent proposals without measured property labels |
| `examples/expected_screening.json` | Per-candidate H-cap and frozen-rule regression expectations |
| `examples/joint_hcap.json` | Published high-Tg 20% and low-EC 5% constraints on the same calculation column |
| `tools/smoke_test.py` | Executable H-cap, screening, export and joint-screen regression check |
| `validation/summary.json` | Aggregate evidence; no original per-material measured records |
| `validation/public_smoke.json` | Public fixture check in a fresh isolated dependency environment |
| `CITATION.cff` | Software and research references |
| `THIRD_PARTY_NOTICES.md` | Upstream identity and unchanged upstream license notice |

## Setup

Run commands from the repository root. The release setup requires **CPython 3.12 and Git**. It creates a fresh isolated environment, installs the recorded dependency versions and obtains the pinned author source. Subsequent calculations use that verified local checkout. Do not reuse a nonempty environment directory.

```bash
python3.12 skills/stca/scripts/setup_locked_environment.py \
  --env-dir "$HOME/.venvs/stca-0.1.0" > stca-setup.json
```

Read the actual interpreter and source paths from the setup JSON, then check the environment:

```bash
STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
export STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"
"$STCA_PY" skills/stca/scripts/stca_runtime.py doctor
```

The default setup checks out the author source inside the new environment. If you already have the clean author checkout at the pinned revision, add `--source /absolute/clean/checkout` to the setup command. Keep `STCA_SOURCE` set for subsequent commands. Use a prepared checkout and dependencies for offline execution. Do not run the older `bootstrap` after creating this locked environment.

Linux x86-64 uses the hashed dependency lock. Other operating systems use the exact version snapshot and still require platform-specific installation verification; a portable version list alone is not a cross-platform test result.

The checked execution environment was Linux x86-64, Python 3.12.14, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0 and RDKit 2025.09.4. Compatibility with another operating system or hosted execution surface should be established by running the checks there. A skill catalog installs instructions and scripts; execution still needs a compatible runtime.

## Run the public smoke test

```bash
"$STCA_PY" tools/smoke_test.py \
  --skill-dir skills/stca \
  --output-dir out/smoke-001
```

Choose a new output directory for each run. The test executes the real installed scripts and frozen author profiles. Expected results:

- 10 original rows and all original fields preserved after H-cap;
- 10 valid candidate structures;
- low EC 5%, `paper`: **P01–P09 selected**, P10 rejected for K124;
- high Tg 20%, `paper`: all 10 pass the structural conditions;
- same-candidate high Tg 20% / low EC 5% intersection: **9 selected**;
- exported EC rule signature and frozen model content match the reference.

The command writes per-step logs, calculation outputs and `smoke_report.json`. It performs no fitting and does not use measured-property labels. This check establishes the published-rule integration and its representation contract; the historical-data and fitting results below are separate audits.

## Workflow 1: screen a candidate file

The bundled candidates use `ID,SMILES` plus descriptive text columns. Preserve those original columns and prepare the calculation column:

```bash
"$STCA_PY" skills/stca/scripts/prepare_hcap.py \
  --input examples/candidates_10.csv \
  --output out/candidates_hcap.csv \
  --smiles-column SMILES --output-column SMILES_hcap

"$STCA_PY" skills/stca/scripts/stca_runtime.py run -- \
  screen --profile ec-low --protocol paper --tier 0.05 \
  --input out/candidates_hcap.csv --smiles-column SMILES_hcap \
  --errors report --output out/ec_low_05_screen.csv
```

Use new output filenames if they already exist. The H-cap adapter refuses to overwrite its input or a previous output, and rejects an entire batch if its connection-point representation cannot be interpreted safely.

Supported published profiles are `tg-high`, `ec-low` and `ec-high`. Tg tiers are 0.30, 0.20 and 0.10; EC tiers are 0.20, 0.15, 0.10 and 0.05. Unsupported tiers are not interpolated.

## Workflow 2: extract rules from measured data

The following commands are a template for **your measured Tg tables**; those tables are not included in this release. They should contain `PID,SMILES,Tg`, with Tg in degrees Celsius. Prepare the same representation in both tables, check material and structure overlap, fit on source labels, freeze, then evaluate:

```bash
"$STCA_PY" skills/stca/scripts/prepare_hcap.py \
  --input tg_source.csv --output out/tg_source_hcap.csv
"$STCA_PY" skills/stca/scripts/prepare_hcap.py \
  --input tg_holdout.csv --output out/tg_holdout_hcap.csv

"$STCA_PY" skills/stca/scripts/audit_dataset.py \
  --input out/tg_source_hcap.csv --test out/tg_holdout_hcap.csv \
  --id-column PID --smiles-column SMILES_hcap --target Tg \
  --output out/tg_data_audit.json

"$STCA_PY" skills/stca/scripts/stca_runtime.py run -- \
  train-profile --profile tg-high --protocol source_locked \
  --input out/tg_source_hcap.csv --smiles-column SMILES_hcap \
  --target Tg --tg-unit degC --group-column PID \
  --output-dir out/tg_fit

"$STCA_PY" skills/stca/scripts/stca_runtime.py run -- \
  evaluate --model out/tg_fit/model.json \
  --input out/tg_holdout_hcap.csv --smiles-column SMILES_hcap \
  --target Tg --group-column PID --tier 0.20 \
  --cutoff-mode fixed_train --output out/tg_test_metrics.json
```

Read the audit before fitting. Resolve cross-set material/structure overlap without silently deleting or averaging repeated measurements. A model trained on a deliberately different representation must retain its own input contract.

For electrical conductivity, provide the actual input unit explicitly with `--ec-input-unit`; the original EC workflow uses `log10(S/cm)` internally. Do not interchange conductivity and resistivity. See `skills/stca/references/commands.md` for EC, original `paper` refitting and custom binary features.

## Workflow 3: export design constraints, propose and verify

```bash
"$STCA_PY" skills/stca/scripts/stca_tools.py export-rules \
  --profile ec-low --protocol paper --tier 0.05 \
  --output-dir out/ec_low_05_rules

"$STCA_PY" skills/stca/scripts/stca_tools.py joint-screen \
  --input out/candidates_hcap.csv --config examples/joint_hcap.json \
  --output-dir out/joint_screen
```

Ask the host agent to propose candidates using the exported `constraints.json` and `prompt.md`, within a stated proposal budget. Keep every raw proposal, run H-cap and the frozen checks, and return both passing and failing rows. Never alter the frozen rules merely to reach a requested candidate count.

Example agent requests:

> Apply the original STCA paper low-EC 5% rule to this candidate CSV. Preserve the original repeat-unit SMILES, H-cap the terminal connection points, and report selected IDs and failed bit conditions.

> Fit STCA to my measured Tg source data with the source_locked protocol, freeze the rules, and evaluate the supplied disjoint holdout using the saved training cutoff. Preserve all rule families and diagnostics.

> Export the published high-Tg 20% and low-EC 5% constraints, propose ten repeat-unit candidates, then H-cap and compute both rule checks. Retain every proposal and report the joint structural intersection.

## Validation evidence

The release includes a compact, aggregate `validation/summary.json` and the public candidate regression fixture. Full historical measured records are not distributed here.

| Audit | Verified result | Interpretation |
| --- | --- | --- |
| Archived rules, families and metric records | 1,251/1,251 metric rows; 11/11 paper and 11/11 source_locked representatives matched | Historical parity, not a new blind accuracy estimate |
| Original low EC 5% paper rule | 328/691 source, **61/172 extra**, 389/863 combined | Same 12 frozen conditions; paper refitting reproduced the representative |
| Original EC MACCS inputs | 863 × 167 positions; zero bit and record differences | Direct input/fingerprint check |
| New source-only fits | Tg split 5,829/1,462; EC split 689/174; 11 tier evaluations | New grouped split of existing measurements, not a new experimental cohort |
| Ten agent proposals after H-cap | 10 valid, **9 selected** by paper EC5; joint structural checks computed | No measured properties, synthesis or novelty validation |

Original paper extra labels participated in representative selection. For the same 61 selected extra records, the original dataset-relative EC5 label definition gives 10 true positives and 51 false positives; the fixed training cutoff gives 16 true positives and 45 false positives. The structural selection does not change.

For the new source-only split at tier 0.20, high Tg / low EC / high EC precision was 0.6926 / 0.3922 / 0.5000 and MCC was 0.5992 / 0.3601 / 0.2699. All 11 tier records, including the low-EC 5% source-only rule with zero holdout coverage, remain in the aggregate evidence. That rule is distinct from the original paper EC5 representative.

## Data handling

The wrapper scripts process user-supplied files in the chosen execution environment. Initial setup downloads the pinned author repository and Python dependencies. The computational scripts do not upload candidate or measured-data tables to an STCA service. Host-agent conversations and files remain subject to the chosen agent platform's data settings; this package does not establish a separate hosted data service.

Keep measured records, credentials, private paths and generated run directories out of public release archives. Publish only data you are entitled to redistribute. This package intentionally uses unlabeled agent proposals as its small public fixture.

## License and attribution

The author implementation is obtained from [foukusa/polymer-stca](https://github.com/foukusa/polymer-stca), pinned to commit `5951b0ef23d63edc8f7e803aaaffa5e4168288f6`. The release support files do not relicense that software. Its exact license notice and the other dependency notices are described in `THIRD_PARTY_NOTICES.md`.

Before public distribution, the publisher must confirm the license applicable to the new skill integration, branding and fixtures, and the scope of any required upstream redistribution permission. The preparation bundle includes `PUBLISHER_LICENSE_NOTES.md` to make those decisions explicit; it is not a license grant. Do not present the whole package as MIT or Apache unless the applicable rights have actually been granted.

## Cite

Weihao Wang, Haoou Ruan, Keith T. Butler, Akiko Kumada and Masahiro Sato. **Interpretable substructure-based screening of multi-property polymer dielectrics with prompt-ready rules for rational design.** *npj Computational Materials* (2026). [doi:10.1038/s41524-026-02345-x](https://doi.org/10.1038/s41524-026-02345-x).

Use `CITATION.cff` to cite this integration version, and cite the original paper and author implementation when using STCA. A release DOI can be added after a software archive is actually published; no DOI or new public repository is claimed by this preparation package.
