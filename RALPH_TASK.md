---
task: Build GrocyScan - a barcode scanning app for Grocy inventory management
test_command: "python -m pytest tests/ -v"
---

# Task: GrocyScan

Build a Python application that scans grocery barcodes and integrates with Grocy for inventory management.

## Success Criteria

1. [ ] Project initialized with pyproject.toml and dependencies
2. [ ] Basic CLI structure with click or typer
3. [ ] Barcode lookup via Open Food Facts API
4. [ ] Grocy API client for inventory operations
5. [ ] Scan command: lookup barcode → find/create product in Grocy
6. [ ] Add command: add scanned item to Grocy inventory
7. [ ] Configuration file support (.env or config.yaml)
8. [ ] Unit tests for core functionality
9. [ ] Error handling and user-friendly messages
10. [ ] README with setup and usage instructions

## Context

- Use Python 3.12+
- Use httpx for API calls
- Use pydantic for data validation
- Grocy API docs: https://demo.grocy.info/api
- Open Food Facts API: https://world.openfoodfacts.org/api/v0/product/{barcode}.json

## Notes

- Each criterion should be completable in a single iteration
- Commit after completing each criterion
- Update progress.md after each work session
