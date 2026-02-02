#!/bin/bash
# Ralph Wiggum Common Functions
# With MCP Browser Tool Support

# Configuration
MAX_ITERATIONS=${MAX_ITERATIONS:-20}
RALPH_MODEL=${RALPH_MODEL:-"claude-sonnet-4-20250514"}
BROWSER_VALIDATION=${BROWSER_VALIDATION:-false}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Ensure we're in project directory
cd "$PROJECT_DIR" || exit 1

# Initialize Ralph state directory
init_ralph_state() {
    mkdir -p .ralph/screenshots
    
    # Create progress.md if missing
    if [[ ! -f .ralph/progress.md ]]; then
        cat > .ralph/progress.md << 'EOF'
# Progress Log

This file tracks what has been accomplished across iterations.

## Session History

<!-- Agent updates this after each work session -->

## Completed Criteria

<!-- Move criteria here when done -->

## Browser Validations

<!-- Screenshots and UI validation results -->

## Current Focus

<!-- What the agent is currently working on -->
EOF
    fi
    
    # Create guardrails.md if missing
    if [[ ! -f .ralph/guardrails.md ]]; then
        cat > .ralph/guardrails.md << 'EOF'
# Guardrails (Signs)

Lessons learned from previous iterations. Read this FIRST before starting work.

## Active Guardrails

<!-- Add lessons learned here -->

## Resolved Guardrails

<!-- Move fixed guardrails here -->
EOF
    fi
    
    # Create activity log
    touch .ralph/activity.log
    touch .ralph/errors.log
    
    # Initialize iteration counter
    echo "0" > .ralph/.iteration
    
    # Check for browser validation in task
    if [[ -f RALPH_TASK.md ]]; then
        if grep -q "browser_validation: true" RALPH_TASK.md 2>/dev/null; then
            BROWSER_VALIDATION=true
            echo -e "${CYAN}Browser validation enabled${NC}"
        fi
    fi
}

# Check if browser validation is needed
check_browser_validation() {
    if [[ -f RALPH_TASK.md ]]; then
        grep -q "browser_validation: true" RALPH_TASK.md 2>/dev/null
        return $?
    fi
    return 1
}

# Check if task is complete
check_task_complete() {
    if [[ ! -f RALPH_TASK.md ]]; then
        echo "false"
        return
    fi
    
    # Count unchecked boxes
    local unchecked=$(grep -c '\[ \]' RALPH_TASK.md 2>/dev/null || echo "0")
    
    if [[ "$unchecked" -eq 0 ]]; then
        echo "true"
    else
        echo "false"
    fi
}

# Get current iteration
get_iteration() {
    if [[ -f .ralph/.iteration ]]; then
        cat .ralph/.iteration
    else
        echo "0"
    fi
}

# Increment iteration
increment_iteration() {
    local current=$(get_iteration)
    echo $((current + 1)) > .ralph/.iteration
}

# Build the prompt for the agent
build_prompt() {
    local browser_section=""
    
    if check_browser_validation; then
        browser_section="
6. For UI criteria, use MCP browser tools:
   - browser_navigate to open pages
   - browser_lock before interactions
   - browser_snapshot before clicking/typing
   - browser_screenshot to capture evidence
   - browser_unlock when done
   - Save screenshots to .ralph/screenshots/criterion-N.png
"
    fi
    
    cat << EOF
Follow the Ralph Wiggum autonomous development protocol:

1. FIRST read these files in order:
   - RALPH_TASK.md (find unchecked [ ] criteria)
   - .ralph/guardrails.md (follow all active guardrails)
   - .ralph/progress.md (see what's done, avoid repeating)

2. Work on ONE unchecked criterion at a time

3. After completing each criterion:
   - Run the test_command from RALPH_TASK.md frontmatter
   - Commit: git add -A && git commit -m "ralph: [N] description"
   - Update RALPH_TASK.md: change [ ] to [x]
   - Update .ralph/progress.md with what was done

4. If something fails:
   - Add a guardrail to .ralph/guardrails.md
   - Try a different approach

5. When ALL criteria are [x], output: <ralph>COMPLETE</ralph>
$browser_section
Start now by reading RALPH_TASK.md.
EOF
}

# Log activity
log_activity() {
    local message="$1"
    local timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] $message" >> .ralph/activity.log
}

# Print status
print_status() {
    local iteration=$(get_iteration)
    local unchecked=$(grep -c '\[ \]' RALPH_TASK.md 2>/dev/null || echo "?")
    local checked=$(grep -c '\[x\]' RALPH_TASK.md 2>/dev/null || echo "0")
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🐛 Ralph Wiggum Status${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "   Iteration: ${YELLOW}$iteration${NC} / $MAX_ITERATIONS"
    echo -e "   Progress:  ${GREEN}$checked${NC} done, ${RED}$unchecked${NC} remaining"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}
