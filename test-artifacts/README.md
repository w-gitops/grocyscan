# Test artifacts (untracked)

Drop CI or local test artifacts here to expand and analyze. This folder is gitignored.

## Playwright report

1. Download `playwright-report.zip` from GitHub Actions (UI Tests job → Artifacts) or copy to repo root.
2. From repo root, run:
   ```powershell
   .\scripts\expand-playwright-report.ps1
   ```
   or (Linux/macOS) `./scripts/expand-playwright-report.sh`
   Optional: pass a path to the zip as the first argument.
3. The report is extracted to `test-artifacts/playwright-report/` and the HTML report opens. Or run: `npx playwright show-report test-artifacts/playwright-report`

## Other artifacts

- **Pytest / coverage**: Drop `htmlcov/` or coverage archives here and open `index.html`.
- **Traces**: Playwright trace zips can go here; use `npx playwright show-trace <path-to.zip>`.
