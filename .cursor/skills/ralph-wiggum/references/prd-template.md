# PRD Template for Ralph Wiggum Methodology

This document provides a template section for PRDs that enables Ralph Wiggum autonomous development.

## Usage

When creating a new PRD, include the `00-Standards-of-Development.md` document as the first section. This establishes the development methodology before diving into requirements.

## PRD Structure with Ralph

```
prd/
├── 00-Standards-of-Development.md  # Development methodology (this template)
├── 01-executive-summary.md         # Vision, problem, solution
├── 02-user-stories.md              # User requirements
├── 03-technical-architecture.md    # System design
├── 04-api-specification.md         # API contracts
├── ...
└── RALPH_TASK.md                   # Generated task file (project root)
```

## Converting PRD to RALPH_TASK.md

### Step 1: Identify Deliverables

From each PRD section, extract concrete deliverables (features, endpoints, models, UI).

### Step 2: Create Success Criteria

Transform deliverables into testable criteria: specific, atomic, numbered with `[ ]` checkboxes.

### Step 3: Order by Dependencies

Infrastructure first, then core logic, then UI, then integration.

### Step 4: Add Frontmatter

```yaml
---
task: Short task description
test_command: "pytest tests/ -v"
browser_validation: true
base_url: "http://localhost:8000"
---
```

## Quality Gates

Before marking a criterion complete:

1. ✅ Code implemented and compiles
2. ✅ Tests pass (`test_command` succeeds)
3. ✅ Browser validation passes (if UI criterion)
4. ✅ Changes committed with `ralph: ` prefix
5. ✅ Progress updated in `.ralph/progress.md`

## State Files

| File | Purpose |
|------|---------|
| `progress.md` | Session history and accomplishments |
| `guardrails.md` | Lessons learned from failures |
| `screenshots/` | Browser validation evidence |

## Failure Handling

1. Don't repeat the same approach
2. Add a guardrail to `.ralph/guardrails.md`
3. Try a different approach or move on
4. If stuck 3+ times, signal `<ralph>GUTTER</ralph>`
