$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$outDir = Join-Path $root "dist\FH6Auto.UI"
$assetsData = "$root\assets;assets"
$imagesData = "$root\images;images"
$Python = "python"
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    $Python = "py"
}
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python or make py.exe/python.exe available."
}

Set-Location $root

if (Test-Path $outDir) {
    Remove-Item -LiteralPath $outDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$pyBuildDir = Join-Path $root "build\pyinstaller-core"
if (Test-Path $pyBuildDir) {
    Remove-Item -LiteralPath $pyBuildDir -Recurse -Force
}

Write-Host "[1/4] Publish WPF frontend"
dotnet publish ".\ui\src\QING.UIKIT\QING.UIKIT.vbproj" `
    -c Release `
    -r win-x64 `
    -o $outDir `
    --self-contained true `
    -p:PublishSingleFile=false `
    -p:PublishReadyToRun=false
if ($LASTEXITCODE -ne 0) {
    throw "dotnet publish failed with exit code $LASTEXITCODE"
}

Write-Host "[2/4] Build Python core executable"
& $Python -m PyInstaller `
    --noconfirm `
    --onefile `
    --name FH6AutoCore `
    --distpath $outDir `
    --workpath $pyBuildDir `
    --specpath $pyBuildDir `
    --icon "$root\assets\icon.ico" `
    --collect-data customtkinter `
    --add-data $assetsData `
    --add-data $imagesData `
    ".\fh6auto_core_launcher.py"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "[3/4] Copy Python source fallback and runtime assets"
Copy-Item -LiteralPath ".\main.py" -Destination $outDir -Force
Copy-Item -LiteralPath ".\fh6auto_core_launcher.py" -Destination $outDir -Force
Copy-Item -LiteralPath ".\requirements.txt" -Destination $outDir -Force
Copy-Item -LiteralPath ".\version.json" -Destination $outDir -Force
Copy-Item -LiteralPath ".\config.json" -Destination $outDir -Force
Copy-Item -LiteralPath ".\fh6auto_core" -Destination $outDir -Recurse -Force
Copy-Item -LiteralPath ".\assets" -Destination $outDir -Recurse -Force
Copy-Item -LiteralPath ".\images" -Destination $outDir -Recurse -Force

Write-Host "[4/4] Write launch helper"
@'
@echo off
cd /d "%~dp0"
FH6Auto.UI.exe
'@ | Set-Content -Path (Join-Path $outDir "run-ui.bat") -Encoding ASCII

@'
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$requiredFiles = @(
    "FH6Auto.UI.exe",
    "FH6AutoCore.exe",
    "config.json",
    "version.json",
    "run-ui.bat"
)

foreach ($file in $requiredFiles) {
    if (-not (Test-Path (Join-Path $root $file))) {
        throw "Missing required file: $file"
    }
}

foreach ($dir in @("assets", "images")) {
    if (-not (Test-Path (Join-Path $root $dir))) {
        throw "Missing required directory: $dir"
    }
}

& ".\FH6AutoCore.exe" --help | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "FH6AutoCore.exe --help failed with exit code $LASTEXITCODE"
}

Write-Host "FH6Auto.UI package self-check passed."
'@ | Set-Content -Path (Join-Path $outDir "self-check.ps1") -Encoding UTF8

Write-Host "Release package ready: $outDir"
