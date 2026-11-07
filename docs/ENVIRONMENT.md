# STCA release environment

The release pins the polymer-stca source revision
`5951b0ef23d63edc8f7e803aaaffa5e4168288f6` and exact Python dependency versions.
The setup helper prepares a new environment without changing STCA rules or algorithms.

## Setup

```bash
python3.12 skills/stca/scripts/setup_locked_environment.py \
  --env-dir "$HOME/.venvs/stca-0.1.1"
```

Read `python` and `source` from the generated `stca-environment.json`, export
`STCA_SOURCE`, and run:

```bash
"$STCA_PY" skills/stca/scripts/stca_runtime.py doctor
```

Use the recorded interpreter for H-cap preparation, screening, fitting, rule export
and objective planning. An existing environment is not overwritten. Linux x86_64
uses the included wheel-hash lock; other systems use the exact version snapshot and
must have compatible wheels.

Detailed user commands are in `skills/stca/references/commands.md`.
