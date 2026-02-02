#!/bin/bash
# Ralph Wiggum - Single Iteration Test
# Run one iteration to test your task definition

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/ralph-common.sh"

echo -e "${GREEN}🐛 Ralph Wiggum - Single Iteration Test${NC}"
echo ""

# Initialize state
init_ralph_state

# Check if task file exists
if [[ ! -f RALPH_TASK.md ]]; then
    echo -e "${RED}Error: RALPH_TASK.md not found${NC}"
    echo "Create a task file first. See the documentation."
    exit 1
fi

# Check if already complete
if [[ "$(check_task_complete)" == "true" ]]; then
    echo -e "${GREEN}✅ All criteria already complete!${NC}"
    exit 0
fi

# Print status
print_status

# Increment iteration
increment_iteration
log_activity "🟢 Starting iteration $(get_iteration)"

# Build prompt
PROMPT=$(build_prompt)

echo ""
echo -e "${YELLOW}Starting agent...${NC}"
echo ""

# Run the agent
agent -p "$PROMPT" --model "$RALPH_MODEL"

# Check completion
if [[ "$(check_task_complete)" == "true" ]]; then
    echo ""
    echo -e "${GREEN}✅ All criteria complete!${NC}"
    log_activity "🎉 COMPLETE - All criteria done"
else
    echo ""
    print_status
    echo -e "${YELLOW}Run again to continue:${NC} ./ralph-once.sh"
fi
