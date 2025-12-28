#requires -Version 5.1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Не найден $py" }

& $py -m py_compile ".\main.py" ".\update_check.py" ".\updater.py"

Remove-Item ".\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\dist"  -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\*.spec" -Force -ErrorAction SilentlyContinue

& $py -m PyInstaller --noconfirm --clean --onefile --windowed --name "GameGiveawaysPro" ".\main.py"
& $py -m PyInstaller --noconfirm --clean --onefile --windowed --name "updater" ".\updater.py"
& $py -m PyInstaller --noconfirm --clean --onefile --console  --debug=all --name "GameGiveawaysPro_debug" ".\main.py"

Get-ChildItem ".\dist" -File | Select-Object Name, Length, LastWriteTime
