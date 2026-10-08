param(
    [ValidateSet("debug", "release")]
    [string]$Mode = "debug"
)
# Both historical entry points build the same local, unified SettingsLab package.
$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonExe = if ($env:DK_PYTHON3) { $env:DK_PYTHON3 } else { "python" }
Push-Location $repoRoot
try {
    & $pythonExe -m unittest discover -s build_tools/tests
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $pythonExe build_tools/localize_configs.py --check
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $pythonExe build_tools/build_lab.py --flash
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
