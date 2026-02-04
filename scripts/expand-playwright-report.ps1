# Expand a Playwright report zip into test-artifacts and open it.
# Always replaces existing report. Removes the zip after expanding.
# Usage: .\scripts\expand-playwright-report.ps1 [path-to-report.zip]
# Default: looks in test-artifacts\ then repo root for playwright-report.zip.

param(
    [string]$ZipPath = ""
)

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutDir = Join-Path $RepoRoot "test-artifacts\playwright-report"

if (-not $ZipPath) {
    $InArtifacts = Join-Path $RepoRoot "test-artifacts\playwright-report.zip"
    $InRoot = Join-Path $RepoRoot "playwright-report.zip"
    $ZipPath = if (Test-Path $InArtifacts) { $InArtifacts } else { $InRoot }
}

if (-not (Test-Path $ZipPath)) {
    Write-Error "Zip not found. Put playwright-report.zip in test-artifacts\ or repo root."
    Write-Host "Download from GitHub Actions (UI Tests → Artifacts → playwright-report) or run E2E locally."
    exit 1
}

$ArtifactsDir = Join-Path $RepoRoot "test-artifacts"
if (-not (Test-Path $ArtifactsDir)) {
    New-Item -ItemType Directory -Path $ArtifactsDir -Force | Out-Null
}

# Always replace stale report
if (Test-Path $OutDir) {
    Remove-Item -Path $OutDir -Recurse -Force
}
Expand-Archive -Path $ZipPath -DestinationPath $OutDir -Force
Remove-Item -Path $ZipPath -Force
Write-Host "Expanded to $OutDir (zip removed)."
Write-Host "Open: $OutDir\index.html"
Write-Host "Or run: npx playwright show-report $OutDir"
Start-Process (Join-Path $OutDir "index.html")
