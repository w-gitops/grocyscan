#!/usr/bin/env bash
# ============================================================
# GrocyScan — Full CI/CD Bootstrap (run on Proxmox host)
# ============================================================
# Single script that sets up the entire CI/CD infrastructure:
#
#   1. Installs gh CLI on the Proxmox host (if missing)
#   2. Authenticates with GitHub and generates runner tokens
#   3. Creates two Debian 13 LXCs (CI + Deploy)
#   4. Installs GitHub Actions runner inside each via pct exec
#   5. Logs the deploy runner into GHCR
#   6. Prints summary with all URLs and next steps
#
# Usage:
#   curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/bootstrap.sh
#   bash bootstrap.sh
#
# Everything is interactive — just answer the prompts.
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

info()  { echo -e "${CYAN}>>>${NC} $*"; }
ok()    { echo -e "${GREEN}>>>${NC} $*"; }
warn()  { echo -e "${YELLOW}>>>${NC} $*"; }
err()   { echo -e "${RED}>>>${NC} $*"; }

prompt() {
  local var_name="$1" prompt_text="$2" default="${3:-}"
  local current="${!var_name}"
  [[ -n "$current" ]] && return
  if [[ -n "$default" ]]; then
    read -rp "$(echo -e "  ${CYAN}${prompt_text}${NC} ${DIM}[${default}]${NC}: ")" input
    eval "${var_name}=\"${input:-$default}\""
  else
    read -rp "$(echo -e "  ${CYAN}${prompt_text}${NC}: ")" input
    eval "${var_name}=\"${input}\""
  fi
}

prompt_secret() {
  local var_name="$1" prompt_text="$2"
  local current="${!var_name}"
  [[ -n "$current" ]] && return
  read -srp "$(echo -e "  ${CYAN}${prompt_text}${NC}: ")" input
  echo ""
  eval "${var_name}=\"${input}\""
}

divider() {
  echo ""
  echo -e "${BOLD}────────────────────────────────────────────${NC}"
  echo -e "${BOLD}  $1${NC}"
  echo -e "${BOLD}────────────────────────────────────────────${NC}"
  echo ""
}

# ---- Validate ----
if ! command -v pct &>/dev/null; then
  err "pct not found — this script must run on a Proxmox VE host."
  exit 1
fi

# ============================================================
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  GrocyScan — CI/CD Bootstrap${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""
echo "  This will set up two Debian LXCs on this Proxmox host"
echo "  as GitHub Actions self-hosted runners:"
echo ""
echo -e "    ${GREEN}1.${NC} CI runner      — pytest + Playwright (bare install)"
echo -e "    ${GREEN}2.${NC} Deploy runner  — Docker previews + staging"
echo ""
echo "  Everything runs from this terminal. No SSH keys or"
echo "  Ansible needed — uses pct exec to configure LXCs."
echo ""
echo -e "${BOLD}============================================${NC}"
echo ""
read -rp "$(echo -e "${YELLOW}Ready to start? [Y/n]${NC}: ")" go
[[ "${go,,}" == "n" ]] && { echo "Aborted."; exit 0; }

# ============================================================
divider "Step 1: GitHub Configuration"
# ============================================================

GITHUB_REPO=""
GITHUB_PAT=""
GHCR_USER=""

prompt GITHUB_REPO "GitHub repository (owner/name)" "w-gitops/grocyscan"
GITHUB_URL="https://github.com/${GITHUB_REPO}"

echo ""
echo "  We need a GitHub Personal Access Token to:"
echo "    - Generate runner registration tokens"
echo "    - Login to GHCR for Docker image pulls"
echo ""
echo -e "  ${DIM}Create one at: https://github.com/settings/tokens${NC}"
echo -e "  ${DIM}Scopes needed: repo, admin:org (for runner tokens), packages:read${NC}"
echo ""
prompt_secret GITHUB_PAT "GitHub PAT"

if [[ -z "$GITHUB_PAT" ]]; then
  err "PAT is required to generate runner tokens."
  exit 1
fi

prompt GHCR_USER "GHCR username (for Docker login)" "$(echo "$GITHUB_REPO" | cut -d/ -f1)"

# ============================================================
divider "Step 2: Network Configuration"
# ============================================================

NETWORK_PREFIX=""
GATEWAY=""
BRIDGE=""
NAMESERVER=""
CI_LAST_OCTET=""
DEPLOY_LAST_OCTET=""

prompt NETWORK_PREFIX  "Network prefix (first 3 octets)" "192.168.200"
prompt GATEWAY         "Gateway IP" "${NETWORK_PREFIX}.2"
prompt BRIDGE          "Proxmox bridge" "vmbr0"
prompt NAMESERVER      "DNS server" "1.1.1.1"

echo ""
echo -e "  ${BOLD}LXC IP addresses:${NC}"
prompt CI_LAST_OCTET     "CI runner — last octet" "50"
prompt DEPLOY_LAST_OCTET "Deploy runner — last octet" "51"

CI_IP="${NETWORK_PREFIX}.${CI_LAST_OCTET}"
DEPLOY_IP="${NETWORK_PREFIX}.${DEPLOY_LAST_OCTET}"

# ============================================================
divider "Step 3: Container IDs"
# ============================================================

CTID_FORMULA=""
CI_CTID=""
DEPLOY_CTID=""

echo "  Your CTID formula: 11200 + last octet"
echo ""
prompt CI_CTID     "CI runner CTID" "$((11200 + CI_LAST_OCTET))"
prompt DEPLOY_CTID "Deploy runner CTID" "$((11200 + DEPLOY_LAST_OCTET))"

# ============================================================
divider "Step 4: Storage & Template"
# ============================================================

STORAGE=""
TEMPLATE_STORAGE=""

prompt STORAGE          "Rootfs storage" "local-lvm"
prompt TEMPLATE_STORAGE "Template storage" "local"

# ============================================================
divider "Step 5: Runner Names"
# ============================================================

CI_NAME=""
DEPLOY_NAME=""

prompt CI_NAME     "CI runner name" "grocyscan-ci"
prompt DEPLOY_NAME "Deploy runner name" "grocyscan-deploy"

# ---- Generate passwords ----
CI_PASSWORD=$(openssl rand -base64 16 2>/dev/null || head -c 16 /dev/urandom | base64)
DEPLOY_PASSWORD=$(openssl rand -base64 16 2>/dev/null || head -c 16 /dev/urandom | base64)

# ============================================================
divider "Review"
# ============================================================

echo -e "  ${BOLD}CI Runner:${NC}"
echo "    CTID:     ${CI_CTID}"
echo "    Name:     ${CI_NAME}"
echo "    IP:       ${CI_IP}/24"
echo "    Profile:  ci (2 vCPU, 4GB RAM, 30GB)"
echo ""
echo -e "  ${BOLD}Deploy Runner:${NC}"
echo "    CTID:     ${DEPLOY_CTID}"
echo "    Name:     ${DEPLOY_NAME}"
echo "    IP:       ${DEPLOY_IP}/24"
echo "    Profile:  deploy (2 vCPU, 4GB RAM, 50GB, nesting+keyctl)"
echo ""
echo -e "  ${BOLD}Network:${NC}"
echo "    Gateway:  ${GATEWAY}"
echo "    Bridge:   ${BRIDGE}"
echo "    DNS:      ${NAMESERVER}"
echo ""
echo -e "  ${BOLD}GitHub:${NC}"
echo "    Repo:     ${GITHUB_REPO}"
echo "    GHCR:     ${GHCR_USER}"
echo ""

read -rp "$(echo -e "${YELLOW}Create both LXCs and configure runners? [Y/n]${NC}: ")" confirm
[[ "${confirm,,}" == "n" ]] && { echo "Aborted."; exit 0; }

# ============================================================
divider "Installing prerequisites on Proxmox host"
# ============================================================

# gh CLI
if ! command -v gh &>/dev/null; then
  info "Installing GitHub CLI..."
  apt-get update -qq
  apt-get install -y -qq curl gnupg
  mkdir -p /etc/apt/keyrings
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    -o /etc/apt/keyrings/githubcli-archive-keyring.gpg
  chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list
  apt-get update -qq && apt-get install -y -qq gh
  ok "gh installed: $(gh --version | head -1)"
else
  ok "gh already installed: $(gh --version | head -1)"
fi

# jq
command -v jq &>/dev/null || apt-get install -y -qq jq

# ============================================================
divider "Generating runner registration tokens"
# ============================================================

info "Requesting two runner tokens from GitHub..."

CI_TOKEN=$(curl -sf \
  -X POST \
  -H "Authorization: token ${GITHUB_PAT}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${GITHUB_REPO}/actions/runners/registration-token" \
  | jq -r '.token') || { err "Failed to get CI runner token. Check your PAT."; exit 1; }

DEPLOY_TOKEN=$(curl -sf \
  -X POST \
  -H "Authorization: token ${GITHUB_PAT}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${GITHUB_REPO}/actions/runners/registration-token" \
  | jq -r '.token') || { err "Failed to get deploy runner token. Check your PAT."; exit 1; }

if [[ -z "$CI_TOKEN" || "$CI_TOKEN" == "null" ]]; then
  err "Runner token is empty. PAT may lack admin:org or repo scope."
  exit 1
fi

ok "Got runner tokens (valid for 1 hour)"

# ============================================================
# Download Debian template
# ============================================================
divider "Preparing Debian template"

TEMPLATE=$(pveam list "${TEMPLATE_STORAGE}" 2>/dev/null \
  | grep -i "debian-13-standard\|debian-12-standard" \
  | sort -V \
  | tail -1 \
  | awk '{print $1}')

if [[ -z "$TEMPLATE" ]]; then
  info "Downloading Debian template..."
  pveam update
  TEMPLATE_DL=$(pveam available --section system 2>/dev/null \
    | grep -iE "debian-(13|12)-standard" \
    | sort -V \
    | tail -1 \
    | awk '{print $2}')

  if [[ -z "$TEMPLATE_DL" ]]; then
    err "No Debian template found. Download one manually:"
    echo "  pveam download ${TEMPLATE_STORAGE} debian-12-standard_12.7-1_amd64.tar.zst"
    exit 1
  fi

  pveam download "${TEMPLATE_STORAGE}" "${TEMPLATE_DL}"
  TEMPLATE="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE_DL}"
fi

ok "Template: ${TEMPLATE}"

# ============================================================
# Helper: create one LXC
# ============================================================
create_lxc() {
  local ctid="$1" hostname="$2" ip="$3" cores="$4" memory="$5" disk="$6" features="$7" password="$8"

  info "Creating CT ${ctid} (${hostname}) at ${ip}..."

  local net_config="name=eth0,bridge=${BRIDGE},ip=${ip}/24,gw=${GATEWAY}"

  pct create "${ctid}" "${TEMPLATE}" \
    --hostname "${hostname}" \
    --cores "${cores}" \
    --memory "${memory}" \
    --swap 1024 \
    --rootfs "${STORAGE}:${disk}" \
    --net0 "${net_config}" \
    --nameserver "${NAMESERVER}" \
    --features "${features}" \
    --ostype debian \
    --unprivileged 1 \
    --password "${password}" \
    --start 0 \
    --onboot 1

  pct start "${ctid}"

  # Wait for boot
  info "Waiting for CT ${ctid} to boot..."
  for i in $(seq 1 30); do
    if pct exec "${ctid}" -- hostname >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  # Install SSH (for manual access later)
  info "Installing SSH in CT ${ctid}..."
  pct exec "${ctid}" -- bash -c "
    apt-get update -qq
    apt-get install -y -qq openssh-server curl ca-certificates gnupg
    sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
    sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
    systemctl enable --now ssh
    systemctl restart ssh
  " 2>&1 | tail -3

  ok "CT ${ctid} (${hostname}) running at ${ip}"
}

# ============================================================
# Helper: install runner inside LXC via pct exec
# ============================================================
install_runner() {
  local ctid="$1" profile="$2" name="$3" token="$4"

  info "Installing runner '${name}' (profile: ${profile}) in CT ${ctid}..."

  # Download setup-runner.sh into the LXC
  pct exec "${ctid}" -- bash -c "
    curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/setup-runner.sh
    chmod +x setup-runner.sh
  "

  # Run setup-runner.sh non-interactively
  pct exec "${ctid}" -- bash -c "
    bash /root/setup-runner.sh \
      --github-url '${GITHUB_URL}' \
      --runner-token '${token}' \
      --runner-name '${name}' \
      --profile '${profile}'
  " 2>&1 | while IFS= read -r line; do
    echo "    ${line}"
  done

  ok "Runner '${name}' installed in CT ${ctid}"
}

# ============================================================
divider "Creating CI Runner LXC (CT ${CI_CTID})"
# ============================================================

create_lxc "${CI_CTID}" "${CI_NAME}" "${CI_IP}" 2 4096 30 "nesting=1" "${CI_PASSWORD}"
install_runner "${CI_CTID}" "ci" "${CI_NAME}" "${CI_TOKEN}"

# ============================================================
divider "Creating Deploy Runner LXC (CT ${DEPLOY_CTID})"
# ============================================================

create_lxc "${DEPLOY_CTID}" "${DEPLOY_NAME}" "${DEPLOY_IP}" 2 4096 50 "nesting=1,keyctl=1" "${DEPLOY_PASSWORD}"
install_runner "${DEPLOY_CTID}" "deploy" "${DEPLOY_NAME}" "${DEPLOY_TOKEN}"

# ---- Login deploy runner to GHCR ----
info "Logging deploy runner into GHCR..."
pct exec "${DEPLOY_CTID}" -- bash -c "
  echo '${GITHUB_PAT}' | su - runner -c 'docker login ghcr.io -u ${GHCR_USER} --password-stdin' 2>&1
" | tail -2
ok "Deploy runner logged into GHCR"

# ============================================================
divider "Verifying runners"
# ============================================================

# Check runner services
for CTID_CHECK in "${CI_CTID}" "${DEPLOY_CTID}"; do
  SVC_STATUS=$(pct exec "${CTID_CHECK}" -- bash -c "
    systemctl is-active actions.runner.*.service 2>/dev/null || echo 'unknown'
  " 2>/dev/null)
  if [[ "$SVC_STATUS" == "active" ]]; then
    ok "CT ${CTID_CHECK}: runner service is active"
  else
    warn "CT ${CTID_CHECK}: runner service status: ${SVC_STATUS}"
    warn "  Check: pct exec ${CTID_CHECK} -- systemctl status actions.runner.*.service"
  fi
done

echo ""
info "Checking GitHub for registered runners..."
RUNNERS=$(curl -sf \
  -H "Authorization: token ${GITHUB_PAT}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${GITHUB_REPO}/actions/runners" \
  | jq -r '.runners[] | "  \(.name)\t\(.status)\t\(.labels | map(.name) | join(", "))"' 2>/dev/null) || true

if [[ -n "$RUNNERS" ]]; then
  echo ""
  echo -e "  ${BOLD}NAME\t\tSTATUS\tLABELS${NC}"
  echo "$RUNNERS"
else
  warn "Could not list runners (they may take a moment to appear)"
fi

# ============================================================
divider "Done!"
# ============================================================

echo -e "  ${BOLD}CI Runner:${NC}"
echo "    CT ${CI_CTID} — ${CI_NAME}"
echo "    IP: ${CI_IP}"
echo "    SSH: ssh root@${CI_IP}"
echo "    Password: ${CI_PASSWORD}"
echo ""
echo -e "  ${BOLD}Deploy Runner:${NC}"
echo "    CT ${DEPLOY_CTID} — ${DEPLOY_NAME}"
echo "    IP: ${DEPLOY_IP}"
echo "    SSH: ssh root@${DEPLOY_IP}"
echo "    Password: ${DEPLOY_PASSWORD}"
echo ""
echo -e "  ${BOLD}Runners should appear at:${NC}"
echo "    ${GITHUB_URL}/settings/actions/runners"
echo ""
echo -e "  ${BOLD}Remaining setup:${NC}"
echo ""
echo "  1. Add GitHub Secrets (repo Settings > Secrets > Actions):"
echo "     DEPLOY_SSH_KEY      — ed25519 private key for production (192.168.200.37)"
echo "     DEPLOY_HOST         — 192.168.200.37"
echo "     NPM_API_URL         — http://<npm-host>:81"
echo "     NPM_API_EMAIL       — NPM admin email"
echo "     NPM_API_PASSWORD    — NPM admin password"
echo "     NPM_CERT_ID         — wildcard cert ID in NPM (optional)"
echo ""
echo "  2. Add wildcard DNS records:"
echo "     *.preview.grocyscan.ssiops.com → ${DEPLOY_IP}"
echo "     dev.grocyscan.ssiops.com       → ${DEPLOY_IP}"
echo ""
echo "  3. Create the dev branch (if it doesn't exist):"
echo "     git checkout main && git checkout -b dev && git push -u origin dev"
echo ""
echo "  4. Push a PR targeting dev — the full pipeline will run!"
echo ""
echo -e "${BOLD}============================================${NC}"
