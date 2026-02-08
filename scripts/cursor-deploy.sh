#!/usr/bin/env bash
# ============================================================
# GrocyScan — Cursor Agent Deploy Helper
# ============================================================
# Smart deployment script for Cursor agents (Desktop and Cloud).
#
# Behavior:
#   - Detects environment (local network vs cloud)
#   - For local: deploys directly via SSH (fast, iterative)
#   - For cloud: triggers GitHub Actions workflow (CI/CD path)
#   - Can also check preview deployment status
#
# Usage:
#   ./scripts/cursor-deploy.sh [command] [options]
#
# Commands:
#   deploy    Deploy current branch (default)
#   status    Check deployment status
#   preview   Show preview URL for current PR
#   logs      Show recent application logs
#   health    Run health check
#   trigger   Trigger GitHub Actions deploy workflow
#
# Examples:
#   ./scripts/cursor-deploy.sh deploy          # Auto-detect and deploy
#   ./scripts/cursor-deploy.sh status          # Check CI/workflow status
#   ./scripts/cursor-deploy.sh preview         # Get preview URL
#   ./scripts/cursor-deploy.sh logs            # Show app logs
#   ./scripts/cursor-deploy.sh trigger         # Trigger workflow manually
# ============================================================

set -euo pipefail

# ---- Configuration ----
PROD_HOST="${DEPLOY_HOST:-192.168.200.37}"
PROD_USER="${DEPLOY_USER:-root}"
PROD_PATH="/opt/grocyscan"
PROD_SERVICE="grocyscan"

# ---- Color Helpers ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ---- Environment Detection ----
detect_environment() {
  # Check if we can reach the production server
  if timeout 3 bash -c "echo >/dev/tcp/${PROD_HOST}/22" 2>/dev/null; then
    echo "local"
  else
    echo "cloud"
  fi
}

# Get current branch
get_branch() {
  git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

# Get current PR number (if any)
get_pr_number() {
  if command -v gh &>/dev/null; then
    gh pr view --json number --jq '.number' 2>/dev/null || echo ""
  else
    echo ""
  fi
}

# ---- Commands ----

cmd_deploy() {
  local env
  env=$(detect_environment)
  local branch
  branch=$(get_branch)

  info "Branch: ${branch}"
  info "Environment: ${env}"

  if [[ "$env" == "local" ]]; then
    deploy_direct
  else
    deploy_via_ci
  fi
}

deploy_direct() {
  info "Deploying directly via SSH to ${PROD_HOST}..."

  # Check SSH connectivity
  if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "${PROD_USER}@${PROD_HOST}" "echo ok" &>/dev/null; then
    err "Cannot SSH to ${PROD_USER}@${PROD_HOST}"
    warn "Falling back to CI deployment..."
    deploy_via_ci
    return
  fi

  # Build frontend if needed
  if [[ -f frontend/package.json ]]; then
    info "Building Vue frontend..."
    (cd frontend && NODE_ENV=production npm run build) || { err "Frontend build failed"; exit 1; }
  fi

  # Sync code
  info "Syncing code..."
  rsync -avz --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '.env' \
    --exclude 'tests' \
    --exclude '.cursor' \
    --exclude '.ralph' \
    --exclude 'prd' \
    --exclude 'docker' \
    --exclude 'infrastructure' \
    --exclude 'docs' \
    --exclude 'frontend/node_modules' \
    --exclude 'frontend/src' \
    --exclude 'frontend/tests' \
    ./ "${PROD_USER}@${PROD_HOST}:${PROD_PATH}/"

  # Sync frontend dist
  if [[ -d frontend/dist ]]; then
    info "Syncing frontend dist..."
    ssh "${PROD_USER}@${PROD_HOST}" "mkdir -p ${PROD_PATH}/frontend"
    rsync -avz frontend/dist/ "${PROD_USER}@${PROD_HOST}:${PROD_PATH}/frontend/dist/"
  fi

  # Install deps, migrate, restart
  info "Installing dependencies and restarting..."
  ssh "${PROD_USER}@${PROD_HOST}" << REMOTE
    set -e
    cd ${PROD_PATH}
    ./venv/bin/pip install -q -r requirements.txt 2>&1 | tail -5
    ./venv/bin/alembic upgrade head 2>&1 | tail -5
    systemctl restart ${PROD_SERVICE}
    sleep 3
REMOTE

  # Health check
  cmd_health
  ok "Deploy complete!"
}

deploy_via_ci() {
  info "Deploying via GitHub Actions CI..."

  if ! command -v gh &>/dev/null; then
    err "GitHub CLI (gh) not available. Cannot trigger CI deployment."
    err "Push your changes and create a PR — CI will deploy automatically."
    exit 1
  fi

  # Push current branch
  local branch
  branch=$(get_branch)
  info "Pushing branch ${branch}..."
  git push -u origin "${branch}" 2>&1 || { err "Push failed"; exit 1; }

  # Check if there's a PR
  local pr_num
  pr_num=$(get_pr_number)

  if [[ -z "$pr_num" ]]; then
    warn "No PR found for branch ${branch}."
    info "Create a PR to trigger preview deployment:"
    info "  gh pr create --title 'Deploy ${branch}' --body 'Preview deployment'"
    return
  fi

  info "PR #${pr_num} found. Preview deployment should trigger automatically."
  info "Check status: gh run list --branch ${branch}"

  # Wait a moment and show status
  sleep 3
  gh run list --branch "${branch}" --limit 5 2>/dev/null || true
}

cmd_status() {
  local branch
  branch=$(get_branch)

  if ! command -v gh &>/dev/null; then
    err "GitHub CLI (gh) not available."
    exit 1
  fi

  info "Workflow status for branch: ${branch}"
  echo ""
  gh run list --branch "${branch}" --limit 10 2>/dev/null || {
    warn "Could not fetch workflow runs"
  }

  echo ""
  local pr_num
  pr_num=$(get_pr_number)
  if [[ -n "$pr_num" ]]; then
    info "PR #${pr_num} checks:"
    gh pr checks 2>/dev/null || true
  fi
}

cmd_preview() {
  local pr_num
  pr_num=$(get_pr_number)

  if [[ -z "$pr_num" ]]; then
    warn "No PR found for current branch."
    info "Create a PR to get a preview deployment."
    return
  fi

  info "PR #${pr_num} — Preview Info:"

  # Calculate expected port
  local port=$((10000 + pr_num))
  info "Expected preview port: ${port}"

  # Try to find preview URL from PR comments
  if command -v gh &>/dev/null; then
    gh pr view "${pr_num}" --json comments --jq '.comments[] | select(.body | contains("Preview Deployment")) | .body' 2>/dev/null | head -20 || {
      warn "No preview comment found yet. Deployment may still be in progress."
      info "Check status: ./scripts/cursor-deploy.sh status"
    }
  fi
}

cmd_logs() {
  local env
  env=$(detect_environment)

  if [[ "$env" == "local" ]]; then
    info "Fetching logs from ${PROD_HOST}..."
    ssh "${PROD_USER}@${PROD_HOST}" "journalctl -u ${PROD_SERVICE} -n 50 --no-pager" 2>/dev/null || {
      err "Could not fetch logs"
    }
  else
    warn "Not on local network. Use GitHub Actions logs instead:"
    info "  gh run view --log"
    info "  gh run list --branch $(get_branch)"
  fi
}

cmd_health() {
  local env
  env=$(detect_environment)

  if [[ "$env" == "local" ]]; then
    info "Health check on ${PROD_HOST}..."
    local result
    result=$(ssh "${PROD_USER}@${PROD_HOST}" "curl -sf http://localhost:3334/health 2>/dev/null || curl -sf http://localhost:3334/api/health 2>/dev/null" 2>/dev/null || echo "FAILED")
    if [[ "$result" == "FAILED" ]]; then
      err "Health check failed!"
      ssh "${PROD_USER}@${PROD_HOST}" "systemctl status ${PROD_SERVICE} --no-pager | head -15" 2>/dev/null || true
      return 1
    else
      ok "Health: ${result}"
    fi
  else
    local pr_num
    pr_num=$(get_pr_number)
    if [[ -n "$pr_num" ]]; then
      info "Check preview health via the preview URL in the PR comments."
      info "  ./scripts/cursor-deploy.sh preview"
    else
      warn "Not on local network and no PR found."
    fi
  fi
}

cmd_trigger() {
  if ! command -v gh &>/dev/null; then
    err "GitHub CLI (gh) not available."
    exit 1
  fi

  local branch
  branch=$(get_branch)

  if [[ "$branch" == "main" ]]; then
    info "Triggering production deployment..."
    gh workflow run deploy-production.yml
    ok "Production deploy workflow triggered."
  else
    local pr_num
    pr_num=$(get_pr_number)
    if [[ -n "$pr_num" ]]; then
      info "Triggering preview deployment for PR #${pr_num}..."
      gh workflow run preview-deploy.yml -f "pr_number=${pr_num}"
      ok "Preview deploy workflow triggered."
    else
      warn "No PR found. Create one first or push to trigger CI."
    fi
  fi

  sleep 2
  gh run list --limit 3
}

# ---- Main ----
COMMAND="${1:-deploy}"

case "$COMMAND" in
  deploy)  cmd_deploy ;;
  status)  cmd_status ;;
  preview) cmd_preview ;;
  logs)    cmd_logs ;;
  health)  cmd_health ;;
  trigger) cmd_trigger ;;
  help|-h|--help)
    head -35 "$0" | tail -30
    ;;
  *)
    err "Unknown command: ${COMMAND}"
    echo "Available: deploy, status, preview, logs, health, trigger, help"
    exit 1
    ;;
esac
