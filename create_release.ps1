# GitHub Release Creator Script
# Автоматически создает релиз и загружает .exe файлы

param(
    [string]$Version = "1.0.0",
    [string]$Token = $env:GITHUB_TOKEN
)

# Цвета для вывода
$ErrorActionPreference = "Stop"

Write-Host "🚀 GitHub Release Creator для GameGiveawaysPro" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

# Проверка токена
if (-not $Token) {
    Write-Host "❌ Ошибка: GitHub Token не найден!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Создайте токен:" -ForegroundColor Yellow
    Write-Host "1. Откройте: https://github.com/settings/tokens/new" -ForegroundColor White
    Write-Host "2. Выберите: repo (full control)" -ForegroundColor White
    Write-Host "3. Скопируйте токен" -ForegroundColor White
    Write-Host ""
    Write-Host "Использование:" -ForegroundColor Yellow
    Write-Host "  .\create_release.ps1 -Token 'ваш_токен'" -ForegroundColor White
    Write-Host "  или" -ForegroundColor White
    Write-Host "  `$env:GITHUB_TOKEN='ваш_токен'" -ForegroundColor White
    Write-Host "  .\create_release.ps1" -ForegroundColor White
    exit 1
}

# Параметры
$owner = "TaJIanT"
$repo = "GameGiveawaysPro"
$tag = "v$Version"
$name = "GameGiveawaysPro v$Version"
$body = @"
## 🎮 GameGiveawaysPro v$Version

Первая стабильная версия трекера бесплатных игр!

### ✨ Возможности:
- 📊 Отслеживание бесплатных раздач игр с популярных платформ
- 🎯 Удобные вкладки: Все / Раздачи / Скидки
- 🔄 Автоматическое обновление данных
- 🎨 Современный темный интерфейс
- 🔔 Открытие ссылок на страницы игр одним кликом

### 📥 Установка:
1. Скачайте ``GameGiveawaysPro.exe``
2. Запустите файл - установка не требуется!
3. Автообновления работают автоматически

### 🛠️ Системные требования:
- Windows 10/11
- Подключение к интернету

---
**Первый релиз проекта!** Спасибо за использование! 🚀
"@

# Проверка наличия файлов
Write-Host "📦 Проверка файлов..." -ForegroundColor Yellow

$mainExe = "dist\GameGiveawaysPro.exe"
$updaterExe = "dist\updater.exe"

if (-not (Test-Path $mainExe)) {
    Write-Host "❌ Файл не найден: $mainExe" -ForegroundColor Red
    Write-Host "   Запустите сборку: .\build.ps1" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $updaterExe)) {
    Write-Host "❌ Файл не найден: $updaterExe" -ForegroundColor Red
    Write-Host "   Запустите сборку: .\build.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Найден: $mainExe ($(([System.IO.FileInfo]$mainExe).Length / 1MB).ToString('0.00') MB)" -ForegroundColor Green
Write-Host "✅ Найден: $updaterExe ($(([System.IO.FileInfo]$updaterExe).Length / 1MB).ToString('0.00') MB)" -ForegroundColor Green

# Создание релиза
Write-Host ""
Write-Host "📝 Создание релиза $tag..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "token $Token"
    "Accept" = "application/vnd.github.v3+json"
}

$releaseData = @{
    tag_name = $tag
    name = $name
    body = $body
    draft = $false
    prerelease = $false
} | ConvertTo-Json

try {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$repo/releases" `
        -Method Post `
        -Headers $headers `
        -Body $releaseData `
        -ContentType "application/json"
    
    Write-Host "✅ Релиз создан: $($release.html_url)" -ForegroundColor Green
    $uploadUrl = $release.upload_url -replace '\{\?name,label\}', ''
}
catch {
    Write-Host "❌ Ошибка создания релиза: $_" -ForegroundColor Red
    Write-Host "   Возможно, релиз $tag уже существует" -ForegroundColor Yellow
    
    # Попытка получить существующий релиз
    try {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$repo/releases/tags/$tag" `
            -Method Get `
            -Headers $headers
        
        Write-Host "ℹ️  Используется существующий релиз: $($release.html_url)" -ForegroundColor Cyan
        $uploadUrl = $release.upload_url -replace '\{\?name,label\}', ''
    }
    catch {
        Write-Host "❌ Не удалось получить релиз: $_" -ForegroundColor Red
        exit 1
    }
}

# Функция загрузки файла
function Upload-Asset {
    param(
        [string]$FilePath,
        [string]$UploadUrl,
        [hashtable]$Headers
    )
    
    $fileName = [System.IO.Path]::GetFileName($FilePath)
    $fileBytes = [System.IO.File]::ReadAllBytes($FilePath)
    $fileSize = $fileBytes.Length
    
    Write-Host "⬆️  Загрузка $fileName ($($fileSize / 1MB).ToString('0.00') MB)..." -ForegroundColor Yellow
    
    $uploadHeaders = $Headers.Clone()
    $uploadHeaders["Content-Type"] = "application/octet-stream"
    
    try {
        $asset = Invoke-RestMethod -Uri "$UploadUrl?name=$fileName" `
            -Method Post `
            -Headers $uploadHeaders `
            -Body $fileBytes
        
        Write-Host "✅ Загружено: $fileName" -ForegroundColor Green
        Write-Host "   URL: $($asset.browser_download_url)" -ForegroundColor Gray
        return $true
    }
    catch {
        Write-Host "❌ Ошибка загрузки $fileName`: $_" -ForegroundColor Red
        return $false
    }
}

# Загрузка файлов
Write-Host ""
Write-Host "📤 Загрузка файлов..." -ForegroundColor Yellow

$success1 = Upload-Asset -FilePath $mainExe -UploadUrl $uploadUrl -Headers $headers
$success2 = Upload-Asset -FilePath $updaterExe -UploadUrl $uploadUrl -Headers $headers

# Итог
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

if ($success1 -and $success2) {
    Write-Host "🎉 Релиз успешно создан и опубликован!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Ссылка: $($release.html_url)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Пользователи могут скачать:" -ForegroundColor White
    Write-Host "  • GameGiveawaysPro.exe" -ForegroundColor Gray
    Write-Host "  • updater.exe" -ForegroundColor Gray
} else {
    Write-Host "⚠️  Релиз создан с ошибками" -ForegroundColor Yellow
    Write-Host "   Проверьте файлы вручную: $($release.html_url)" -ForegroundColor Yellow
}
