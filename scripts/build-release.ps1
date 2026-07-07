param(
    [string]$Version
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = (Get-Content -LiteralPath (Join-Path $root "version.json") -Raw | ConvertFrom-Json).version
}

$Python = "python"
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    $Python = "py"
}
if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    throw "Python was not found. Install Python or make py.exe/python.exe available."
}

$buildRoot = Join-Path $root "build\release"
$releaseRoot = Join-Path $root "dist\release"
$coreOutput = Join-Path $buildRoot "core"
$pyWork = Join-Path $buildRoot "pyinstaller"
$uiWithRuntime = Join-Path $buildRoot "ui-with-runtime"
$uiWithoutRuntime = Join-Path $buildRoot "ui-without-runtime"
$withRuntimeName = "FH6Farm-v$Version-win-x64-with-runtime"
$withoutRuntimeName = "FH6Farm-v$Version-win-x64-without-runtime"
$withRuntimeDir = Join-Path $releaseRoot $withRuntimeName
$withoutRuntimeDir = Join-Path $releaseRoot $withoutRuntimeName

function Remove-WorkspaceDirectory([string]$Path) {
    $fullPath = [IO.Path]::GetFullPath($Path)
    $rootPrefix = [IO.Path]::GetFullPath($root).TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove a directory outside the workspace: $fullPath"
    }
    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Recurse -Force
    }
}

Remove-WorkspaceDirectory $buildRoot
Remove-WorkspaceDirectory $releaseRoot
New-Item -ItemType Directory -Force -Path $coreOutput, $pyWork, $uiWithRuntime, $uiWithoutRuntime, $releaseRoot | Out-Null

Write-Host "[1/5] Build Python automation core"
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name FH6AutoCore `
    --distpath $coreOutput `
    --workpath $pyWork `
    --specpath $pyWork `
    --icon "$root\assets\icon.ico" `
    --add-data "$root\assets;assets" `
    --add-data "$root\images;images" `
    ".\fh6auto_core_launcher.py"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "[2/5] Publish self-contained WPF frontend"
dotnet publish ".\ui\src\QING.UIKIT\QING.UIKIT.vbproj" `
    -c Release `
    -r win-x64 `
    -o $uiWithRuntime `
    --self-contained true `
    -p:PublishSingleFile=true `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -p:EnableCompressionInSingleFile=true `
    -p:PublishReadyToRun=false `
    -p:DebugSymbols=false `
    -p:DebugType=None
if ($LASTEXITCODE -ne 0) {
    throw "Self-contained dotnet publish failed with exit code $LASTEXITCODE"
}

Write-Host "[3/5] Publish framework-dependent WPF frontend"
dotnet publish ".\ui\src\QING.UIKIT\QING.UIKIT.vbproj" `
    -c Release `
    -r win-x64 `
    -o $uiWithoutRuntime `
    --self-contained false `
    -p:PublishSingleFile=true `
    -p:PublishReadyToRun=false `
    -p:DebugSymbols=false `
    -p:DebugType=None
if ($LASTEXITCODE -ne 0) {
    throw "Framework-dependent dotnet publish failed with exit code $LASTEXITCODE"
}

Write-Host "[4/5] Assemble minimal packages"
foreach ($packageDir in @($withRuntimeDir, $withoutRuntimeDir)) {
    New-Item -ItemType Directory -Force -Path $packageDir | Out-Null
    Copy-Item -LiteralPath (Join-Path $coreOutput "FH6AutoCore.exe") -Destination $packageDir -Force
    Copy-Item -LiteralPath ".\assets\config\config_example.json" -Destination (Join-Path $packageDir "config.json") -Force
}
Copy-Item -LiteralPath (Join-Path $uiWithRuntime "FH6Farm.exe") -Destination $withRuntimeDir -Force
Copy-Item -LiteralPath (Join-Path $uiWithoutRuntime "FH6Farm.exe") -Destination $withoutRuntimeDir -Force

foreach ($packageDir in @($withRuntimeDir, $withoutRuntimeDir)) {
    $files = Get-ChildItem -LiteralPath $packageDir -File
    if ($files.Count -ne 3) {
        throw "Package should contain exactly 3 files, found $($files.Count): $packageDir"
    }
    & (Join-Path $packageDir "FH6AutoCore.exe") --help | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Bundled core probe failed: $packageDir"
    }
}

Write-Host "[5/5] Create release archives and checksums"
$withRuntimeZip = Join-Path $releaseRoot "$withRuntimeName.zip"
$withoutRuntimeZip = Join-Path $releaseRoot "$withoutRuntimeName.zip"
Compress-Archive -Path (Join-Path $withRuntimeDir "*") -DestinationPath $withRuntimeZip -CompressionLevel Optimal
Compress-Archive -Path (Join-Path $withoutRuntimeDir "*") -DestinationPath $withoutRuntimeZip -CompressionLevel Optimal

$hashLines = foreach ($archive in @($withRuntimeZip, $withoutRuntimeZip)) {
    $hash = Get-FileHash -LiteralPath $archive -Algorithm SHA256
    "$($hash.Hash.ToLowerInvariant())  $([IO.Path]::GetFileName($archive))"
}
$hashLines | Set-Content -LiteralPath (Join-Path $releaseRoot "SHA256SUMS.txt") -Encoding ASCII

Write-Host "Release packages ready: $releaseRoot"
Get-ChildItem -LiteralPath $releaseRoot -File | Select-Object Name, Length
