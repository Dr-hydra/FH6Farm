# FH6Farm QING.UIKIT Frontend

This branch keeps the Python automation core and adds a VB.NET/WPF frontend based on QING.UIKIT.

## Architecture

- `main.py`: legacy CustomTkinter app and current automation implementation.
- `fh6auto_core/`: headless entry and shared non-UI helpers.
- `ui/FH6Auto.UI.sln`: WPF frontend using QING.UIKIT controls and shell.
- `ui/src/QING.UIKIT/Modules/FH6CoreBridge.vb`: starts and stops the Python core process.
- `FH6AutoCore.exe`: bundled PyInstaller headless core generated in release packages.

In development, the WPF frontend launches:

```powershell
python -u -m fh6auto_core.headless --start race
```

In release packages, the frontend first uses `FH6AutoCore.exe` from the same folder. If that exe is missing, it falls back to the Python module command above.

The `--start` value can be `race`, `buy`, `cj`, or `sell`.

## Development Run

```powershell
dotnet run --project .\ui\src\QING.UIKIT\QING.UIKIT.vbproj
```

## Verify

```powershell
.\scripts\verify.ps1
```

Include release packaging:

```powershell
.\scripts\verify.ps1 -Release
```

## Build Release Package

```powershell
.\scripts\build-release.ps1
```

Output:

```text
dist\release\
```

The build creates two minimal packages:

- `with-runtime`: self-contained WPF frontend; no .NET installation required.
- `without-runtime`: requires the .NET 10 Desktop Runtime for Windows x64.

Each package contains only:

```text
FH6Farm.exe
FH6AutoCore.exe
config.json
```

The Python automation core is bundled in both variants, so neither package requires a local Python installation.

## Attribution

Original automation project: [`YOUSTHEONE/FH6Auto`](https://github.com/YOUSTHEONE/FH6Auto).

Original author: `YOUSTHEONE / YSTO`.

UI development and frontend/core integration: `Dr.Hydra`.

The WPF UI is built with QING.UIKIT and preserves the original Python automation core.

The UI layout and interaction design reference PCL (Plain Craft Launcher). This project is not affiliated with or endorsed by PCL.
