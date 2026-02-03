---
name: ralph-wiggum-methodology
description: >
  Autonomous development methodology using iterative task completion with file-based state management.
  Use when building software from PRDs, implementing features with clear success criteria, or when
  the user mentions Ralph Wiggum, autonomous development, iterative tasks, or structured development workflow.
  Supports MCP browser tools for UI validation.
license: MIT
metadata:
  author: cursor-command
  version: "1.0.0"
compatibility: Requires Cursor IDE with Agent mode. Optional: MCP browser tools for UI validation.
---

# Ralph Wiggum Development Methodology

An autonomous development approach where state lives in **files and git**, not in conversation context. Each session starts fresh, reads state from files, and persists progress through commits.

## Core Principle

> "That's the beauty of Ralph - the technique is deterministically bad in an undeterministic world."

The same prompt is fed repeatedly to an AI agent. Progress persists in files and git, not in the LLM's context window. When context fills up, you get a fresh agent with fresh context.

## When to Use This Skill

- Building software from a PRD with defined success criteria
- Implementing features that can be broken into discrete tasks
- Projects requiring autonomous, iterative development
- When you need browser-based UI validation
- Long-running development sessions that may exceed context limits

## Quick Start

1. Create `RALPH_TASK.md` with success criteria as checkboxes
2. Initialize `.ralph/` state directory
3. Follow the startup sequence each session
4. Work through criteria one at a time
5. Commit after each completed criterion

## Startup Sequence

Execute these steps at the start of EVERY session:

1. **Read RALPH_TASK.md** - Find unchecked `[ ]` criteria
2. **Read .ralph/guardrails.md** - Follow all active guardrails (lessons learned)
3. **Read .ralph/progress.md** - See what's done, avoid repeating work
4. **Check git log** - Understand current state from recent commits
5. **Check MCP browser availability** - If task has `browser_validation: true`

## Work Loop

For each unchecked criterion:

```
1. Focus on ONE criterion at a time
2. Implement the solution
3. Run test_command from RALPH_TASK.md frontmatter
4. If UI criterion: validate with MCP browser tools
5. Commit: git add -A && git commit -m "ralph: [criterion] - description"
6. Update RALPH_TASK.md: change [ ] to [x]
7. Update .ralph/progress.md with what was accomplished
8. Repeat until all criteria complete
```

## Failure Protocol

When something fails:

1. **Don't repeat the same approach** - That's "the gutter"
2. **Add a guardrail** to `.ralph/guardrails.md`:
   ```markdown
   ### Sign: [Short description]
   - **Trigger**: When this situation occurs
   - **Instruction**: What to do instead
   - **Evidence**: Screenshot or log reference
   - **Added after**: Iteration N - reason
   ```
3. **Capture evidence** - Screenshot for browser failures, logs for code failures
4. **Try a different approach** - Or move on to the next criterion

## Signals

Output these sigils when appropriate:

| Signal | Meaning |
|--------|---------|
| `<ralph>COMPLETE</ralph>` | All criteria are `[x]`, task is finished |
| `<ralph>BLOCKED</ralph>` | Cannot proceed without human input |
| `<ralph>GUTTER</ralph>` | Stuck repeating failures, need fresh approach |
| `<ralph>BROWSER_NEEDED</ralph>` | UI validation required but browser unavailable |

## MCP Browser Tools Protocol

For tasks with `browser_validation: true`, this project uses **cursor-browser-extension**. See `.cursor/skills/ralph-wiggum/references/browser-tools.md` for details.

### Workflow
```
1. browser_tabs (list)     - Check existing tabs
2. browser_navigate        - Open target URL
3. browser_snapshot       - Get page structure before interacting
4. [interactions]         - click, type, fill, scroll as needed
5. browser_take_screenshot - Capture evidence
```

### Key Rules
- ALWAYS call `browser_snapshot` before clicking/typing to get element refs
- Use element refs from snapshot (e.g., `@e3`) for interactions
- Save screenshots to `.ralph/screenshots/criterion-N.png`
- No lock/unlock needed with cursor-browser-extension

## Git Protocol

- Commit after EACH completed criterion
- Use prefix: `ralph: ` for all commits
- Include criterion number in message: `ralph: [1] Initialize project structure`
- Push periodically to preserve progress

## Context Management

- Don't read entire large files - use search to find relevant sections
- Prefer small, focused changes over large rewrites
- If context feels polluted (many failed attempts), suggest starting fresh
- State in files means fresh context can resume seamlessly

## Reference Files

For detailed specifications, see:
- [Task Format](./references/task-format.md) - RALPH_TASK.md specification
- [State Files](./references/state-files.md) - .ralph/ directory guide
- [Browser Tools](./references/browser-tools.md) - MCP browser integration
- [PRD Template](./references/prd-template.md) - Standards section for PRDs
