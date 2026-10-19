<#
.SYNOPSIS
    SceneryX PowerShell Build Pipeline
.DESCRIPTION
    Runs the complete build pipeline:
      1. Synchronizes versioning across UI (splash.html, index.html) and Inno Setup script
      2. Compiles PyInstaller single-file binary into D:\SceneryX\build\SceneryX\
      3. Cleans intermediate cache (D:\SceneryX\build\pyinstaller_temp\)
      4. Compiles Inno Setup installer into D:\SceneryX\build\installer\<ReleaseName>\
.PARAMETER Increment
    Increments the release patch version (e.g. 1.0.1 -> 1.0.2).
.PARAMETER Version
    Explicit version tag (e.g. RC_v1.0.1).
.PARAMETER SkipPyInstaller
    Skips PyInstaller rebuild and only regenerates the Inno Setup installer.
#>

[CmdletBinding()]
param(
    [switch]$Increment,
    [string]$Version,
    [switch]$SkipPyInstaller
)

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "         SceneryX Windows Production Build Pipeline              " -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan

$baseDir = "D:\SceneryX"
$pythonExe = "python.exe"

if (-not (Test-Path (Join-Path $baseDir "main.py"))) {
    Write-Host "[ERROR] Could not find main.py in $baseDir" -ForegroundColor Red
    exit 1
}

$buildScript = Join-Path $baseDir "build_pipeline.py"
Write-Host "Executing build pipeline runner: $buildScript..." -ForegroundColor White

$pyArgs = @($buildScript)
if ($Increment) {
    $pyArgs += "--increment"
}
if ($Version) {
    $pyArgs += "--version"
    $pyArgs += $Version
}
if ($SkipPyInstaller) {
    $pyArgs += "--skip-pyinstaller"
}

& $pythonExe @pyArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Build pipeline completed without errors!" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Build pipeline failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
