#Requires -Version 5.1
<#
.SYNOPSIS
  Copy a trained openWakeWord .onnx into JARVIS wake folder.

.EXAMPLE
  .\scripts\install_wake_onnx.ps1 -SourcePath .\Downloads\jarvis.onnx
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $SourcePath,

    [string] $DestName = "jarvis.onnx"
)

$ErrorActionPreference = "Stop"
$src = Resolve-Path -LiteralPath $SourcePath
if (-not (Test-Path -LiteralPath $src -PathType Leaf)) {
    throw "Source not found: $SourcePath"
}
if ($src.Path -notmatch '\.onnx$') {
    Write-Warning "File does not end with .onnx — continuing anyway."
}

$destDir = Join-Path $env:APPDATA "Jarvis\wake"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
$dest = Join-Path $destDir $DestName
Copy-Item -LiteralPath $src -Destination $dest -Force

Write-Host "Installed: $dest"
Write-Host "Stem must contain 'jarvis' to auto-disable SenseVoice text-wake fallback."
Write-Host "Restart: pythonw -m jarvis serve  (or re-run Startup JARVIS.vbs)"

Get-ChildItem $destDir -Filter *.onnx | ForEach-Object {
    Write-Host ("  - {0} ({1:N0} bytes)" -f $_.Name, $_.Length)
}
