# Reproducible STCA release environment

The release retains the original STCA source revision
`5951b0ef23d63edc8f7e803aaaffa5e4168288f6`. The environment installer changes
dependency setup only; it does not change the STCA algorithm, rules or data.

## Files and placement

| File | Position inside the distributed skill |
| --- | --- |
| `setup_locked_environment.py` | `scripts/setup_locked_environment.py` |
| `requirements-py312.txt` | `assets/requirements-py312.txt` |
| `requirements-py312-linux-x86_64.lock` | `assets/requirements-py312-linux-x86_64.lock` |

Keep `DEPENDENCY_VALIDATION.json` with the public release's validation evidence.
Do not distribute either development virtual environment or the private build
logs. The original algorithm is fetched from its public repository, not bundled
by this installer.

## Setup

Install CPython 3.12 and Git first. Run from the release repository root:

```bash
python3.12 skills/stca/scripts/setup_locked_environment.py \
  --env-dir "$HOME/.venvs/stca-0.1.0" > stca-setup.json
```

The environment directory must not already exist. Installation progress goes
to stderr. Stdout contains one JSON object with `python` and `source` keys.
The same object is saved to `stca-environment.json` inside the new environment.

```bash
STCA_PY="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["python"])')"
STCA_SOURCE="$(python3.12 -c 'import json; print(json.load(open("stca-setup.json"))["source"])')"
export STCA_SOURCE
"$STCA_PY" skills/stca/scripts/stca_runtime.py --source "$STCA_SOURCE" doctor
"$STCA_PY" tools/smoke_test.py --skill-dir skills/stca \
  --source "$STCA_SOURCE" --output-dir out/smoke-001
```

Use this interpreter for subsequent H-cap, screening, fitting and export
commands. Do not invoke the convenience `bootstrap` command afterward: that
command prepares a different cache environment and does not select this lock.

If the pinned source checkout already exists, supply `--source /absolute/path`
to the setup command. The checkout must match the pinned commit and its source
and license files must be clean. This option skips the GitHub download; PyPI
access is still required for the dependency installation.

## Dependency policies

- On Linux x86_64, the default `linux-hashed` mode uses the exact wheels and
  SHA256 hashes recorded from the clean installation. It requires compatible
  manylinux wheels; RDKit's selected wheel requires glibc 2.28 or newer.
- On other operating systems, the default `portable-pinned` mode uses the same
  nine exact package versions and requires binary wheels. It has no wheel-hash
  claim. This path must pass the release smoke test on the actual target
  machine before that platform is listed as supported.
- No package version is relaxed or replaced if installation fails. A partial
  newly created directory is retained for inspection, and an existing directory
  is never changed or removed by the installer.

## What has been verified

On 2026-11-07, a new Linux x86_64 / CPython 3.12.14 environment was created with
`system_site_packages=False`. All nine active runtime dependencies were
installed from public PyPI at the specified versions. `pip check` passed;
NumPy, pandas, SciPy and RDKit imported successfully, and RDKit returned a
167-position MACCS fingerprint for a basic structural check.

The separate release installer then successfully created another isolated
environment using the SHA256 wheel lock, verified the supplied clean source at
the pinned commit, and ran the original runtime's `doctor` command. See
`DEPENDENCY_VALIDATION.json` for the recorded scope and wheel hashes. Screening
and scientific-rule verification are recorded separately in the release's
smoke report and STCA audit evidence.

A separate fresh GitHub clone and checkout of the pinned commit also
succeeded. The installer test itself supplied an existing clean checkout;
the source-download check is recorded separately rather than described as
one combined end-to-end download test.

macOS and Windows have not been executed in this validation environment. The
files support attempting the exact-version setup there, but this is not a
claim of completed cross-platform validation.

## 中文说明

这组文件把已验证环境固定为九个实际依赖的精确版本。Linux x86_64 另提供已验证
wheel 的 SHA256 锁；macOS／Windows 使用同版本的可移植文件，并需要在目标机器
运行公开验收样例。安装器只写入新建目录，保留原 STCA 算法与规则，不覆盖现有
Python 环境，也不因安装失败而自动降低版本。
