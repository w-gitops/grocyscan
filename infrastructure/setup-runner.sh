#!/usr/bin/env bash
# ============================================================
# GrocyScan — Proxmox Self-Hosted Runner Bootstrap
# ============================================================
# Sets up an Ubuntu 24.04 server (VM or LXC on Proxmox) as a
# GitHub Actions self-hosted runner.
#
# Profiles:
#   ci      — Python 3.12, Node 20, Playwright browsers, pip/npm.
#              For running pytest + Playwright E2E tests.
#   deploy  — Docker + Docker Compose only.
#              For preview deploys and staging.
#   all     — Everything (ci + deploy). Default.
#
# Usage:
#   bash setup-runner.sh \
#     --github-url https://github.com/w-gitops/grocyscan \
#     --runner-token <TOKEN> \
#     --runner-name grocyscan-ci \
#     --profile ci
#
# Multiple runners:
#   You can run this script multiple times on different VMs with
#   different profiles and names:
#     VM 1: --profile ci     --runner-name grocyscan-ci
#     VM 2: --profile deploy --runner-name grocyscan-deploy
#   Or use one VM with --profile all for both.
#
# Runner token:
#   GitHub → Repo → Settings → Actions → Runners → New self-hosted runner
#   Or: gh api -X POST repos/OWNER/REPO/actions/runners/registration-token
# ============================================================

set -euo pipefail

# ---- Defaults ----
GITHUB_URL=""
RUNNER_TOKEN=""
RUNNER_NAME="grocyscan-runner"
RUNNER_LABELS=""          # Auto-set from profile if empty
RUNNER_PROFILE="all"      # ci | deploy | all
RUNNER_USER="runner"
RUNNER_DIR="/opt/actions-runner"
RUNNER_VERSION="2.321.0"
NODE_VERSION="20"
PYTHON_VERSION="3.12"

# ---- Parse Arguments ----
while [[ $# -gt 0 ]]; do
  case $1 in
    --github-url)    GITHUB_URL="$2"; shift 2 ;;
    --runner-token)  RUNNER_TOKEN="$2"; shift 2 ;;
    --runner-name)   RUNNER_NAME="$2"; shift 2 ;;
    --runner-labels) RUNNER_LABELS="$2"; shift 2 ;;
    --profile)       RUNNER_PROFILE="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 --github-url <URL> --runner-token <TOKEN> [options]"
      echo ""
      echo "Options:"
      echo "  --runner-name   NAME     Runner name (default: grocyscan-runner)"
      echo "  --runner-labels LABELS   Comma-separated labels (auto-set from profile)"
      echo "  --profile       PROFILE  ci | deploy | all (default: all)"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$GITHUB_URL" || -z "$RUNNER_TOKEN" ]]; then
  echo "ERROR: --github-url and --runner-token are required"
  exit 1
fi

# Auto-set labels from profile
if [[ -z "$RUNNER_LABELS" ]]; then
  case "$RUNNER_PROFILE" in
    ci)     RUNNER_LABELS="self-hosted,linux,x64,proxmox-ci" ;;
    deploy) RUNNER_LABELS="self-hosted,linux,x64,proxmox,preview" ;;
    all)    RUNNER_LABELS="self-hosted,linux,x64,proxmox-ci,proxmox,preview" ;;
    *) echo "Unknown profile: $RUNNER_PROFILE (use ci, deploy, or all)"; exit 1 ;;
  esac
fi

STEP_TOTAL=0
case "$RUNNER_PROFILE" in
  ci)     STEP_TOTAL=9 ;;
  deploy) STEP_TOTAL=7 ;;
  all)    STEP_TOTAL=10 ;;
esac

echo "============================================"
echo "  GrocyScan Runner Setup"
echo "============================================"
echo "  Profile:       $RUNNER_PROFILE"
echo "  GitHub URL:    $GITHUB_URL"
echo "  Runner Name:   $RUNNER_NAME"
echo "  Runner Labels: $RUNNER_LABELS"
echo "============================================"

STEP=0
step() { STEP=$((STEP + 1)); echo -e "\n>>> [${STEP}/${STEP_TOTAL}] $1"; }

# ============================================================
# Common: System updates + base tools
# ============================================================
step "Updating system packages..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

step "Installing base tools (curl, jq, git, gh)..."
apt-get install -y -qq curl jq git unzip software-properties-common

# GitHub CLI
if ! command -v gh &>/dev/null; then
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg 2>/dev/null
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  apt-get update -qq && apt-get install -y -qq gh
fi

# ============================================================
# Profile: deploy (Docker)
# ============================================================
if [[ "$RUNNER_PROFILE" == "deploy" || "$RUNNER_PROFILE" == "all" ]]; then
  step "Installing Docker..."
  if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
  else
    echo "  Docker already installed: $(docker --version)"
  fi
  if ! docker compose version &>/dev/null; then
    apt-get install -y -qq docker-compose-plugin
  fi
  echo "  Docker:  $(docker --version)"
  echo "  Compose: $(docker compose version)"
fi

# ============================================================
# Profile: ci (Python + Node + Playwright)
# ============================================================
if [[ "$RUNNER_PROFILE" == "ci" || "$RUNNER_PROFILE" == "all" ]]; then

  # ---- Python ----
  step "Installing Python ${PYTHON_VERSION}..."
  if ! python${PYTHON_VERSION} --version &>/dev/null 2>&1; then
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update -qq
    apt-get install -y -qq \
      python${PYTHON_VERSION} \
      python${PYTHON_VERSION}-venv \
      python${PYTHON_VERSION}-dev \
      python3-pip
  fi
  # Make this version the default python3
  update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1 2>/dev/null || true
  # Install pip for this version
  python${PYTHON_VERSION} -m ensurepip --upgrade 2>/dev/null || apt-get install -y -qq python3-pip
  python3 -m pip install --quiet --upgrade pip setuptools wheel
  echo "  Python: $(python3 --version)"

  # ---- Node.js ----
  step "Installing Node.js ${NODE_VERSION}..."
  if ! node --version 2>/dev/null | grep -q "v${NODE_VERSION}"; then
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt-get install -y -qq nodejs
  fi
  echo "  Node: $(node --version)"
  echo "  npm:  $(npm --version)"

  # ---- Playwright system deps ----
  step "Installing Playwright system dependencies..."
  # These are the libraries Playwright's Chromium needs
  apt-get install -y -qq \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2t64 libatspi2.0-0 libxshmfence1 \
    fonts-liberation fonts-noto-color-emoji xvfb \
    2>/dev/null || {
      # Fallback for older Ubuntu where package names differ
      apt-get install -y -qq \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
        libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
        libcairo2 libasound2 libatspi2.0-0 libxshmfence1 \
        fonts-liberation fonts-noto-color-emoji xvfb \
        2>/dev/null || echo "  Some Playwright deps may need manual install"
    }
  echo "  System deps installed for headless Chromium"

  # ---- Pre-install project Python deps (warm cache) ----
  step "Pre-installing Python dependencies (pip cache warmup)..."
  # Download the requirements files from the repo if this is a fresh setup
  # The runner will install them properly during workflow runs, but this
  # warms the pip cache so subsequent installs are fast
  if [[ -f /tmp/grocyscan-requirements.txt ]]; then
    python3 -m pip install --quiet -r /tmp/grocyscan-requirements.txt 2>/dev/null || true
  fi
  echo "  Pip cache warmed (deps will be installed per-workflow)"

fi

# ============================================================
# Common: Runner user
# ============================================================
step "Creating runner user..."
if ! id "$RUNNER_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$RUNNER_USER"
  echo "  Created user: $RUNNER_USER"
else
  echo "  User $RUNNER_USER already exists"
fi

# Add to docker group if Docker is installed
if command -v docker &>/dev/null; then
  usermod -aG docker "$RUNNER_USER"
  echo "  Added to docker group"
fi

# ============================================================
# Common: GitHub Actions Runner
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
chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"

step "Configuring and starting runner..."
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

cd "$RUNNER_DIR"
./svc.sh install "$RUNNER_USER"
./svc.sh start

# ============================================================
# Done
# ============================================================
echo ""
echo "============================================"
echo "  Runner Setup Complete!"
echo "============================================"
echo ""
echo "  Profile:       $RUNNER_PROFILE"
echo "  Runner Name:   $RUNNER_NAME"
echo "  Runner Labels: $RUNNER_LABELS"
echo ""
case "$RUNNER_PROFILE" in
  ci)
    echo "  Installed: Python $(python3 --version 2>&1 | awk '{print $2}'), Node $(node --version), Playwright deps"
    echo "  NOT installed: Docker (use --profile all or deploy for Docker)"
    ;;
  deploy)
    echo "  Installed: Docker $(docker --version 2>&1 | awk '{print $3}' | tr -d ',')"
    echo "  NOT installed: Python/Node (use --profile all or ci for tests)"
    ;;
  all)
    echo "  Installed: Python $(python3 --version 2>&1 | awk '{print $2}'), Node $(node --version), Docker $(docker --version 2>&1 | awk '{print $3}' | tr -d ',')"
    ;;
esac
echo ""
echo "  Service:       systemctl status actions.runner.*.service"
echo "  Logs:          journalctl -u actions.runner.*.service -f"
echo ""
echo "  Verify at: $GITHUB_URL/settings/actions/runners"
echo ""
if [[ "$RUNNER_PROFILE" == "deploy" || "$RUNNER_PROFILE" == "all" ]]; then
  echo "  Next: docker login ghcr.io -u <user> --password-stdin <<< \$PAT"
fi
echo "============================================"
