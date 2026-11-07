# 在本地 agent 宿主准备 STCA 运行环境

适用于 DeepSeek Harness、WorkBuddy 或其他能够执行本地 Python 的宿主。`SKILL_DIR` 指向实际包含 `SKILL.md` 的 `stca` 目录；输入和输出放在用户工作目录中。

## macOS / Linux

准备 CPython 3.12 和 Git，然后运行：

```bash
SKILL_DIR="/absolute/path/to/stca"
STCA_ENV_DIR="$HOME/.venvs/stca-0.1.1"
export PYTHONUTF8=1

python3.12 "$SKILL_DIR/scripts/setup_locked_environment.py" \
  --env-dir "$STCA_ENV_DIR"

STCA_PY="$(python3.12 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["python"])' "$STCA_ENV_DIR/stca-environment.json")"
export STCA_SOURCE="$(python3.12 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["source"])' "$STCA_ENV_DIR/stca-environment.json")"

"$STCA_PY" "$SKILL_DIR/scripts/stca_runtime.py" doctor
```

## Windows PowerShell

```powershell
$SkillDir = (Resolve-Path "C:ctual\path\stca").Path
$StcaEnvDir = Join-Path $env:USERPROFILE ".venvs\stca-0.1.1"
$env:PYTHONUTF8 = "1"

py -3.12 (Join-Path $SkillDir "scripts\setup_locked_environment.py") --env-dir $StcaEnvDir
$Setup = Get-Content -LiteralPath (Join-Path $StcaEnvDir "stca-environment.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$StcaPy = $Setup.python
$env:STCA_SOURCE = $Setup.source
& $StcaPy (Join-Path $SkillDir "scripts\stca_runtime.py") doctor
```

`doctor` 成功后直接执行用户任务。筛选和规则提取命令见 [commands.md](commands.md)。

## 路径与 H-cap

保留原始重复单元 SMILES，用 `prepare_hcap.py` 另建 `SMILES_hcap` 计算列，再用该列计算 MACCS。环境和输出目录不要放进 skill 安装目录。已有成功环境可复用 `stca-environment.json` 中的解释器和源码路径。
