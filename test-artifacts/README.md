# Test artifacts (untracked)

Drop CI or local test artifacts here to expand and analyze. This folder is gitignored.

## Playwright report

1. Download `playwright-report.zip` from GitHub Actions (UI Tests job → Artifacts) and put it in `test-artifacts/` or repo root.
2. From repo root, run:
   ```powershell
   .\scripts\expand-playwright-report.ps1
   ```
   or (Linux/macOS) `./scripts/expand-playwright-report.sh`  
   Optional: pass a path to the zip as the first argument.
3. The script **replaces** any existing report in `test-artifacts/playwright-report/`, **deletes the zip** after expanding, and opens the HTML report. Or run: `npx playwright show-report test-artifacts/playwright-report`

### E2E run log (for analysis)

From the same UI Tests run, download the **e2e-run-log** artifact (plain text). Save it in `test-artifacts/` (e.g. `e2e-run.log`). It contains the full test console output (passed/failed/skipped, error messages, stack traces) so you or tooling can grep/analyze without opening the HTML report.

## Other artifacts

- **Pytest / coverage**: Drop `htmlcov/` or coverage archives here and open `index.html`.
- **Traces**: Playwright trace zips can go here; use `npx playwright show-trace <path-to.zip>`.
