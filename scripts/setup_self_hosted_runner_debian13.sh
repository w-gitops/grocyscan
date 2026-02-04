#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-}"
RUNNER_TOKEN="${RUNNER_TOKEN:-}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)-runner}"
RUNNER_LABELS="${RUNNER_LABELS:-proxmox-ui}"
RUNNER_USER="${RUNNER_USER:-github-runner}"
RUNNER_DIR="${RUNNER_DIR:-/opt/actions-runner}"
RUNNER_AS_SERVICE="${RUNNER_AS_SERVICE:-true}"
ALLOW_PASSWORDLESS_SUDO="${ALLOW_PASSWORDLESS_SUDO:-true}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as root (sudo -i)."
  exit 1
fi

if [ -z "$REPO_URL" ] || [ -z "$RUNNER_TOKEN" ]; then
  echo "REPO_URL and RUNNER_TOKEN are required."
  echo "Example:"
  echo "  REPO_URL=https://github.com/w-gitops/grocyscan \\"
  echo "  RUNNER_TOKEN=YOUR_TOKEN \\"
  echo "  bash $0"
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl git jq sudo tar

apt-get install -y docker.io docker-compose-plugin
systemctl enable --now docker

if ! id "$RUNNER_USER" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$RUNNER_USER"
fi

usermod -aG docker "$RUNNER_USER"

if [ "$ALLOW_PASSWORDLESS_SUDO" = "true" ]; then
  echo "$RUNNER_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/$RUNNER_USER"
  chmod 0440 "/etc/sudoers.d/$RUNNER_USER"
fi

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

RUNNER_TAG="$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest | jq -r .tag_name)"
if [ -z "$RUNNER_TAG" ] || [ "$RUNNER_TAG" = "null" ]; then
  echo "Failed to determine latest runner release tag."
  exit 1
fi

RUNNER_VERSION="${RUNNER_TAG#v}"
curl -fsSL -o actions-runner.tar.gz \
  "https://github.com/actions/runner/releases/download/${RUNNER_TAG}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
tar xzf actions-runner.tar.gz
rm -f actions-runner.tar.gz

chown -R "$RUNNER_USER:$RUNNER_USER" "$RUNNER_DIR"

sudo -u "$RUNNER_USER" ./config.sh \
  --url "$REPO_URL" \
  --token "$RUNNER_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --unattended \
  --replace \
  --work "_work"

if [ "$RUNNER_AS_SERVICE" = "true" ]; then
  ./svc.sh install "$RUNNER_USER"
  ./svc.sh start
  echo "Runner installed and started as a service."
else
  echo "Runner configured. Start it manually with:"
  echo "  sudo -u $RUNNER_USER $RUNNER_DIR/run.sh"
fi

echo "Check GitHub -> Settings -> Actions -> Runners to confirm it is online."
