#!/usr/bin/env bash
# ============================================================
# GrocyScan — Proxmox Self-Hosted Runner Bootstrap
# ============================================================
# This script sets up an Ubuntu 24.04 server (VM or LXC on Proxmox)
# as a GitHub Actions self-hosted runner with Docker support.
#
# Prerequisites:
#   - Fresh Ubuntu 24.04 installation (VM or LXC with nesting enabled)
#   - Root or sudo access
#   - Internet connectivity
#
# Usage:
#   1. Create an Ubuntu 24.04 VM/LXC on Proxmox
#   2. SSH into it: ssh root@<IP>
#   3. Copy this script and run:
#      bash setup-runner.sh \
#        --github-url https://github.com/w-gitops/grocyscan \
#        --runner-token <TOKEN> \
#        --runner-name grocyscan-runner
#
# To get the runner token:
#   GitHub → Repository → Settings → Actions → Runners → New self-hosted runner
#   Or use: gh api -X POST repos/w-gitops/grocyscan/actions/runners/registration-token
# ============================================================

set -euo pipefail

# ---- Configuration Defaults ----
GITHUB_URL=""
RUNNER_TOKEN=""
RUNNER_NAME="grocyscan-runner"
RUNNER_LABELS="self-hosted,linux,x64,proxmox,preview"
RUNNER_USER="runner"
RUNNER_DIR="/opt/actions-runner"
RUNNER_VERSION="2.321.0"  # Update as needed: https://github.com/actions/runner/releases

# ---- Parse Arguments ----
while [[ $# -gt 0 ]]; do
  case $1 in
    --github-url)   GITHUB_URL="$2"; shift 2 ;;
    --runner-token) RUNNER_TOKEN="$2"; shift 2 ;;
    --runner-name)  RUNNER_NAME="$2"; shift 2 ;;
    --runner-labels) RUNNER_LABELS="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 --github-url <URL> --runner-token <TOKEN> [--runner-name <NAME>] [--runner-labels <LABELS>]"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$GITHUB_URL" || -z "$RUNNER_TOKEN" ]]; then
  echo "ERROR: --github-url and --runner-token are required"
  echo "Run with --help for usage information"
  exit 1
fi

echo "============================================"
echo "  GrocyScan Runner Setup"
echo "============================================"
echo "  GitHub URL:    $GITHUB_URL"
echo "  Runner Name:   $RUNNER_NAME"
echo "  Runner Labels: $RUNNER_LABELS"
echo "============================================"

# ---- 1. System Updates ----
echo ""
echo ">>> [1/7] Updating system packages..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq

# ---- 2. Install Docker ----
echo ""
echo ">>> [2/7] Installing Docker..."
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
else
  echo "  Docker already installed: $(docker --version)"
fi

# Install Docker Compose plugin if not present
if ! docker compose version &>/dev/null; then
  apt-get install -y -qq docker-compose-plugin
fi

echo "  Docker: $(docker --version)"
echo "  Compose: $(docker compose version)"

# ---- 3. Install Additional Tools ----
echo ""
echo ">>> [3/7] Installing tools (curl, jq, git, gh)..."
apt-get install -y -qq curl jq git unzip

# Install GitHub CLI
if ! command -v gh &>/dev/null; then
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  apt-get update -qq
  apt-get install -y -qq gh
fi

echo "  gh: $(gh --version | head -1)"

# ---- 4. Create Runner User ----
echo ""
echo ">>> [4/7] Creating runner user..."
if ! id "$RUNNER_USER" &>/dev/null; then
  useradd -m -s /bin/bash "$RUNNER_USER"
  usermod -aG docker "$RUNNER_USER"
  echo "  Created user: $RUNNER_USER (docker group)"
else
  usermod -aG docker "$RUNNER_USER"
  echo "  User $RUNNER_USER already exists, added to docker group"
fi

# ---- 5. Install GitHub Actions Runner ----
echo ""
echo ">>> [5/7] Installing GitHub Actions Runner v${RUNNER_VERSION}..."
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

# ---- 6. Configure Runner ----
echo ""
echo ">>> [6/7] Configuring runner..."
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

# ---- 7. Install as System Service ----
echo ""
echo ">>> [7/7] Installing runner as systemd service..."
cd "$RUNNER_DIR"
./svc.sh install "$RUNNER_USER"
./svc.sh start

echo ""
echo "============================================"
echo "  Runner Setup Complete!"
echo "============================================"
echo ""
echo "  Runner Name:   $RUNNER_NAME"
echo "  Runner Labels: $RUNNER_LABELS"
echo "  Service:       actions.runner.*.service"
echo ""
echo "  Check status:  systemctl status actions.runner.*.service"
echo "  View logs:     journalctl -u actions.runner.*.service -f"
echo ""
echo "  The runner should now appear in:"
echo "  $GITHUB_URL/settings/actions/runners"
echo ""
echo "  Next steps:"
echo "  1. Verify runner appears as 'Online' in GitHub"
echo "  2. Login to GHCR: echo \$PAT | docker login ghcr.io -u <user> --password-stdin"
echo "  3. Push a PR to test preview deployments"
echo "============================================"
