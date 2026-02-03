# RALPH_TASK.md Specification

This document defines the format for task definition files used in the Ralph Wiggum methodology.

## File Location

Place `RALPH_TASK.md` in the project root directory.

## Structure

```markdown
---
task: Short description of what to build
test_command: "command to run tests"
browser_validation: true|false
base_url: "http://localhost:3000"
---

# Task: [Title]

[Optional description of the overall task]

## Success Criteria

1. [ ] First criterion - specific, testable outcome
2. [ ] Second criterion - another testable outcome
3. [ ] Third criterion - and so on

## Context

- Technology stack details
- API documentation links
- Constraints and requirements

## Notes

- Guidelines for the agent
- Special considerations
```

## Frontmatter Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `task` | string | Brief description of what to build (1-100 chars) |
| `test_command` | string | Shell command to validate work (e.g., `pytest`, `npm test`) |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `browser_validation` | boolean | `false` | Enable MCP browser tool validation |
| `base_url` | string | - | Base URL for browser testing |
| `max_iterations` | integer | `20` | Maximum iterations before stopping |
| `model` | string | - | Preferred model for this task |

## Success Criteria Format

### Rules

1. Use numbered list with checkbox syntax: `1. [ ] Criterion`
2. Each criterion must be:
   - **Specific** - Clear what "done" looks like
   - **Testable** - Can be verified programmatically or visually
   - **Atomic** - Completable in a single iteration (~80k tokens)
   - **Independent** - Minimal dependencies on other criteria (when possible)

3. Mark completed criteria: `1. [x] Criterion`

### Good Examples

```markdown
## Success Criteria

1. [ ] GET /health endpoint returns 200 with {"status": "ok"}
2. [ ] User model has fields: id, email, password_hash, created_at
3. [ ] Login form validates email format before submission
4. [ ] All tests pass with >80% coverage
```

### Bad Examples

```markdown
## Success Criteria

1. [ ] Make it work  # Too vague
2. [ ] Build the entire authentication system  # Too large
3. [ ] Fix bugs  # Not specific
4. [ ] Improve performance  # Not testable
```

## Context Section

Provide information the agent needs:

```markdown
## Context

### Tech Stack
- Python 3.11+ with FastAPI
- PostgreSQL 17 for database
- Redis for caching

### APIs
- Grocy API: https://demo.grocy.info/api
- Open Food Facts: https://world.openfoodfacts.org/api/v0/product/{barcode}.json

### Constraints
- Must work offline with sync queue
- Mobile-first responsive design
- Maximum 10 second load time
```

## Notes Section

Include guidance for the agent:

```markdown
## Notes

- Run `docker-compose up -d` before testing
- Use existing auth patterns from src/auth/
- Commit after each criterion with `ralph: ` prefix
- Browser validation required for UI criteria (6-8)
```

## Complete Example

```markdown
---
task: Build user authentication for GrocyScan
test_command: "pytest tests/ -v --cov=src"
browser_validation: true
base_url: "http://localhost:8000"
---

# Task: User Authentication

Implement secure user authentication with JWT tokens and session management.

## Success Criteria

1. [ ] User model with email, password_hash, created_at fields
2. [ ] POST /auth/register creates new user with hashed password
3. [ ] POST /auth/login returns JWT token for valid credentials
4. [ ] Protected endpoints return 401 without valid token
5. [ ] Login page renders with email and password fields
6. [ ] Login form shows validation errors for invalid input
7. [ ] Successful login redirects to dashboard
8. [ ] All tests pass with >80% coverage

## Context

### Tech Stack
- FastAPI with Pydantic models
- SQLAlchemy ORM with PostgreSQL
- python-jose for JWT handling
- passlib for password hashing

### Security Requirements
- Passwords must be hashed with bcrypt
- JWT tokens expire after 24 hours
- Rate limit login attempts to 5 per minute

## Notes

- Criteria 5-7 require browser validation
- Use existing database connection from src/db.py
- Follow auth patterns from FastAPI documentation
```

## Validation

The task file is valid when:

1. Frontmatter contains required `task` and `test_command` fields
2. At least one success criterion exists with `[ ]` checkbox
3. Criteria are numbered sequentially
4. No duplicate criterion numbers
