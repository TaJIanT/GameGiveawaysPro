param(
    [string]$Version = "1.0.0",
    [string]$Token = $env:GITHUB_TOKEN
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 GitHub Release Creator" -ForegroundColor Cyan

if (-not $Token) {
    Write-Host " GitHub Token не найден!" -ForegroundColor Red
    exit 1
}

$owner = "TaJIanT"
$repo = "GameGiveawaysPro"
$tag = "v$Version"
$name = "GameGiveawaysPro v$Version"

$body = @"
##  GameGiveawaysPro v$Version

Первая стабильная версия трекера бесплатных игр!

###  Возможности:
-  Отслеживание бесплатных раздач игр
-  Удобные вкладки: Все / Раздачи / Скидки
-  Автоматическое обновление
-  Современный интерфейс

###  Установка:
1. Скачайте GameGiveawaysPro.exe
2. Запустите файл
3. Готово!
"@

Write-Host " Проверка файлов..." -ForegroundColor Yellow

$mainExe = "dist\GameGiveawaysPro.exe"
$updaterExe = "dist\updater.exe"

if (-not (Test-Path $mainExe)) {
    Write-Host " Файл не найден: $mainExe" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $updaterExe)) {
    Write-Host " Файл не найден: $updaterExe" -ForegroundColor Red
    exit 1
}

Write-Host " Найден: $mainExe" -ForegroundColor Green
Write-Host " Найден: $updaterExe" -ForegroundColor Green

Write-Host "`n Создание релиза..." -ForegroundColor Yellow

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
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$repo/releases" -Method Post -Headers $headers -Body $releaseData -ContentType "application/json"
    Write-Host " Релиз создан!" -ForegroundColor Green
    $uploadUrl = $release.upload_url -replace '\{\?name,label\}', ''
} catch {
    try {
        $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$owner/$repo/releases/tags/$tag" -Method Get -Headers $headers
        Write-Host "ℹ Используется существующий релиз" -ForegroundColor Cyan
        $uploadUrl = $release.upload_url -replace '\{\?name,label\}', ''
    } catch {
        Write-Host " Ошибка: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n Загрузка файлов..." -ForegroundColor Yellow

$uploadHeaders = $headers.Clone()
$uploadHeaders["Content-Type"] = "application/octet-stream"

# Загрузка GameGiveawaysPro.exe
$fileName1 = "GameGiveawaysPro.exe"
$fileBytes1 = [System.IO.File]::ReadAllBytes($mainExe)
Write-Host " Загрузка $fileName1..." -ForegroundColor Yellow

try {
    Invoke-RestMethod -Uri "$uploadUrl?name=$fileName1" -Method Post -Headers $uploadHeaders -Body $fileBytes1 | Out-Null
    Write-Host " Загружено: $fileName1" -ForegroundColor Green
} catch {
    Write-Host " Ошибка: $_" -ForegroundColor Red
}

# Загрузка updater.exe
$fileName2 = "updater.exe"
$fileBytes2 = [System.IO.File]::ReadAllBytes($updaterExe)
Write-Host " Загрузка $fileName2..." -ForegroundColor Yellow

try {
    Invoke-RestMethod -Uri "$uploadUrl?name=$fileName2" -Method Post -Headers $uploadHeaders -Body $fileBytes2 | Out-Null
    Write-Host " Загружено: $fileName2" -ForegroundColor Green
} catch {
    Write-Host " Ошибка: $_" -ForegroundColor Red
}

Write-Host "`n Готово!" -ForegroundColor Green
Write-Host " $($release.html_url)" -ForegroundColor Cyan
