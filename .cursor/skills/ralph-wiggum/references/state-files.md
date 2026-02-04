# State Files Specification

The `.ralph/` directory contains state files that persist across sessions. This is the "memory" of the Ralph Wiggum methodology.

## Directory Structure

```
.ralph/
├── progress.md      # Session history and accomplishments
├── guardrails.md    # Lessons learned (Signs)
├── activity.log     # Tool call traces (automation)
├── errors.log       # Failure records (automation)
├── screenshots/     # Browser validation evidence
└── .iteration       # Current iteration counter (automation)
```

## progress.md

Tracks what has been accomplished across sessions.

### Format

```markdown
# Progress Log

## Session 1 (2024-02-02)

### Completed
- [x] Criterion 1 - Initialize project structure
  - Commit: abc1234
  - Notes: Created FastAPI app with basic structure

- [x] Criterion 2 - Add health endpoint
  - Commit: def5678
  - Notes: GET /health returns {"status": "ok"}

### Browser Validations
- Health endpoint accessible at http://localhost:8000/health
- Response time under 100ms

### Blockers Encountered
- None

---

## Session 2 (2024-02-03)

### Completed
- [x] Criterion 3 - User model
  - Commit: ghi9012
  - Screenshot: .ralph/screenshots/user-model-test.png

### Current Focus
Working on Criterion 4 - Registration endpoint

### Blockers Encountered
- Database migration tool not configured (resolved)
```

### Update Rules

1. Create new session header at start of each session
2. Add completed criteria with commit hash
3. Include screenshot references for UI validations
4. Note any blockers and their resolution
5. Update "Current Focus" when switching criteria

## guardrails.md

Contains lessons learned from failures. The agent reads this FIRST before starting work.

### Format

```markdown
# Guardrails (Signs)

Lessons learned from previous iterations. Read this FIRST before starting work.

## Active Guardrails

### Sign: Check imports before adding new ones
- **Trigger**: Adding a new import statement
- **Instruction**: First search the file for existing imports of the same module
- **Evidence**: Duplicate import caused lint failure
- **Added after**: Session 2 - Import collision in auth.py

### Sign: Run migrations before testing database changes
- **Trigger**: Modifying database models
- **Instruction**: Run `alembic upgrade head` before running tests
- **Evidence**: Tests failed with "table does not exist"
- **Added after**: Session 3 - Missing migration step

## Resolved Guardrails

<!-- Move guardrails here when the underlying issue is permanently fixed -->
```

### Guardrail Structure

Each guardrail must have:

| Field | Required | Description |
|-------|----------|-------------|
| **Trigger** | Yes | When this guardrail applies |
| **Instruction** | Yes | What to do instead |
| **Evidence** | No | Screenshot, log, or error message |
| **Added after** | Yes | Session/iteration and reason |

## screenshots/

Directory for browser validation evidence. Naming: `criterion-N.png`, `criterion-N-description.png`, or `error-001.png`.

## Git Integration

### What to Track

| File | Git Status | Reason |
|------|------------|--------|
| progress.md | ✅ Track | Persists accomplishments |
| guardrails.md | ✅ Track | Persists lessons learned |
| activity.log | ❌ Ignore | Too verbose, regenerated |
| errors.log | ❌ Ignore | Temporary debugging |
| screenshots/ | Project choice | Evidence; may be ignored if large |
| .iteration | ❌ Ignore | Runtime state only |
