#!/usr/bin/env bash
# ============================================================
# GrocyScan — Preview Stack Dashboard
# ============================================================
# Shows status of all active preview/staging environments on the
# deploy runner. Run on the deploy LXC or via pct exec / SSH.
#
# Usage:
#   ./scripts/preview-status.sh             # Overview of all previews
#   ./scripts/preview-status.sh logs pr-42  # Logs for a specific preview
#   ./scripts/preview-status.sh inspect pr-42  # Detailed inspection
#   ./scripts/preview-status.sh health      # Health check all previews
#   ./scripts/preview-status.sh cleanup     # Remove stopped previews
#
# Also available via CI:
#   pct exec <DEPLOY_CTID> -- bash /root/preview-status.sh
#   ssh root@<DEPLOY_IP> preview-status.sh
# ============================================================

set -euo pipefail

# ---- Colors ----
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

# ---- Helpers ----
divider() { echo -e "\n${BOLD}── $1 ──${NC}"; }

# Get runner IP
RUNNER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")

# ============================================================
# List all active preview stacks
# ============================================================
cmd_list() {
  divider "Active Preview Environments"
  echo ""

  # Find all grocyscan- compose projects
  local projects
  projects=$(docker compose ls --format json 2>/dev/null \
    | jq -r '.[].Name' 2>/dev/null \
    | grep "^grocyscan-" \
    | sort) || true

  if [[ -z "$projects" ]]; then
    echo -e "  ${DIM}No active preview stacks found.${NC}"
    return
  fi

  printf "  ${BOLD}%-22s %-10s %-7s %-30s %s${NC}\n" "STACK" "STATUS" "PORT" "URL" "CONTAINERS"
  echo "  $(printf '%.0s─' {1..100})"

  while IFS= read -r project; do
    local preview_id="${project#grocyscan-}"
    local app_container="grocyscan-${preview_id}"

    # Get port from container
    local port
    port=$(docker port "${app_container}" 3334/tcp 2>/dev/null | head -1 | cut -d: -f2 || echo "?")

    # Health check
    local status_icon
    local http_status
    http_status=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:${port}/health" 2>/dev/null || echo "000")
    case "$http_status" in
      200) status_icon="${GREEN}healthy${NC}" ;;
      *)   status_icon="${RED}down(${http_status})${NC}" ;;
    esac

    # Count containers and their states
    local container_info
    container_info=$(docker compose -p "${project}" ps --format '{{.Name}}:{{.State}}' 2>/dev/null \
      | tr '\n' ' ') || container_info="?"

    # URL
    local url="http://${RUNNER_IP}:${port}"

    printf "  %-22s $(echo -e "${status_icon}")%-3s %-7s %-30s %s\n" \
      "${preview_id}" "" "${port}" "${url}" "${container_info}"

  done <<< "$projects"

  echo ""

  # Resource summary
  divider "Resource Usage"
  echo ""
  local container_count
  container_count=$(docker ps --filter "name=grocyscan-" --format '{{.Names}}' 2>/dev/null | wc -l)
  local image_size
  image_size=$(docker images --filter "reference=ghcr.io/*/grocyscan" --format '{{.Size}}' 2>/dev/null | head -1 || echo "?")

  echo "  Containers: ${container_count}"
  echo "  Image size: ${image_size}"
  echo "  Disk usage: $(docker system df --format '{{.Type}}\t{{.Size}}\t{{.Reclaimable}}' 2>/dev/null | head -3 | while read -r line; do echo "    ${line}"; done)"
  echo ""
}

# ============================================================
# Show logs for a specific preview
# ============================================================
cmd_logs() {
  local preview_id="${1:?Usage: preview-status.sh logs <preview-id> [lines]}"
  local lines="${2:-50}"
  local project="grocyscan-${preview_id}"

  divider "Logs: ${preview_id} (last ${lines} lines)"
  echo ""

  # Check if stack exists
  if ! docker compose -p "${project}" ps --quiet 2>/dev/null | head -1 >/dev/null; then
    echo -e "  ${RED}Stack '${project}' not found.${NC}"
    echo "  Run './preview-status.sh' to see active stacks."
    return 1
  fi

  # App logs
  echo -e "  ${BOLD}[app]${NC}"
  docker logs "grocyscan-${preview_id}" --tail "${lines}" 2>&1 | sed 's/^/    /'
  echo ""

  # Postgres logs (if present)
  local pg_container="grocyscan-${preview_id}-postgres"
  if docker ps --format '{{.Names}}' | grep -q "${pg_container}" 2>/dev/null; then
    echo -e "  ${BOLD}[postgres]${NC}"
    docker logs "${pg_container}" --tail 20 2>&1 | sed 's/^/    /'
    echo ""
  fi

  # Redis logs (if present)
  local redis_container="grocyscan-${preview_id}-redis"
  if docker ps --format '{{.Names}}' | grep -q "${redis_container}" 2>/dev/null; then
    echo -e "  ${BOLD}[redis]${NC}"
    docker logs "${redis_container}" --tail 10 2>&1 | sed 's/^/    /'
    echo ""
  fi
}

# ============================================================
# Detailed inspect of a preview stack
# ============================================================
cmd_inspect() {
  local preview_id="${1:?Usage: preview-status.sh inspect <preview-id>}"
  local project="grocyscan-${preview_id}"
  local app_container="grocyscan-${preview_id}"

  divider "Inspect: ${preview_id}"
  echo ""

  # Container status
  echo -e "  ${BOLD}Containers:${NC}"
  docker compose -p "${project}" ps 2>/dev/null | sed 's/^/    /'
  echo ""

  # Port mapping
  echo -e "  ${BOLD}Ports:${NC}"
  docker port "${app_container}" 2>/dev/null | sed 's/^/    /' || echo "    (no ports)"
  echo ""

  # Environment (sanitized — hide passwords)
  echo -e "  ${BOLD}Environment:${NC}"
  docker inspect "${app_container}" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null \
    | grep -v -iE "password|secret|token|key" \
    | sed 's/^/    /' || echo "    (container not found)"
  echo ""

  # Health endpoint response
  local port
  port=$(docker port "${app_container}" 3334/tcp 2>/dev/null | head -1 | cut -d: -f2 || echo "")
  if [[ -n "$port" ]]; then
    echo -e "  ${BOLD}Health (/health):${NC}"
    curl -sf "http://localhost:${port}/health" 2>/dev/null | jq '.' 2>/dev/null | sed 's/^/    /' \
      || echo "    (not responding)"
    echo ""
  fi

  # Resource usage
  echo -e "  ${BOLD}Resources:${NC}"
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
    $(docker compose -p "${project}" ps --format '{{.Names}}' 2>/dev/null | tr '\n' ' ') 2>/dev/null \
    | sed 's/^/    /' || echo "    (stats not available)"
  echo ""

  # Recent logs (last 20 lines)
  echo -e "  ${BOLD}Recent app logs:${NC}"
  docker logs "${app_container}" --tail 20 2>&1 | sed 's/^/    /'
  echo ""
}

# ============================================================
# Health check all previews
# ============================================================
cmd_health() {
  divider "Health Check — All Previews"
  echo ""

  local projects
  projects=$(docker compose ls --format json 2>/dev/null \
    | jq -r '.[].Name' 2>/dev/null \
    | grep "^grocyscan-" \
    | sort) || true

  if [[ -z "$projects" ]]; then
    echo -e "  ${DIM}No active preview stacks.${NC}"
    return
  fi

  while IFS= read -r project; do
    local preview_id="${project#grocyscan-}"
    local app_container="grocyscan-${preview_id}"
    local port
    port=$(docker port "${app_container}" 3334/tcp 2>/dev/null | head -1 | cut -d: -f2 || echo "")

    if [[ -z "$port" ]]; then
      echo -e "  ${RED}✗${NC} ${preview_id} — no port mapping"
      continue
    fi

    local response
    response=$(curl -sf "http://localhost:${port}/health" 2>/dev/null) || response=""
    if [[ -n "$response" ]]; then
      echo -e "  ${GREEN}✓${NC} ${preview_id} — port ${port} — ${response}"
    else
      echo -e "  ${RED}✗${NC} ${preview_id} — port ${port} — not responding"
      # Show last few log lines for unhealthy stacks
      echo -e "    ${DIM}Last 5 app log lines:${NC}"
      docker logs "${app_container}" --tail 5 2>&1 | sed 's/^/      /'
    fi
  done <<< "$projects"
  echo ""
}

# ============================================================
# Collect debug bundle (for CI — outputs structured text)
# ============================================================
cmd_debug_bundle() {
  local preview_id="${1:?Usage: preview-status.sh debug-bundle <preview-id>}"
  local project="grocyscan-${preview_id}"
  local app_container="grocyscan-${preview_id}"

  # This output is designed to be captured by CI and posted to PR comments
  echo "### Preview Debug: ${preview_id}"
  echo ""

  # Container status
  echo "**Container Status:**"
  echo '```'
  docker compose -p "${project}" ps 2>/dev/null || echo "(stack not found)"
  echo '```'
  echo ""

  # App logs (last 40 lines)
  echo "**App Logs (last 40 lines):**"
  echo '```'
  docker logs "${app_container}" --tail 40 2>&1 || echo "(no logs)"
  echo '```'
  echo ""

  # Postgres logs (last 15 lines)
  local pg_container="grocyscan-${preview_id}-postgres"
  if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "${pg_container}"; then
    echo "**Postgres Logs (last 15 lines):**"
    echo '```'
    docker logs "${pg_container}" --tail 15 2>&1 || echo "(no logs)"
    echo '```'
    echo ""
  fi

  # Migration output (if app ran alembic)
  echo "**Alembic Migration Check:**"
  echo '```'
  docker exec "${app_container}" python -m alembic current 2>&1 || echo "(could not check)"
  echo '```'
  echo ""

  # Environment (sanitized)
  echo "**Environment (sanitized):**"
  echo '```'
  docker inspect "${app_container}" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null \
    | grep -v -iE "password|secret|token|key|hash" \
    || echo "(not available)"
  echo '```'
}

# ============================================================
# Cleanup stopped/orphaned previews
# ============================================================
cmd_cleanup() {
  divider "Cleanup — Stopped Previews"
  echo ""

  local removed=0
  local projects
  projects=$(docker compose ls -a --format json 2>/dev/null \
    | jq -r '.[] | select(.Status | test("exited|dead|created")) | .Name' 2>/dev/null \
    | grep "^grocyscan-" \
    | sort) || true

  if [[ -z "$projects" ]]; then
    echo -e "  ${GREEN}No stopped previews to clean up.${NC}"
    echo ""
    return
  fi

  while IFS= read -r project; do
    local preview_id="${project#grocyscan-}"
    echo -e "  Removing ${YELLOW}${preview_id}${NC}..."
    docker compose -p "${project}" down --remove-orphans --volumes 2>/dev/null || true
    removed=$((removed + 1))
  done <<< "$projects"

  echo ""
  echo "  Removed ${removed} stopped stack(s)."
  docker system prune -f --filter "until=2h" 2>/dev/null | tail -1 | sed 's/^/  /'
  echo ""
}

# ============================================================
# Main
# ============================================================
COMMAND="${1:-list}"
shift || true

case "$COMMAND" in
  list|ls|"")     cmd_list ;;
  logs|log)       cmd_logs "$@" ;;
  inspect|info)   cmd_inspect "$@" ;;
  health|check)   cmd_health ;;
  debug-bundle)   cmd_debug_bundle "$@" ;;
  cleanup|prune)  cmd_cleanup ;;
  help|-h|--help)
    echo "Usage: $(basename "$0") [command] [args]"
    echo ""
    echo "Commands:"
    echo "  list                    Overview of all active previews (default)"
    echo "  logs <id> [lines]       Show logs for a preview (e.g. 'logs pr-42 100')"
    echo "  inspect <id>            Detailed inspection (containers, env, health, resources)"
    echo "  health                  Health check all previews"
    echo "  debug-bundle <id>       Collect debug info (markdown, for CI/PR comments)"
    echo "  cleanup                 Remove stopped/orphaned preview stacks"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0")                  # Show all previews"
    echo "  $(basename "$0") logs pr-42       # App + DB + Redis logs"
    echo "  $(basename "$0") inspect pr-42    # Full inspection"
    echo "  $(basename "$0") health           # Check all"
    echo "  $(basename "$0") debug-bundle pr-42 > debug.md  # For CI"
    ;;
  *)
    echo "Unknown command: $COMMAND (run with 'help')"
    exit 1
    ;;
esac
