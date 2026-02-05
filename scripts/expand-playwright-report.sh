#!/usr/bin/env bash
# Expand a Playwright report zip into test-artifacts and open it.
# Always replaces existing report. Removes the zip after expanding.
# Usage: ./scripts/expand-playwright-report.sh [path-to-report.zip]
# Default: looks in test-artifacts/ then repo root for playwright-report.zip.

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$REPO_ROOT/test-artifacts/playwright-report"

if [ -n "$1" ]; then
  ZIP_PATH="$1"
else
  if [ -f "$REPO_ROOT/test-artifacts/playwright-report.zip" ]; then
    ZIP_PATH="$REPO_ROOT/test-artifacts/playwright-report.zip"
  else
    ZIP_PATH="$REPO_ROOT/playwright-report.zip"
  fi
fi

if [ ! -f "$ZIP_PATH" ]; then
  echo "Zip not found. Put playwright-report.zip in test-artifacts/ or repo root." >&2
  echo "Download from GitHub Actions (UI Tests → Artifacts → playwright-report) or run E2E locally."
  exit 1
fi

mkdir -p "$REPO_ROOT/test-artifacts"
rm -rf "$OUT_DIR"
unzip -o "$ZIP_PATH" -d "$OUT_DIR"
rm -f "$ZIP_PATH"
echo "Expanded to $OUT_DIR (zip removed)."
echo "Open: $OUT_DIR/index.html"
echo "Or run: npx playwright show-report $OUT_DIR"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$OUT_DIR/index.html"
elif command -v open >/dev/null 2>&1; then
  open "$OUT_DIR/index.html"
fi
