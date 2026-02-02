# Guardrails (Signs)

Lessons learned from previous iterations. Read this FIRST before starting work.

## Known UI Limitations (documented, not bugs)

- **Review dialog**: Product images are not shown in the scan Review Product dialog (lookup may not return image_url, or UI does not render it).
- **Products page detail popup**: Grocy product detail popup does not show UPC/barcode; barcodes are in Grocy’s product_barcodes API and are not yet fetched or displayed there.

See `.cursor/plans/browsermcp_ui_testing_plan_*.plan.md` for Scanner Gun Mode test procedure and known issues.

## Active Guardrails

<!-- Add lessons learned here in this format:

### Sign: [Short description]
- **Trigger**: When this situation occurs
- **Instruction**: What to do instead
- **Added after**: Which iteration and why

-->

## Example Format

### Sign: Check imports before adding
- **Trigger**: Adding a new import statement
- **Instruction**: First check if import already exists in file
- **Added after**: Iteration 3 - duplicate import caused lint failure
