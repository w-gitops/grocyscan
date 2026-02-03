# Ralph Wiggum in GrocyScan

Ralph Wiggum methodology is **installed** from the **cursor-command** repo and wired into this project so you can use it when you want.

## What’s Installed

| Item | Location | Purpose |
|------|----------|---------|
| **Cursor rule** | `.cursor/rules/ralph-wiggum.mdc` | Main protocol (startup, work loop, browser tools, signals). Applied by default (`alwaysApply: true`). |
| **Optional rule** | `.cursor/rules/ralph-optional.mdc` | Explains when/how to use Ralph; `alwaysApply: false`. Enable manually if you prefer Ralph only for some chats. |
| **Skill** | `.cursor/skills/ralph-wiggum/` | Full methodology: `SKILL.md` plus `references/` (task format, state files, browser tools, PRD template). |
| **State** | `.ralph/` | `progress.md`, `guardrails.md`, `screenshots/` (and optional logs). |
| **Task file** | `RALPH_TASK.md` (root) | Define your task and success criteria here. |

## Using Ralph

### Default (always on)

The rule `.cursor/rules/ralph-wiggum.mdc` is set to `alwaysApply: true`, so the agent already follows the Ralph protocol (read RALPH_TASK.md, guardrails, progress, one criterion at a time, commit with `ralph: [N]`, etc.).

To run a Ralph session:

1. Edit `RALPH_TASK.md` with your task and unchecked criteria.
2. Start an Agent chat.
3. Say: **"Follow the Ralph Wiggum protocol. Work on RALPH_TASK.md"** (or similar).

The agent will read guardrails and progress, then work through criteria.

### Optional (use only when you want)

If you prefer Ralph only for certain chats:

1. In `.cursor/rules/ralph-wiggum.mdc`, set **`alwaysApply: false`**.
2. When you want a Ralph session, enable the **"Ralph Wiggum"** rule in Cursor (e.g. rule picker / rules for this workspace).
3. Or open `RALPH_TASK.md` / `.ralph/` so the optional rule (and its globs) can apply.

The optional rule (`.cursor/rules/ralph-optional.mdc`) documents this and points to the skill.

## Updating from cursor-command

Source repo: `C:\git\cursor-command`.

- **Rule**: Copy `cursor-command/rules/ralph-wiggum.mdc` into `.cursor/rules/`. Merge any GrocyScan-specific edits (e.g. cursor-browser-extension) back in.
- **Skill**: Copy `cursor-command/skills/ralph-wiggum/` (SKILL.md and `references/`) into `.cursor/skills/ralph-wiggum/`.

## Re-bootstrap (fresh install)

From WSL or Git Bash, from the grocyscan repo root:

```bash
bash /c/git/cursor-command/scripts/init-ralph.sh .
```

This recreates `.ralph/` state, rule, and a sample `RALPH_TASK.md` if missing. It may overwrite `.cursor/rules/ralph-wiggum.mdc` with the upstream version; re-apply GrocyScan-specific browser-extension details if needed.
