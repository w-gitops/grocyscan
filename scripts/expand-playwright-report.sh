#!/usr/bin/env bash
# Expand a Playwright report zip into test-artifacts and open it.
# Usage: ./scripts/expand-playwright-report.sh [path-to-report.zip]
# Default: playwright-report.zip in repo root (e.g. downloaded from CI).

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ZIP_PATH="${1:-$REPO_ROOT/playwright-report.zip}"
OUT_DIR="$REPO_ROOT/test-artifacts/playwright-report"

if [ ! -f "$ZIP_PATH" ]; then
  echo "Zip not found: $ZIP_PATH" >&2
  echo "Download from GitHub Actions (UI Tests → Artifacts → playwright-report) or run E2E locally to produce the zip."
  exit 1
fi

mkdir -p "$REPO_ROOT/test-artifacts"
unzip -o "$ZIP_PATH" -d "$OUT_DIR"
echo "Expanded to $OUT_DIR"
echo "Open: $OUT_DIR/index.html"
echo "Or run: npx playwright show-report $OUT_DIR"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$OUT_DIR/index.html"
elif command -v open >/dev/null 2>&1; then
  open "$OUT_DIR/index.html"
fi
