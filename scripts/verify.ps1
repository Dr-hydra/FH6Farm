param(
    [switch]$Release
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root
$Python = "python"
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    $Python = "py"
}
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python or make py.exe/python.exe available."
}

Write-Host "[1/6] Validate config.json"
@'
from fh6auto_core.config import ensure_config_file, config_path
cfg = ensure_config_file()
print(f"config ok: {config_path()}")
print(f"race_count={cfg['race_count']}, buy_count={cfg['buy_count']}, global_loops={cfg['global_loops']}")
'@ | & $Python -
if ($LASTEXITCODE -ne 0) { throw "Config validation failed with exit code $LASTEXITCODE" }

Write-Host "[2/6] Check Python runtime imports"
@'
import customtkinter
import cv2
import numpy
import pyautogui
import pydirectinput
import requests
import pynput
import PIL
import win32gui
print("runtime imports ok")
'@ | & $Python -
if ($LASTEXITCODE -ne 0) { throw "Python runtime import check failed with exit code $LASTEXITCODE" }

Write-Host "[3/6] Compile Python sources"
$pyFiles = @("main.py", "fh6auto_core_launcher.py") + (Get-ChildItem -Path "fh6auto_core" -Filter "*.py" -File | ForEach-Object { $_.FullName })
& $Python -m py_compile @pyFiles
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed with exit code $LASTEXITCODE" }

Write-Host "[4/6] Probe headless entry"
& $Python -m fh6auto_core.headless --help | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Headless entry probe failed with exit code $LASTEXITCODE" }

Write-Host "[5/6] Build WPF frontend"
dotnet build ".\ui\FH6Auto.UI.sln" -c Debug
if ($LASTEXITCODE -ne 0) { throw "WPF build failed with exit code $LASTEXITCODE" }

if ($Release) {
    Write-Host "[6/6] Build release packages"
    & ".\scripts\build-release.ps1"
    if ($LASTEXITCODE -ne 0) { throw "Release package build failed with exit code $LASTEXITCODE" }

    $releaseDir = Join-Path $root "dist\release"
    $packageDirs = Get-ChildItem -LiteralPath $releaseDir -Directory
    if ($packageDirs.Count -ne 2) { throw "Expected two release package directories." }
    foreach ($packageDir in $packageDirs) {
        $fileCount = (Get-ChildItem -LiteralPath $packageDir.FullName -File).Count
        if ($fileCount -ne 3) { throw "Expected three files in $($packageDir.Name), found $fileCount." }
        foreach ($required in @("FH6Farm.exe", "FH6AutoCore.exe", "config.json")) {
            if (-not (Test-Path -LiteralPath (Join-Path $packageDir.FullName $required))) {
                throw "Missing $required in $($packageDir.Name)."
            }
        }
    }

    Write-Host "[release] Smoke bundled core without game process"
    $packageDir = $packageDirs | Where-Object { $_.Name -like "*with-runtime" } | Select-Object -First 1
    $coreExe = Join-Path $packageDir.FullName "FH6AutoCore.exe"
    $stdout = Join-Path $packageDir.FullName "core-smoke.out"
    $stderr = Join-Path $packageDir.FullName "core-smoke.err"
    Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $coreExe `
        -ArgumentList "--start race" `
        -WorkingDirectory $packageDir.FullName `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
    if (-not $p.WaitForExit(60000)) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        throw "Bundled core smoke test timed out."
    }
    if ((Test-Path $stderr) -and ((Get-Item $stderr).Length -gt 0)) {
        Get-Content -Path $stderr -Encoding UTF8 | Select-Object -Last 30
        throw "Bundled core smoke test wrote stderr."
    }
    Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "[6/6] Release package skipped. Pass -Release to include it."
}

Remove-Item -LiteralPath "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "fh6auto_core\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Verification completed."
