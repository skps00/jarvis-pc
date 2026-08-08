#Requires -Version 5.1
<#
.SYNOPSIS
  Launch the Jarvis wake-word sample recorder (16 kHz mono WAVs).

.EXAMPLE
  .\scripts\record_jarvis_wake.ps1
  .\scripts\record_jarvis_wake.ps1 -Target 1000
  .\scripts\record_jarvis_wake.ps1 -Target 1000 -Seconds 2.0
#>
param(
    [int] $Target = 1000,
    [double] $Seconds = 2.0,
    [string] $WakeWord = "jarvis",
    [string] $OutDir = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root "scripts\record_jarvis_wake.py"
if (-not (Test-Path -LiteralPath $py)) {
    throw "Missing $py"
}

$argsList = @(
    $py,
    "--wake-word", $WakeWord,
    "--target", "$Target",
    "--seconds", "$Seconds"
)
if ($OutDir) {
    $argsList += @("--out-dir", $OutDir)
}

Write-Host "Output default: %APPDATA%\Jarvis\wake_recordings\my_real_samples"
Write-Host "Stop Jarvis serve first if mic is busy (tray → 結束)."
Write-Host ""

& python @argsList
exit $LASTEXITCODE
