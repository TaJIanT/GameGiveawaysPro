param(
  [string]$Repo = "TaJIanT/GameGiveawaysPro",
  [string]$Version = "1.0.1",
  [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

# Проверка gh
gh auth status | Out-Null

# Если идет rebase — стоп
if (Test-Path (Join-Path ".git" "rebase-merge")) {
  throw "Rebase in progress. Finish it: git rebase --continue OR abort: git rebase --abort"
}

# Build
.\build.ps1

$mainExe = "dist\GameGiveawaysPro.exe"
$updExe  = "dist\updater.exe"
if (!(Test-Path $mainExe)) { throw "Not found: $mainExe" }
if (!(Test-Path $updExe))  { throw "Not found: $updExe" }

$tag   = "v$Version"
$title = "GameGiveawaysPro $tag"

$notes = @"
### Исправления
- Исправлены уведомления о новых бесплатных раздачах (история просмотра + окно уведомления).
- Исправлена пометка скоро закончится и обновление списка.
- Исправлена стабильность запуска/работы трея.

### Техническое
- Обновлены зависимости.
"@

# Release create/update
$exists = $false
try { gh release view $tag -R $Repo | Out-Null; $exists = $true } catch { $exists = $false }

if (-not $exists) {
  gh release create $tag $mainExe $updExe -R $Repo -t $title -n $notes --latest
} else {
  gh release upload $tag $mainExe $updExe -R $Repo --clobber
  gh release edit $tag -R $Repo -t $title -n $notes
}
