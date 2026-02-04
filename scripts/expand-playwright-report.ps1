# Expand a Playwright report zip into test-artifacts and open it.
# Usage: .\scripts\expand-playwright-report.ps1 [path-to-report.zip]
# Default: playwright-report.zip in repo root (e.g. downloaded from CI).

param(
    [string]$ZipPath = (Join-Path $PSScriptRoot "..\playwright-report.zip")
)

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutDir = Join-Path $RepoRoot "test-artifacts\playwright-report"

if (-not (Test-Path $ZipPath)) {
    Write-Error "Zip not found: $ZipPath"
    Write-Host "Download from GitHub Actions (UI Tests → Artifacts → playwright-report) or run E2E locally to produce the zip."
    exit 1
}

if (-not (Test-Path (Join-Path $RepoRoot "test-artifacts"))) {
    New-Item -ItemType Directory -Path (Join-Path $RepoRoot "test-artifacts") -Force | Out-Null
}

Expand-Archive -Path $ZipPath -DestinationPath $OutDir -Force
Write-Host "Expanded to $OutDir"
Write-Host "Open: $OutDir\index.html"
Write-Host "Or run: npx playwright show-report $OutDir"
Start-Process (Join-Path $OutDir "index.html")
