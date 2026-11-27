param([string]$OptionsJson)

$ErrorActionPreference = 'Stop'
$Run = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'daily-clear-uu.json') -Encoding UTF8 -Raw | ConvertFrom-Json
if (-not (Test-Path -LiteralPath $Run.python -PathType Leaf) -or
    -not (Test-Path -LiteralPath $Run.runner -PathType Leaf)) {
    throw 'UU helper is missing. Rerun setup-windows.ps1 with -WithUu.'
}
$env:DAILY_CLEAR_HUB_UU_OPTIONS = $OptionsJson
& $Run.python -X utf8 -u $Run.runner pretask
exit $LASTEXITCODE
