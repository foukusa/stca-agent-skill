# Bootstrap an existing CPython >=3.10. Never installs or changes execution policy.
$stcaArgs = [System.Collections.Generic.List[string]]::new()
foreach ($item in $args) { $stcaArgs.Add([string]$item) }
$stcaScript = Join-Path $PSScriptRoot 'agent_runtime.py'
$stcaExplicit = $env:STCA_BOOTSTRAP_PY
while ($stcaArgs.Count -gt 0) {
    if ($stcaArgs[0] -eq '--script' -or $stcaArgs[0] -eq '--bootstrap-python') {
        if ($stcaArgs.Count -lt 2) { Write-Error 'STCA: missing launcher option value.'; exit 2 }
        if ($stcaArgs[0] -eq '--script') { $stcaScript = $stcaArgs[1] } else { $stcaExplicit = $stcaArgs[1] }
        $stcaArgs.RemoveRange(0, 2)
    } elseif ($stcaArgs[0] -eq '--') { $stcaArgs.RemoveAt(0); break } else { break }
}
for ($index = 0; $index -lt $stcaArgs.Count; $index++) {
    if ($stcaArgs[$index] -eq '--python' -and $index + 1 -lt $stcaArgs.Count) { $stcaExplicit = $stcaArgs[$index + 1]; break }
    if ($stcaArgs[$index].StartsWith('--python=')) { $stcaExplicit = $stcaArgs[$index].Substring(9); break }
    if ($stcaArgs[$index] -in @('ensure','discover','run','prepare','status')) { break }
}
$stcaCandidates = [System.Collections.Generic.List[string]]::new()
function Add-StcaCandidate([string]$candidate) {
    if ($candidate -and -not $stcaCandidates.Contains($candidate) -and $stcaCandidates.Count -lt 96) { $stcaCandidates.Add($candidate) }
}
function Add-StcaPrefix([string]$prefix) {
    if ($prefix) { Add-StcaCandidate (Join-Path $prefix 'python.exe'); Add-StcaCandidate (Join-Path $prefix 'Scripts/python.exe') }
}
if ($stcaExplicit) { Add-StcaCandidate $stcaExplicit } else {
    Add-StcaCandidate $env:STCA_PY
    Add-StcaPrefix $env:VIRTUAL_ENV; Add-StcaPrefix $env:CONDA_PREFIX
    foreach ($name in @('python3','python','python3.10','python3.11','python3.12','python3.13','python3.14','python3.15')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) { Add-StcaCandidate $command.Source }
    }
    $stcaRoots = @((Join-Path $PWD '.venv'), (Join-Path $PWD 'venv'))
    foreach ($base in @($env:USERPROFILE,$env:LOCALAPPDATA,$env:ProgramData)) {
        if ($base) {
            foreach ($name in @('miniconda3','anaconda3','miniforge3','mambaforge')) {
                $root = Join-Path $base $name; $stcaRoots += $root
                $stcaRoots += @(Get-ChildItem -LiteralPath (Join-Path $root 'envs') -Directory -ErrorAction SilentlyContinue | Select-Object -First 32 | ForEach-Object FullName)
            }
        }
    }
    foreach ($base in @((Join-Path $env:USERPROFILE '.venvs'),(Join-Path $env:USERPROFILE '.virtualenvs'))) {
        $stcaRoots += @(Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Select-Object -First 32 | ForEach-Object FullName)
    }
    if ($env:LOCALAPPDATA) {
        $stcaRoots += @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'Programs/Python') -Directory -Filter 'Python*' -ErrorAction SilentlyContinue | Select-Object -First 32 | ForEach-Object FullName)
    }
    foreach ($base in @($env:ProgramFiles,${env:ProgramFiles(x86)})) {
        if ($base) { $stcaRoots += @(Get-ChildItem -LiteralPath $base -Directory -Filter 'Python*' -ErrorAction SilentlyContinue | Select-Object -First 32 | ForEach-Object FullName) }
    }
    $registry = Join-Path $env:USERPROFILE '.conda/environments.txt'
    if (Test-Path -LiteralPath $registry -PathType Leaf) { $stcaRoots += @(Get-Content -LiteralPath $registry -TotalCount 64) }
    foreach ($root in $stcaRoots) { Add-StcaPrefix $root }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($line in @(& $py.Source -0p 2>&1 | Select-Object -First 64)) {
            if ([string]$line -match '([A-Za-z]:\\.*?python(?:\d+(?:\.\d+)*)?\.exe)\s*$') { Add-StcaCandidate $Matches[1] }
        }
    }
    foreach ($key in @('HKCU:\Software\Python\PythonCore','HKLM:\Software\Python\PythonCore','HKLM:\Software\WOW6432Node\Python\PythonCore')) {
        foreach ($version in @(Get-ChildItem -LiteralPath $key -ErrorAction SilentlyContinue | Select-Object -First 32)) {
            try { $prefix = (Get-Item -LiteralPath (Join-Path $version.PSPath 'InstallPath') -ErrorAction Stop).GetValue(''); Add-StcaPrefix $prefix } catch {}
        }
    }
}
foreach ($candidate in $stcaCandidates) {
    if ($candidate -match '\\WindowsApps\\') { continue }
    try {
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
        & $candidate -c "import platform,sys;sys.exit(0 if platform.python_implementation()=='CPython' and sys.version_info[:2]>=(3,10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { & $candidate $stcaScript @stcaArgs; exit $LASTEXITCODE }
    } catch {}
}
if ($stcaExplicit) { Write-Error 'STCA: the explicitly selected Python is unavailable or below Python 3.10; no other interpreter was substituted.' }
else { Write-Error 'STCA: no usable Python 3.10+ was found in local environments. Select an existing interpreter or prepare Python, then retry. No packages were installed.' }
exit 2
