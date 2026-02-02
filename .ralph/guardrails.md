# Guardrails (Signs)

Lessons learned from previous iterations. Read this FIRST before starting work.

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
