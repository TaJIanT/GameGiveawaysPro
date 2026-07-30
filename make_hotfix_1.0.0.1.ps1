param(
  [string]$Repo = "TaJIanT/GameGiveawaysPro",
  [string]$Branch = "main",
  [string]$TargetLatestTag = "v1.0.1",
  [string]$HotfixTag = "v1.0.0.1",
  [string]$HotfixVersion = "1.0.0.1",
  [string]$AssetMain = "GameGiveawaysPro.exe",
  [string]$AssetUpdater = "updater.exe"
)

$ErrorActionPreference = "Stop"
Set-Location "C:\GameGiveawaysPro"

function Info($m){ Write-Host $m -ForegroundColor Cyan }
function Ok($m){ Write-Host $m -ForegroundColor Green }
function Warn($m){ Write-Host $m -ForegroundColor Yellow }

if ([string]::IsNullOrWhiteSpace($Repo) -or $Repo -notmatch '.+/.+') { throw "Repo must be OWNER/REPO" }
if ([string]::IsNullOrWhiteSpace($TargetLatestTag)) { throw "TargetLatestTag is empty" }
if ([string]::IsNullOrWhiteSpace($HotfixTag)) { throw "HotfixTag is empty" }

$Owner, $RepoName = $Repo.Split("/")

Info "Check releases/latest..."
$latest = gh api "/repos/$Owner/$RepoName/releases/latest" | ConvertFrom-Json
if ($latest.tag_name -ne $TargetLatestTag) { throw "Latest tag is '$($latest.tag_name)', expected '$TargetLatestTag'." }
Ok "OK: latest tag is $($latest.tag_name)"

$names = @($latest.assets | ForEach-Object { $_.name })
if (-not ($names -contains $AssetMain)) { throw "Latest missing asset: $AssetMain" }
if (-not ($names -contains $AssetUpdater)) { throw "Latest missing asset: $AssetUpdater" }
Ok "OK: latest has required assets"

Info "Sync branch..."
git fetch origin
git checkout $Branch | Out-Null
git pull --ff-only origin $Branch

Info "Patch config.py APP_VERSION..."
(Get-Content .\config.py -Raw) -replace 'APP_VERSION\s*=\s*".*?"', ('APP_VERSION = "' + $HotfixVersion + '"') |
  Set-Content .\config.py -Encoding UTF8

Info "Patch main.py: early check_and_update before any heavy imports..."
$mainPath = Join-Path $PWD "main.py"
$main = Get-Content $mainPath -Raw

$earlyBlock = @"
# --- early self-update (must be before any heavy imports) ---
try:
    from update_check import check_and_update
    import sys
    if check_and_update():
        raise SystemExit(0)
except Exception:
    pass
# -----------------------------------------------------------

"@

if ($main -notmatch "early self-update") {
  $main = $main -replace "^\s*from update_check import check_and_update\s*\r?\n", ""
  $main = $earlyBlock + $main
  Set-Content -Path $mainPath -Value $main -Encoding UTF8
} else {
  Warn "main.py already contains early self-update block"
}

Info "Commit + push..."
git add -u
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
  git commit -m "Bootstrap updater hotfix $HotfixTag"
  git push origin $Branch
} else {
  Warn "No tracked changes to commit (already patched?)"
}

Info "Tag + push tag..."
git show-ref --tags --verify ("refs/tags/" + $HotfixTag) *> $null
if ($LASTEXITCODE -ne 0) {
  git tag -a $HotfixTag -m "Bootstrap updater hotfix ($HotfixTag)"
}
git push origin $HotfixTag

Info "Build..."
.\build.ps1

$mainExe = "dist\$AssetMain"
$updExe  = "dist\$AssetUpdater"
if (!(Test-Path $mainExe)) { throw "Not found: $mainExe" }
if (!(Test-Path $updExe))  { throw "Not found: $updExe" }

Info "Publish release $HotfixTag..."
$notesFile = Join-Path $PWD ("RELEASE_NOTES_" + $HotfixTag + ".md")
@"
## $HotfixTag (bootstrap)

Запусти один раз  приложение сразу проверит обновления и автоматически обновится до $TargetLatestTag.

Assets:
- $AssetMain
- $AssetUpdater
"@ | Set-Content -Path $notesFile -Encoding UTF8

$exists = $false
try { gh release view $HotfixTag -R $Repo | Out-Null; $exists = $true } catch { $exists = $false }

if (-not $exists) {
  gh release create $HotfixTag $mainExe $updExe -R $Repo -t "GameGiveawaysPro $HotfixTag" -F $notesFile
} else {
  gh release upload $HotfixTag $mainExe $updExe -R $Repo --clobber
  gh release edit $HotfixTag -R $Repo -t "GameGiveawaysPro $HotfixTag" -F $notesFile
}

Ok "DONE: published $HotfixTag"
