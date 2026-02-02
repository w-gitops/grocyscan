# 13. Project Standards

> **See Also:** [Standards of Development](00-Standards-of-Development.md) for the development methodology (Ralph Wiggum protocol) and consolidated reference for AI agents.

## 13.1 Standards Directory Structure

```
docs/standards/
├── README.md                 # Overview and index
├── VERSIONING.md             # Semantic versioning rules
├── CHANGELOG.md              # Changelog maintenance
├── COMMIT_MESSAGES.md        # Conventional commits
├── LOGGING.md                # Logging standards
├── TESTING.md                # Testing requirements
├── DATABASE.md               # Schema evolution rules
├── API.md                    # REST API conventions
├── UI_COMPONENTS.md          # NiceGUI/AG Grid patterns
├── PRD_TEMPLATE.md           # PRD structure
├── USER_STORY_TEMPLATE.md    # User story format
└── CODE_STYLE.md             # Python style guide
```

## 13.2 Semantic Versioning

### Format: MAJOR.MINOR.PATCH

| Component | When to Increment |
|-----------|-------------------|
| **MAJOR** | Breaking API changes |
| **MINOR** | New features, backwards compatible |
| **PATCH** | Bug fixes, backwards compatible |

### Pre-release Tags
- Alpha: `1.0.0-alpha.1`
- Beta: `1.0.0-beta.1`
- Release Candidate: `1.0.0-rc.1`

## 13.3 Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

### Scopes
`api`, `ui`, `db`, `lookup`, `llm`, `grocy`, `scanner`, `cache`, `auth`, `logging`

### Examples
```
feat(lookup): add Brave Search API provider
fix(scanner): handle empty barcode input
docs(standards): add commit message conventions
```

## 13.4 User Story Template

| Field | Content |
|-------|---------|
| **ID** | US-XXX |
| **Title** | Brief description |
| **As a** | User role |
| **I want to** | Action/feature |
| **So that** | Benefit/value |
| **Acceptance Criteria** | Testable conditions |
| **Priority** | P0/P1/P2 |

### Example

| Field | Content |
|-------|---------|
| **ID** | US-42 |
| **Title** | Camera barcode scanning |
| **As a** | user |
| **I want to** | scan barcodes with my phone camera |
| **So that** | I can quickly add products without typing |
| **Acceptance Criteria** | 1. Camera opens within 1s<br>2. Barcode detected within 2s<br>3. Visual/audio feedback on scan |
| **Priority** | P0 |

## 13.5 Logging Standards

### Log Format (JSON)

```json
{
  "timestamp": "2026-02-02T00:15:32.123456Z",
  "level": "INFO",
  "message": "Barcode scan completed",
  "logger": "grocyscan.services.lookup",
  "trace_id": "abc123...",
  "span_id": "def456...",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "barcode": "012345678901",
  "provider": "openfoodfacts",
  "duration_ms": 234
}
```

### Log Levels

| Level | Usage |
|-------|-------|
| **DEBUG** | Detailed diagnostic information |
| **INFO** | Normal operations, business events |
| **WARNING** | Unexpected but recoverable situations |
| **ERROR** | Errors that prevented operation completion |
| **CRITICAL** | System-wide failures |

## 13.6 Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints for all function parameters and returns
- Maximum line length: 100 characters
- Use docstrings for all public functions and classes
- Use `black` for formatting
- Use `ruff` for linting

### Example

```python
from typing import Optional
from uuid import UUID


async def lookup_barcode(
    barcode: str,
    include_nutrition: bool = True,
) -> Optional[ProductDetail]:
    """
    Look up product information by barcode.
    
    Args:
        barcode: The barcode to look up (UPC, EAN, etc.)
        include_nutrition: Whether to include nutrition information
    
    Returns:
        Product details if found, None otherwise
    
    Raises:
        LookupProviderError: If all providers fail
    """
    pass
```

## 13.7 Testing Standards

- Minimum 80% code coverage
- All new features require unit tests
- Integration tests for API endpoints
- Database tests for migrations
- Mock external services in tests

---

## Navigation

- **Previous:** [Security](12-security.md)
- **Next:** [Delivery Plan](14-delivery-plan.md)
- **Back to:** [README](README.md)
