param(
    [ValidateSet("smoke", "editorial")]
    [string]$Preset = "smoke",
    [int]$Runs = 0,
    [int]$WarmRequests = 0,
    [switch]$IncludeNative
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ArgsList = @("--preset", $Preset)
if ($Runs -gt 0) { $ArgsList += @("--runs", "$Runs") }
if ($WarmRequests -gt 0) { $ArgsList += @("--warm-requests", "$WarmRequests") }
if ($IncludeNative) { $ArgsList += "--include-native" }

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    & python (Join-Path $Root "scripts\run-lab.py") @ArgsList
} else {
    & py -3 (Join-Path $Root "scripts\run-lab.py") @ArgsList
}
