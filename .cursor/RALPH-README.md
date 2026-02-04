# Ralph Wiggum for Homebot

This project uses the [Ralph Wiggum autonomous development technique](https://ghuntley.com/ralph/) for building Homebot.

## Prerequisites

1. **cursor-agent CLI** - Install from Cursor
   ```bash
   curl https://cursor.com/install -fsS | bash
   ```

2. **gum** (optional, for interactive UI)
   ```bash
   brew install gum  # macOS
   # or let the installer prompt you
   ```

3. **Git repo** - Already set up

## Quick Start

### Option 1: Interactive Setup (Recommended)

```bash
./.cursor/ralph-scripts/ralph-setup.sh
```

This gives you a beautiful gum-based UI to:
- Select model (opus-4.5-thinking, sonnet, gpt-5.2, etc.)
- Set max iterations
- Choose options (branch, PR, parallel mode)

### Option 2: CLI Mode

```bash
# Basic run with defaults
./.cursor/ralph-scripts/ralph-loop.sh

# Custom iterations and model
./.cursor/ralph-scripts/ralph-loop.sh -n 50 -m gpt-5.2-high

# Skip confirmation
./.cursor/ralph-scripts/ralph-loop.sh -y

# Create branch and PR when done
./.cursor/ralph-scripts/ralph-loop.sh --branch feature/phase1 --pr -y
```

### Option 3: Parallel Execution

```bash
# Run 3 agents in parallel (tasks with <!-- group: N --> annotations)
./.cursor/ralph-scripts/ralph-loop.sh --parallel

# Run 5 agents in parallel
./.cursor/ralph-scripts/ralph-loop.sh --parallel --max-parallel 5

# Parallel with integration PR
./.cursor/ralph-scripts/ralph-loop.sh --parallel --max-parallel 5 --branch feature/phase1 --pr
```

### Option 4: Single Iteration (Testing)

```bash
# Run ONE iteration to test before going AFK
./.cursor/ralph-scripts/ralph-once.sh
```

## How It Works

1. **RALPH_TASK.md** defines the task with checkbox criteria
2. Ralph loops, running `cursor-agent` with fresh context each iteration
3. Progress persists in **files and git**, not LLM memory
4. At ~80k tokens, context rotates to fresh agent
5. Loop continues until all `[ ]` become `[x]`

## Task Groups (Parallel)

Use `<!-- group: N -->` to control execution order:

```markdown
- [ ] Create database schema <!-- group: 1 -->
- [ ] Create User model <!-- group: 1 -->
- [ ] Add auth endpoints <!-- group: 2 -->
- [ ] Update README  # no annotation = runs LAST
```

Groups run sequentially, tasks within groups run in parallel.

## Monitoring

```bash
# Watch activity in real-time
tail -f .ralph/activity.log

# Check for errors
cat .ralph/errors.log

# See progress
cat .ralph/progress.md
```

## State Files

| File | Purpose |
|------|---------|
| `RALPH_TASK.md` | Task definition with checkbox criteria |
| `.ralph/progress.md` | Session history (what's been accomplished) |
| `.ralph/guardrails.md` | Lessons learned (read FIRST before acting) |
| `.ralph/activity.log` | Tool call log with token counts |
| `.ralph/errors.log` | Failure log for debugging |

## Signals

The agent outputs signals that the loop detects:

| Signal | Meaning |
|--------|---------|
| `<ralph>COMPLETE</ralph>` | All criteria satisfied |
| `<ralph>GUTTER</ralph>` | Agent is stuck, needs help |

## Phase Workflow

Homebot is built in 7 phases. After each phase:

1. Ralph completes all criteria
2. Commit and push
3. Update `RALPH_TASK.md` with next phase (copy from `prd/80.XX-ralph-phase-N-*.md`)
4. Run Ralph again

## Tips

- **Don't fight the gutter**: If stuck 3x on same issue, the context is polluted. Start fresh.
- **Commit often**: The agent's commits ARE its memory across rotations.
- **Trust the files**: Progress is in `.ralph/` and git, not conversation history.
- **Use groups**: For parallel execution, annotate independent tasks.

## Learn More

- [Original technique](https://ghuntley.com/ralph/) - Geoffrey Huntley
- [Context engineering](https://ghuntley.com/gutter/) - The malloc/free metaphor
- [PRD Overview](prd/80.10-ralph-phases-overview.md) - Phase breakdown
