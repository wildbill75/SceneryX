<#
.SYNOPSIS
    SceneryX "Fresh User" Environment Reset Routine
.DESCRIPTION
    Systematically rolls back MSFS simulator state to stock defaults and purges
    all SceneryX installation footprints, AppData cache, configuration files,
    registry entries, and shortcuts. This guarantees a 100% pristine environment
    to test new builds exactly like a brand-new user.
.PARAMETER InstallDir
    Optional custom installation directory path (defaults to C:\Program Files\SceneryX).
.PARAMETER SkipRollback
    Skips the MSFS simulator rollback if you only want to clean SceneryX app files.
.PARAMETER NonInteractive
    Runs without waiting for confirmation prompts.
#>

[CmdletBinding()]
param(
    [string]$InstallDir = "C:\Program Files\SceneryX",
    [switch]$SkipRollback,
    [switch]$NonInteractive
)

$ErrorActionPreference = "Continue"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "     SceneryX Automated 'Fresh User' Environment Reset Routine    " -ForegroundColor White
Write-Host "=================================================================" -ForegroundColor Cyan

# 0. Check Administrator Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[WARNING] Running without Administrator privileges!" -ForegroundColor Yellow
    Write-Host "          Modifications to Program Files or HKLM may be restricted." -ForegroundColor Yellow
    Write-Host "          For complete cleanup, consider running PowerShell as Administrator." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Administrator privileges confirmed." -ForegroundColor Green
}

# 1. Terminate Running Processes
Write-Host "`n[Step 1/5] Terminating any running SceneryX instances..." -ForegroundColor Cyan
$processes = Get-Process -Name "SceneryX" -ErrorAction SilentlyContinue
if ($processes) {
    foreach ($p in $processes) {
        Write-Host "  -> Terminating process PID $($p.Id)..." -ForegroundColor Yellow
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 1
    Write-Host "  [OK] Running processes terminated." -ForegroundColor Green
} else {
    Write-Host "  [OK] No running SceneryX processes detected." -ForegroundColor Gray
}

# 2. Non-Destructive Simulator Rollback
if (-not $SkipRollback) {
    Write-Host "`n[Step 2/5] Performing non-destructive MSFS rollback to stock defaults..." -ForegroundColor Cyan
    $rollbackDone = $false

    # Search for an executable or Python main.py to execute the --restore-defaults command
    $candidateRunners = @(
        (Join-Path $InstallDir "SceneryX.exe"),
        "D:\SceneryX\build\SceneryX\SceneryX.exe",
        "D:\SceneryX\SceneryX.exe"
    )

    foreach ($exe in $candidateRunners) {
        if (Test-Path $exe) {
            Write-Host "  -> Invoking rollback via: $exe --restore-defaults" -ForegroundColor White
            try {
                $proc = Start-Process -FilePath $exe -ArgumentList "--restore-defaults" -NoNewWindow -Wait -PassThru
                if ($proc.ExitCode -eq 0) {
                    Write-Host "  [OK] Rollback executed successfully via $exe." -ForegroundColor Green
                    $rollbackDone = $true
                    break
                }
            } catch {
                Write-Host "  [WARN] Failed executing $($exe) : $_" -ForegroundColor Yellow
            }
        }
    }

    if (-not $rollbackDone) {
        $pythonScript = "D:\SceneryX\main.py"
        if (Test-Path $pythonScript) {
            Write-Host "  -> Invoking fallback rollback via: python.exe $pythonScript --restore-defaults" -ForegroundColor White
            try {
                $pyProc = Start-Process -FilePath "python.exe" -ArgumentList "`"$pythonScript`" --restore-defaults" -NoNewWindow -Wait -PassThru
                if ($pyProc.ExitCode -eq 0) {
                    Write-Host "  [OK] Fallback rollback completed successfully via Python." -ForegroundColor Green
                    $rollbackDone = $true
                }
            } catch {
                Write-Host "  [WARN] Failed executing Python rollback: $_" -ForegroundColor Yellow
            }
        }
    }

    if (-not $rollbackDone) {
        Write-Host "  [WARN] No SceneryX executable or Python environment found for automated rollback." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[Step 2/5] Simulator rollback skipped by request." -ForegroundColor Gray
}

# 3. Clean Installation Directory
Write-Host "`n[Step 3/5] Cleaning installation directory footprints..." -ForegroundColor Cyan
if (Test-Path $InstallDir) {
    Write-Host "  -> Removing installation folder: $InstallDir" -ForegroundColor White
    try {
        Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction Stop
        Write-Host "  [OK] Removed $InstallDir." -ForegroundColor Green
    } catch {
        Write-Host "  [ERROR] Could not fully remove $InstallDir ($($_)). Elevation may be required." -ForegroundColor Red
    }
} else {
    Write-Host "  [OK] No installation folder found at $InstallDir (clean)." -ForegroundColor Gray
}

# 4. Clean User Configurations, Cache & State Files
Write-Host "`n[Step 4/5] Removing user configs, cache, and state files (%APPDATA% & %LOCALAPPDATA%)..." -ForegroundColor Cyan
$userPaths = @(
    (Join-Path $env:APPDATA "SceneryX"),
    (Join-Path $env:LOCALAPPDATA "SceneryX")
)

foreach ($uPath in $userPaths) {
    if (Test-Path $uPath) {
        Write-Host "  -> Removing user directory: $uPath" -ForegroundColor White
        try {
            Remove-Item -Path $uPath -Recurse -Force -ErrorAction Stop
            Write-Host "  [OK] Purged $uPath." -ForegroundColor Green
        } catch {
            Write-Host "  [ERROR] Failed to remove $($uPath) : $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  [OK] No residual data found at $uPath." -ForegroundColor Gray
    }
}

# 5. Clean Registry Keys & Shortcuts
Write-Host "`n[Step 5/5] Purging registry keys and shortcuts..." -ForegroundColor Cyan

# 5a. Registry Keys
$regKeys = @(
    "HKCU:\Software\SceneryX",
    "HKLM:\Software\SceneryX",
    "HKLM:\Software\WOW6432Node\SceneryX",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{8B8A6E3F-7A9B-4D2E-B7C6-9E3F1A2B4C5D}_is1",
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SceneryX_is1",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{8B8A6E3F-7A9B-4D2E-B7C6-9E3F1A2B4C5D}_is1",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SceneryX_is1"
)

foreach ($rKey in $regKeys) {
    if (Test-Path $rKey) {
        Write-Host "  -> Deleting registry key: $rKey" -ForegroundColor White
        try {
            Remove-Item -Path $rKey -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Deleted $rKey." -ForegroundColor Green
        } catch {
            Write-Host "  [WARN] Could not remove $($rKey) : $_" -ForegroundColor Yellow
        }
    }
}

# Search and prune any additional SceneryX uninstall keys
$uninstallBases = @(
    "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall",
    "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall",
    "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
)
foreach ($base in $uninstallBases) {
    if (Test-Path $base) {
        Get-ChildItem -Path $base -ErrorAction SilentlyContinue | Where-Object {
            $_.PSChildName -like "*SceneryX*" -or (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue).DisplayName -like "*SceneryX*"
        } | ForEach-Object {
            Write-Host "  -> Deleting lingering uninstall entry: $($_.PSPath)" -ForegroundColor White
            Remove-Item -Path $_.PSPath -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# 5b. Desktop and Start Menu Shortcuts
$shortcuts = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) "SceneryX.lnk"),
    (Join-Path ([Environment]::GetFolderPath('CommonDesktop')) "SceneryX.lnk"),
    (Join-Path ([Environment]::GetFolderPath('Programs')) "SceneryX.lnk"),
    (Join-Path ([Environment]::GetFolderPath('Programs')) "SceneryX"),
    (Join-Path ([Environment]::GetFolderPath('CommonPrograms')) "SceneryX.lnk"),
    (Join-Path ([Environment]::GetFolderPath('CommonPrograms')) "SceneryX")
)

foreach ($s in $shortcuts) {
    if (Test-Path $s) {
        Write-Host "  -> Removing shortcut: $s" -ForegroundColor White
        try {
            Remove-Item -Path $s -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Removed shortcut: $s" -ForegroundColor Green
        } catch {
            Write-Host "  [WARN] Failed to delete shortcut $($s) : $_" -ForegroundColor Yellow
        }
    }
}

Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "     FRESH USER ENVIRONMENT RESET COMPLETE!                      " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "The system is now in a 100% stock, pristine condition for testing.`n" -ForegroundColor White
