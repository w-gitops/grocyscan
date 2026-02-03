# MCP Browser Tools Integration

This document describes how to use MCP (Model Context Protocol) browser tools for UI validation in the Ralph Wiggum methodology.

## Overview

MCP browser tools allow the agent to:
- Navigate to web pages
- Interact with UI elements (click, type, scroll)
- Capture screenshots as evidence
- Validate UI state after implementation

## Default MCP Server

**Use `cursor-browser-extension` for all browser automation.**

Call tools via `CallMcpTool` with `server: "cursor-browser-extension"`.

## Available Tools

### Core Browser Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `browser_navigate` | Navigate to URL | Open pages for testing (returns snapshot) |
| `browser_snapshot` | Get page structure | Get element refs before interacting |
| `browser_click` | Click an element | Buttons, links, checkboxes (use ref) |
| `browser_type` | Type text (append) | Text inputs |
| `browser_fill_form` | Fill form fields | Form inputs (clears first) |
| `browser_take_screenshot` | Capture screenshot | Evidence collection |
| `browser_hover` | Hover over element | Tooltips, dropdowns |
| `browser_press_key` | Press keyboard key | Enter, Tab, Escape, etc. |
| `browser_tabs` | List/manage browser tabs | Check existing tabs, get current URL |

### Key Rules

- ALWAYS call `browser_snapshot` before clicking/typing to get element refs
- Use element refs from snapshot (e.g., `@e3`) for interactions
- No lock/unlock needed with `cursor-browser-extension`
- Save screenshots to `.ralph/screenshots/criterion-N.png`

## Standard Workflow

1. **Navigate** – `browser_navigate` (returns snapshot)
2. **Get refs** – `browser_snapshot` if page changed
3. **Interact** – `browser_click`, `browser_fill_form`, `browser_type` using refs
4. **Wait** – Short waits (2–3s) with snapshot checks
5. **Evidence** – `browser_take_screenshot`, reference in progress.md

## Waiting Strategy

Use short incremental waits with snapshot checks; avoid single long waits.

## Integration with RALPH_TASK.md

Enable browser validation in task frontmatter:

```yaml
---
task: Build login page
test_command: "pytest tests/"
browser_validation: true
base_url: "http://localhost:8000"
---
```

## Troubleshooting

- **No server found** – Check Cursor Settings → Features → MCP for `cursor-browser-extension`
- **Element not found** – Call `browser_snapshot` for fresh refs; refs change when page updates
- **Blank screenshot** – Wait for load (short waits + snapshot), then capture
