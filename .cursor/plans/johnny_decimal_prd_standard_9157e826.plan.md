---
name: Johnny Decimal PRD Standard
overview: Create a Johnny Decimal numbering standard document and remap all PRD files to use correct JD numbering (content IDs start at .10, not .01).
todos:
  - id: create-jd-standard
    content: Create prd/00.00-johnny-decimal-standard.md with Johnny Decimal rules and project area definitions
    status: completed
  - id: rename-10-series
    content: Rename 10.01/10.02/10.03 to 10.10/10.11/10.12
    status: completed
  - id: rename-20-series
    content: Rename 20.01/20.02 to 20.10/20.11
    status: completed
  - id: rename-30-series
    content: Rename 30.01/30.02/30.03/30.04 to 30.10/30.11/30.12/30.13
    status: completed
  - id: rename-40-series
    content: Rename 40.01/40.02/40.03/40.04/40.06 to 40.10/40.11/40.12/40.13/40.14
    status: completed
  - id: rename-50-series
    content: Rename 50.01/50.02/50.03 to 50.10/50.11/50.12
    status: completed
  - id: rename-60-series
    content: Rename 60.02/60.06 to 60.10/60.11
    status: completed
  - id: rename-91-series
    content: Rename 91.01-91.05 to 91.10-91.14
    status: completed
  - id: update-references
    content: Update any cross-references in PRD files and plan documents
    status: in_progress
isProject: false
---

# Johnny Decimal PRD Numbering Standard

## Summary

Create a standards document explaining Johnny Decimal conventions for this project, then rename all PRD files to use correct numbering where content IDs start at `.10` (reserving `.00-.09` for system management).

## Key Johnny Decimal Rules

- **Areas**: `X0-X9` (e.g., `10-19`, `20-29`)
- **Categories**: First digit of area + any digit (e.g., `10`, `11`, `21`)
- **IDs**: Two digits after decimal, content starts at `.10`
- **Reserved IDs** (`.00-.09`): System management purposes


| Reserved ID | Purpose                 |
| ----------- | ----------------------- |
| `.00`       | Index/JDex for category |
| `.01`       | Inbox                   |
| `.02`       | Task/project management |
| `.03`       | Templates               |
| `.04`       | Links                   |
| `.05-.07`   | Reserved for expansion  |
| `.08`       | Someday                 |
| `.09`       | Archive                 |


## File Changes

### 1. Create Standards Document

Create `prd/00.00-johnny-decimal-standard.md` containing:

- Johnny Decimal structure explanation
- Area definitions for this project
- Reserved ID meanings
- Naming conventions

### 2. PRD File Renaming


| Current File                        | New File                            |
| ----------------------------------- | ----------------------------------- |
| `10.01-standards-of-development.md` | `10.10-standards-of-development.md` |
| `10.02-executive-summary.md`        | `10.11-executive-summary.md`        |
| `10.03-delivery-plan.md`            | `10.12-delivery-plan.md`            |
| `20.01-user-stories.md`             | `20.10-user-stories.md`             |
| `20.02-functional-requirements.md`  | `20.11-functional-requirements.md`  |
| `30.01-technical-architecture.md`   | `30.10-technical-architecture.md`   |
| `30.02-data-models.md`              | `30.11-data-models.md`              |
| `30.03-api-specification.md`        | `30.12-api-specification.md`        |
| `30.04-ui-specification.md`         | `30.13-ui-specification.md`         |
| `40.01-installation-operations.md`  | `40.10-installation-operations.md`  |
| `40.02-observability.md`            | `40.11-observability.md`            |
| `40.03-security.md`                 | `40.12-security.md`                 |
| `40.04-schema-evolution.md`         | `40.13-schema-evolution.md`         |
| `40.06-environment-variables.md`    | `40.14-environment-variables.md`    |
| `50.01-testing-strategy.md`         | `50.10-testing-strategy.md`         |
| `50.02-project-standards.md`        | `50.11-project-standards.md`        |
| `50.03-troubleshooting.md`          | `50.12-troubleshooting.md`          |
| `60.02-qr-routing-system.md`        | `60.10-qr-routing-system.md`        |
| `60.06-multi-tenant.md`             | `60.11-multi-tenant.md`             |
| `91.01-api-documentation.md`        | `91.10-api-documentation.md`        |
| `91.02-mcp-server.md`               | `91.11-mcp-server.md`               |
| `91.03-user-documentation.md`       | `91.12-user-documentation.md`       |
| `91.04-n8n-integration.md`          | `91.13-n8n-integration.md`          |
| `91.05-decision-log.md`             | `91.14-decision-log.md`             |


### 3. Area Definitions for Project


| Area    | Purpose                                        |
| ------- | ---------------------------------------------- |
| `00-09` | System management, standards, indexes          |
| `10-19` | Foundation - standards, vision, planning       |
| `20-29` | Requirements - user stories, functional specs  |
| `30-39` | Technical Design - architecture, data, API, UI |
| `40-49` | Operations - install, observability, security  |
| `50-59` | Quality - testing, standards, troubleshooting  |
| `60-69` | Features - individual feature PRDs             |
| `70-79` | (Reserved for future expansion)                |
| `80-89` | Ralph Phases - execution task documents        |
| `90-99` | Appendices - reference documentation           |


## Implementation Steps

1. Create `prd/00.00-johnny-decimal-standard.md` with full documentation
2. Use `git mv` to rename each file (preserves git history)
3. Update any cross-references within PRD files
4. Update the plan document references

