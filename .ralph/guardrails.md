# Guardrails (Signs)

Lessons learned from previous iterations. **READ THIS FIRST** before starting work.

---

## Project Context

- **Project:** Homebot (home inventory management)
- **Tech Stack:** FastAPI, Vue 3 + Quasar, PostgreSQL with RLS
- **Deploy Target:** `192.168.200.37` via SSH
- **PRD Location:** `prd/` directory with Johnny Decimal numbering

---

## Active Guardrails

### Sign: Always Set Tenant Context
- **Trigger**: Any database query
- **Instruction**: Set `app.tenant_id` in PostgreSQL session before queries; RLS policies depend on this
- **Added after**: Multi-tenant design decision

### Sign: Deploy Before Testing
- **Trigger**: After making code changes
- **Instruction**: Deploy to remote server before testing; local machine doesn't run the service
- **Added after**: Development workflow defined

### Sign: Use Johnny Decimal PRD References
- **Trigger**: Looking up requirements or specifications
- **Instruction**: PRD documents are in `prd/` with format `XX.XX-name.md` (e.g., `30.11-data-models.md`)
- **Added after**: PRD reorganization

### Sign: Check Phase Document for Criteria
- **Trigger**: Starting a new phase or resuming work
- **Instruction**: The detailed criteria are in `prd/80.1X-ralph-phase-N-*.md`, not just RALPH_TASK.md
- **Added after**: Phase documentation structure

### Sign: Commit with Ralph Prefix
- **Trigger**: Completing a criterion
- **Instruction**: Use format `ralph: [N] description` where N is criterion number
- **Added after**: Git workflow standard

### Sign: BrowserMCP Snapshot Before Click
- **Trigger**: Interacting with browser for UI testing
- **Instruction**: Always call `browser_snapshot` to get element refs before `browser_click` or `browser_type`
- **Added after**: BrowserMCP integration

---

## Legacy Guardrails (from GrocyScan v1)

### Sign: Check imports before adding
- **Trigger**: Adding a new import statement
- **Instruction**: First check if import already exists in file
- **Added after**: Iteration 3 - duplicate import caused lint failure

---

## Known Limitations

- **Review dialog**: Product images may not display if lookup provider doesn't return image_url
- **Grocy compatibility**: Some endpoints may behave differently from vanilla Grocy

---

## Adding New Guardrails

When you encounter a failure that should be prevented in the future, add a new sign:

```markdown
### Sign: [Short description]
- **Trigger**: When this situation occurs
- **Instruction**: What to do instead
- **Evidence**: Error message or screenshot
- **Added after**: Iteration N - reason
```
