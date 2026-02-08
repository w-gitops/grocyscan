#!/usr/bin/env bash
# ============================================================
# GrocyScan — Self-Hosted Runner Bootstrap (Debian 13 Trixie)
# ============================================================
# Sets up a Debian 13 LXC (or VM) as a GitHub Actions self-hosted
# runner. Designed for Proxmox LXCs with nesting enabled.
#
# Two modes:
#   Interactive:  bash setup-runner.sh          (prompts for values)
#   CLI flags:    bash setup-runner.sh --github-url ... --runner-token ...
#
# Profiles:
#   ci      — Python 3, Node 20, Playwright system deps, pip/npm.
#   deploy  — Docker + Docker Compose only. LXC needs nesting+keyctl.
#   all     — Everything (ci + deploy). Default.
#
# Runner token:
#   gh api -X POST repos/w-gitops/grocyscan/actions/runners/registration-token --jq .token
# ============================================================

set -euo pipefail

# ---- Colors ----
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
DIM='\033[2m'
NC='\033[0m'

# ---- Defaults ----
GITHUB_URL=""
RUNNER_TOKEN=""
RUNNER_NAME=""
RUNNER_LABELS=""
RUNNER_PROFILE=""
RUNNER_USER="runner"
RUNNER_DIR="/opt/actions-runner"
RUNNER_VERSION="2.321.0"
NODE_MAJOR="20"
INTERACTIVE=false

# ---- Parse Arguments ----
if [[ $# -eq 0 ]]; then
  INTERACTIVE=true
fi

while [[ $# -gt 0 ]]; do
  case $1 in
    --github-url)    GITHUB_URL="$2"; shift 2 ;;
    --runner-token)  RUNNER_TOKEN="$2"; shift 2 ;;
    --runner-name)   RUNNER_NAME="$2"; shift 2 ;;
    --runner-labels) RUNNER_LABELS="$2"; shift 2 ;;
    --profile)       RUNNER_PROFILE="$2"; shift 2 ;;
    --runner-user)   RUNNER_USER="$2"; shift 2 ;;
    -i|--interactive) INTERACTIVE=true; shift ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Run with no arguments for interactive mode, or pass flags:"
      echo ""
      echo "Options:"
      echo "  --github-url    URL     GitHub repository URL"
      echo "  --runner-token  TOKEN   Runner registration token"
      echo "  --runner-name   NAME    Runner name"
      echo "  --runner-labels LABELS  Comma-separated labels (auto-set from profile)"
      echo "  --profile       PROF    ci | deploy | all (default: all)"
      echo "  --runner-user   USER    System user for runner (default: runner)"
      echo "  -i, --interactive       Force interactive prompts"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ---- Interactive prompts ----
prompt() {
  local var_name="$1"
  local prompt_text="$2"
  local default="$3"
  local current_val="${!var_name}"

  if [[ -n "$current_val" ]]; then
    return
  fi

  if [[ -n "$default" ]]; then
    read -rp "$(echo -e "${CYAN}${prompt_text}${NC} ${DIM}[${default}]${NC}: ")" input
    eval "${var_name}=\"${input:-$default}\""
  else
    read -rp "$(echo -e "${CYAN}${prompt_text}${NC}: ")" input
    eval "${var_name}=\"${input}\""
  fi
}

prompt_secret() {
  local var_name="$1"
  local prompt_text="$2"
  local current_val="${!var_name}"

  if [[ -n "$current_val" ]]; then
    return
  fi

  read -srp "$(echo -e "${CYAN}${prompt_text}${NC}: ")" input
  echo ""
  eval "${var_name}=\"${input}\""
}

if [[ "$INTERACTIVE" == true ]] || [[ -z "$GITHUB_URL" ]] || [[ -z "$RUNNER_TOKEN" ]]; then
  echo ""
  echo -e "${BOLD}============================================${NC}"
  echo -e "${BOLD}  GrocyScan — Runner Setup${NC}"
  echo -e "${BOLD}============================================${NC}"
  echo -e "  OS: $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || echo "Debian")"
  echo -e "${BOLD}============================================${NC}"
  echo ""

  # ---- Profile selection ----
  if [[ -z "$RUNNER_PROFILE" ]]; then
    echo -e "${BOLD}Select runner profile:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} ci      — Python + Node + Playwright (for tests)"
    echo -e "  ${GREEN}2)${NC} deploy  — Docker + Compose (for preview/staging deploys)"
    echo -e "  ${GREEN}3)${NC} all     — Everything (combined runner)"
    echo ""
    read -rp "$(echo -e "${CYAN}Profile [1/2/3]${NC} ${DIM}[3]${NC}: ")" profile_choice
    case "${profile_choice:-3}" in
      1|ci)     RUNNER_PROFILE="ci" ;;
      2|deploy) RUNNER_PROFILE="deploy" ;;
      3|all)    RUNNER_PROFILE="all" ;;
      *) echo "Invalid choice, using 'all'"; RUNNER_PROFILE="all" ;;
    esac
  fi
  echo ""

  # ---- Default runner name from profile ----
  DEFAULT_NAME=""
  case "$RUNNER_PROFILE" in
    ci)     DEFAULT_NAME="grocyscan-ci" ;;
    deploy) DEFAULT_NAME="grocyscan-deploy" ;;
    all)    DEFAULT_NAME="grocyscan-runner" ;;
  esac

  # ---- GitHub connection ----
  echo -e "${BOLD}GitHub configuration:${NC}"
  echo ""
  prompt       GITHUB_URL   "  Repository URL" "https://github.com/w-gitops/grocyscan"
  prompt_secret RUNNER_TOKEN "  Runner registration token (from GitHub Settings > Actions > Runners)"

  if [[ -z "$RUNNER_TOKEN" ]]; then
    echo ""
    echo -e "${YELLOW}  No token provided. You can get one with:${NC}"
    echo "  gh api -X POST repos/w-gitops/grocyscan/actions/runners/registration-token --jq .token"
    echo ""
    prompt_secret RUNNER_TOKEN "  Runner registration token"
  fi
  echo ""

  # ---- Runner identity ----
  echo -e "${BOLD}Runner settings:${NC}"
  echo ""
  prompt RUNNER_NAME "  Runner name" "$DEFAULT_NAME"
  prompt RUNNER_USER "  System user" "runner"
  echo ""

  # ---- Labels (optional override) ----
  echo -e "${BOLD}Labels:${NC} ${DIM}(press Enter for auto-assigned from profile)${NC}"
  echo ""
  prompt RUNNER_LABELS "  Custom labels (comma-separated)" ""
  echo ""
fi

# ---- Fill remaining defaults ----
if [[ -z "$RUNNER_PROFILE" ]]; then
  RUNNER_PROFILE="all"
fi

if [[ -z "$RUNNER_NAME" ]]; then
  case "$RUNNER_PROFILE" in
    ci)     RUNNER_NAME="grocyscan-ci" ;;
    deploy) RUNNER_NAME="grocyscan-deploy" ;;
    all)    RUNNER_NAME="grocyscan-runner" ;;
  esac
fi

# Auto-set labels from profile if not provided
if [[ -z "$RUNNER_LABELS" ]]; then
  case "$RUNNER_PROFILE" in
    ci)     RUNNER_LABELS="self-hosted,linux,x64,proxmox-ci" ;;
    deploy) RUNNER_LABELS="self-hosted,linux,x64,proxmox,preview" ;;
    all)    RUNNER_LABELS="self-hosted,linux,x64,proxmox-ci,proxmox,preview" ;;
  esac
fi

# ---- Final validation ----
if [[ -z "$GITHUB_URL" ]]; then
  echo "ERROR: GitHub URL is required (--github-url or interactive)"
  exit 1
fi
if [[ -z "$RUNNER_TOKEN" ]]; then
  echo "ERROR: Runner token is required (--runner-token or interactive)"
  exit 1
fi

# ---- Confirmation ----
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  GrocyScan Runner Setup${NC}"
echo -e "${BOLD}============================================${NC}"
echo -e "  Profile:       ${GREEN}${RUNNER_PROFILE}${NC}"
echo -e "  GitHub URL:    ${GITHUB_URL}"
echo -e "  Runner Name:   ${RUNNER_NAME}"
echo -e "  Runner Labels: ${RUNNER_LABELS}"
echo -e "  Runner User:   ${RUNNER_USER}"
echo -e "  OS:            $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || echo "Debian")"
echo -e "${BOLD}============================================${NC}"

if [[ "$INTERACTIVE" == true ]]; then
  echo ""
  read -rp "$(echo -e "${YELLOW}Proceed with installation? [Y/n]${NC}: ")" confirm
  if [[ "${confirm,,}" == "n" ]]; then
    echo "Aborted."
    exit 0
  fi
fi

STEP=0
step() { STEP=$((STEP + 1)); echo -e "\n>>> [${STEP}] $1"; }

# ============================================================
# 1. System updates + base tools
# ============================================================
step "Updating system packages..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

step "Installing base tools..."
apt-get install -y -qq \
  curl wget jq git unzip gnupg lsb-release ca-certificates \
  build-essential libffi-dev libssl-dev

# ---- GitHub CLI ----
if ! command -v gh &>/dev/null; then
  step "Installing GitHub CLI..."
  mkdir -p /etc/apt/keyrings
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    -o /etc/apt/keyrings/githubcli-archive-keyring.gpg
  chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list
  apt-get update -qq && apt-get install -y -qq gh
fi
echo "  gh: $(gh --version | head -1)"

# ============================================================
# 2. Docker (deploy + all profiles)
# ============================================================
if [[ "$RUNNER_PROFILE" == "deploy" || "$RUNNER_PROFILE" == "all" ]]; then
  step "Installing Docker..."

  if [[ -f /proc/1/status ]] && grep -q "NSpid:" /proc/1/status 2>/dev/null; then
    echo "  Running in container — ensure nesting=1 and keyctl=1 in Proxmox LXC config"
  fi

  if ! command -v docker &>/dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
    if ! curl -sf "https://download.docker.com/linux/debian/dists/${CODENAME}/Release" >/dev/null 2>&1; then
      echo "  Docker repo for ${CODENAME} not available, using bookworm"
      CODENAME="bookworm"
    fi

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian ${CODENAME} stable" \
      > /etc/apt/sources.list.d/docker.list

    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
  fi

  echo "  Docker:  $(docker --version)"
  echo "  Compose: $(docker compose version)"

  if docker run --rm hello-world >/dev/null 2>&1; then
    echo "  Docker test: OK"
  else
    echo "  WARNING: 'docker run hello-world' failed."
    echo "  If running in an LXC, verify nesting=1 and keyctl=1 in Proxmox."
    echo "  On the Proxmox host: pct set <CTID> --features nesting=1,keyctl=1"
  fi
fi

# ============================================================
# 3. Python (ci + all profiles)
# ============================================================
if [[ "$RUNNER_PROFILE" == "ci" || "$RUNNER_PROFILE" == "all" ]]; then
  step "Installing Python 3..."

  apt-get install -y -qq \
    python3 python3-venv python3-dev python3-pip python3-full

  PYTHON_INSTALL_DIR=$(python3 -c "import sysconfig; print(sysconfig.get_path('stdlib'))")
  EXTERN_MARKER="${PYTHON_INSTALL_DIR}/EXTERNALLY-MANAGED"
  if [[ -f "$EXTERN_MARKER" ]]; then
    echo "  Removing EXTERNALLY-MANAGED marker for CI use"
    rm -f "$EXTERN_MARKER"
  fi

  python3 -m pip install --quiet --upgrade pip setuptools wheel 2>/dev/null || true
  echo "  Python: $(python3 --version)"
  echo "  pip:    $(pip3 --version 2>/dev/null | head -1 || echo 'via python3 -m pip')"

  # ---- Node.js ----
  step "Installing Node.js ${NODE_MAJOR}..."
  if ! node --version 2>/dev/null | grep -q "v${NODE_MAJOR}"; then
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
      | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
      > /etc/apt/sources.list.d/nodesource.list
    apt-get update -qq
    apt-get install -y -qq nodejs
  fi
  echo "  Node: $(node --version)"
  echo "  npm:  $(npm --version)"

  # ---- Playwright system dependencies ----
  step "Installing Playwright browser dependencies..."
  apt-get install -y -qq \
    libnss3 libnspr4 libatk1.0-0t64 libatk-bridge2.0-0t64 \
    libcups2t64 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2t64 libatspi2.0-0t64 libxshmfence1 \
    fonts-liberation fonts-noto-color-emoji \
    xvfb \
    2>/dev/null || {
      apt-get install -y -qq \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
        libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
        libcairo2 libasound2 libatspi2.0-0 libxshmfence1 \
        fonts-liberation fonts-noto-color-emoji \
        xvfb \
        2>/dev/null || echo "  WARNING: Some Playwright deps may need manual install"
    }
  echo "  Chromium system deps installed"
fi

# ============================================================
# 4. Runner user
# ============================================================
step "Creating runner user..."
if ! id "$RUNNER_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$RUNNER_USER"
  echo "  Created user: $RUNNER_USER"
else
  echo "  User $RUNNER_USER already exists"
fi

if command -v docker &>/dev/null; then
  usermod -aG docker "$RUNNER_USER"
  echo "  Added $RUNNER_USER to docker group"
fi

# ============================================================
# 5. GitHub Actions Runner
# ============================================================
step "Installing GitHub Actions Runner v${RUNNER_VERSION}..."
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

ARCH=$(uname -m)
case $ARCH in
  x86_64)  RUNNER_ARCH="x64" ;;
  aarch64) RUNNER_ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

RUNNER_TAR="actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz"
if [[ ! -f "$RUNNER_TAR" ]]; then
  curl -sL -o "$RUNNER_TAR" \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_TAR}"
fi
tar xzf "$RUNNER_TAR"

apt-get install -y -qq libicu-dev 2>/dev/null || true

chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"

step "Configuring runner..."
su - "$RUNNER_USER" -c "
  cd $RUNNER_DIR && \
  ./config.sh \
    --url '$GITHUB_URL' \
    --token '$RUNNER_TOKEN' \
    --name '$RUNNER_NAME' \
    --labels '$RUNNER_LABELS' \
    --work '_work' \
    --unattended \
    --replace
"

step "Starting runner service..."
cd "$RUNNER_DIR"
./svc.sh install "$RUNNER_USER"
./svc.sh start

# ============================================================
# Done
# ============================================================
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${GREEN}  Runner Setup Complete!${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""
echo "  Profile:       $RUNNER_PROFILE"
echo "  Runner Name:   $RUNNER_NAME"
echo "  Runner Labels: $RUNNER_LABELS"
echo "  OS:            $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || echo "Debian")"
echo ""
case "$RUNNER_PROFILE" in
  ci)
    echo "  Installed:"
    echo "    Python $(python3 --version 2>&1 | awk '{print $2}')"
    echo "    Node   $(node --version 2>/dev/null || echo 'N/A')"
    echo "    Playwright system deps (Chromium)"
    echo ""
    echo "  NOT installed: Docker (use --profile deploy or all)"
    ;;
  deploy)
    echo "  Installed:"
    echo "    Docker  $(docker --version 2>&1 | awk '{print $3}' | tr -d ',')"
    echo "    Compose $(docker compose version 2>&1 | awk '{print $NF}')"
    echo ""
    echo "  NOT installed: Python/Node (use --profile ci or all)"
    ;;
  all)
    echo "  Installed:"
    echo "    Python  $(python3 --version 2>&1 | awk '{print $2}')"
    echo "    Node    $(node --version 2>/dev/null || echo 'N/A')"
    echo "    Docker  $(docker --version 2>&1 | awk '{print $3}' | tr -d ',')"
    echo "    Compose $(docker compose version 2>&1 | awk '{print $NF}')"
    echo "    Playwright system deps (Chromium)"
    ;;
esac
echo ""
echo "  Service:  systemctl status actions.runner.*.service"
echo "  Logs:     journalctl -u actions.runner.*.service -f"
echo ""
echo "  Verify:   $GITHUB_URL/settings/actions/runners"
echo ""
if [[ "$RUNNER_PROFILE" == "deploy" || "$RUNNER_PROFILE" == "all" ]]; then
  echo "  Next: Login to GHCR as the runner user:"
  echo "    su - $RUNNER_USER"
  echo "    echo \$PAT | docker login ghcr.io -u <username> --password-stdin"
  echo ""
fi
echo "============================================"
