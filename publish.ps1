param(
  [string]$Repo = "TaJIanT/GameGiveawaysPro",
  [string]$Version = "1.0.4",
  [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

# Проверка gh
gh auth status | Out-Null

# Build
.\build.ps1

$mainExe = "dist\GameGiveawaysPro.exe"
$updExe  = "dist\updater.exe"
if (!(Test-Path $mainExe)) { throw "Not found: $mainExe" }
if (!(Test-Path $updExe))  { throw "Not found: $updExe" }

$tag   = "v$Version"
$title = "GameGiveawaysPro $tag"

$notes = @"
## 🚀 GameGiveawaysPro v1.0.4 — Большое обновление!

Мы прокачали программу, чтобы вы экономили еще больше! 💰

### ✨ Что нового:
- 💰 **Умный Калькулятор**: Теперь программа считает общую стоимость всех раздаваемых игр и показывает вашу выгоду прямо в главном окне!
- 🎯 **Тихий снайпер**: Фоновый сканер работает полностью автоматически. Сверните программу, и она сама пришлет уведомление со звуком, если появится годная халява.
- 🔗 **Умные кнопки**: Для Steam-игр теперь доступно прямое открытие прямо в клиенте Steam на вашем ПК. Epic Games и GOG получили собственные стильные кнопки!

### 🛠️ Техническое:
- Убраны тестовые уведомления, сканер переведен в автономный режим.
- Оптимизирована логика подсчета цен.

### 📥 Как обновиться?
Просто скачайте новый ``GameGiveawaysPro.exe`` ниже и запустите его.
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

Write-Host "✅ Релиз v$Version успешно опубликован на GitHub!" -ForegroundColor Green