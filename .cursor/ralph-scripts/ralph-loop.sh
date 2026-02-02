#!/bin/bash
# Ralph Wiggum - Automated Loop
# Runs the agent repeatedly until task is complete or max iterations reached

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/ralph-common.sh"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        -m|--model)
            RALPH_MODEL="$2"
            shift 2
            ;;
        -y|--yes)
            AUTO_YES=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}"
echo "═══════════════════════════════════════════════════════════════════"
echo "🐛 Ralph Wiggum - Autonomous Loop"
echo "═══════════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Initialize state
init_ralph_state

# Check if task file exists
if [[ ! -f RALPH_TASK.md ]]; then
    echo -e "${RED}Error: RALPH_TASK.md not found${NC}"
    exit 1
fi

# Check if already complete
if [[ "$(check_task_complete)" == "true" ]]; then
    echo -e "${GREEN}✅ All criteria already complete!${NC}"
    exit 0
fi

# Print status
print_status

# Confirm
if [[ "$AUTO_YES" != "true" ]]; then
    echo ""
    echo -e "${YELLOW}This will run up to $MAX_ITERATIONS iterations autonomously.${NC}"
    read -p "Continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Build prompt
PROMPT=$(build_prompt)

echo ""
echo -e "${GREEN}Starting autonomous loop...${NC}"
echo -e "Model: ${BLUE}$RALPH_MODEL${NC}"
echo -e "Max iterations: ${BLUE}$MAX_ITERATIONS${NC}"
echo ""

# Main loop
while true; do
    current_iteration=$(get_iteration)
    
    # Check max iterations
    if [[ $current_iteration -ge $MAX_ITERATIONS ]]; then
        echo -e "${YELLOW}⚠️  Max iterations ($MAX_ITERATIONS) reached${NC}"
        print_status
        exit 1
    fi
    
    # Increment iteration
    increment_iteration
    current_iteration=$(get_iteration)
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🔄 Iteration $current_iteration / $MAX_ITERATIONS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    log_activity "🟢 Starting iteration $current_iteration"
    
    # Run the agent
    if ! agent -p "$PROMPT" --model "$RALPH_MODEL"; then
        echo -e "${RED}Agent exited with error${NC}"
        log_activity "🔴 Iteration $current_iteration failed"
        # Continue to next iteration
    fi
    
    # Check completion
    if [[ "$(check_task_complete)" == "true" ]]; then
        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ COMPLETE! All criteria done in $current_iteration iterations${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
        log_activity "🎉 COMPLETE - All criteria done in $current_iteration iterations"
        exit 0
    fi
    
    # Brief pause between iterations
    echo -e "${YELLOW}Rotating to fresh context...${NC}"
    sleep 2
done
