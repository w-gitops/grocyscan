#!/usr/bin/env bash
# ============================================================
# GrocyScan — Self-Hosted Runner Bootstrap (Debian 13 Trixie)
# ============================================================
# Sets up a Debian 13 LXC (or VM) as a GitHub Actions self-hosted
# runner. Designed for Proxmox LXCs with nesting enabled.
#
# Profiles:
#   ci      — Python 3, Node 20, Playwright system deps, pip/npm.
#              For running pytest + Playwright E2E tests.
#   deploy  — Docker + Docker Compose only.
#              For preview deploys and staging. LXC needs nesting+keyctl.
#   all     — Everything (ci + deploy). Default.
#
# Usage (inside the LXC):
#   bash setup-runner.sh \
#     --github-url https://github.com/w-gitops/grocyscan \
#     --runner-token <TOKEN> \
#     --runner-name grocyscan-ci \
#     --profile ci
#
# Runner token:
#   gh api -X POST repos/w-gitops/grocyscan/actions/runners/registration-token --jq .token
# ============================================================

set -euo pipefail

# ---- Defaults ----
GITHUB_URL=""
RUNNER_TOKEN=""
RUNNER_NAME="grocyscan-runner"
RUNNER_LABELS=""
RUNNER_PROFILE="all"
RUNNER_USER="runner"
RUNNER_DIR="/opt/actions-runner"
RUNNER_VERSION="2.321.0"
NODE_MAJOR="20"

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

echo "============================================"
echo "  GrocyScan Runner Setup (Debian)"
echo "============================================"
echo "  Profile:       $RUNNER_PROFILE"
echo "  GitHub URL:    $GITHUB_URL"
echo "  Runner Name:   $RUNNER_NAME"
echo "  Runner Labels: $RUNNER_LABELS"
echo "  OS:            $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || echo "Debian")"
echo "============================================"

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

  # Check LXC nesting (warn if not enabled)
  if [[ -f /proc/1/status ]] && grep -q "NSpid:" /proc/1/status 2>/dev/null; then
    echo "  Running in container — ensure nesting=1 and keyctl=1 in Proxmox LXC config"
  fi

  if ! command -v docker &>/dev/null; then
    # Docker official install for Debian
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
    # Debian 13 (Trixie) may not have Docker repo yet; fall back to bookworm
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

  # Quick Docker sanity check
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

  # Debian 13 ships Python 3.12+ natively
  apt-get install -y -qq \
    python3 python3-venv python3-dev python3-pip python3-full

  # Debian 13 enforces PEP 668 (externally-managed). The runner user
  # will use --break-system-packages or venvs. For CI simplicity we
  # allow global pip installs.
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
  # Chromium's runtime shared library requirements on Debian
  apt-get install -y -qq \
    libnss3 libnspr4 libatk1.0-0t64 libatk-bridge2.0-0t64 \
    libcups2t64 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2t64 libatspi2.0-0t64 libxshmfence1 \
    fonts-liberation fonts-noto-color-emoji \
    xvfb \
    2>/dev/null || {
      # Fallback: Debian 12 package names (without t64 suffix)
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

# Docker group
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

# The runner has its own bundled dotnet and node — install any missing
# native deps it needs (ICU for .NET globalization)
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
echo "============================================"
echo "  Runner Setup Complete!"
echo "============================================"
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
