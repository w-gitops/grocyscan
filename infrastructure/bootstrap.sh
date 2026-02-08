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
#   6. (Optional) Installs Portainer Edge Agents in both LXCs
#   7. (Optional) Configures NPM HTTPS proxies for staging
#   8. Prints summary with all URLs and next steps
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
echo "  Optional: Portainer agents + NPM HTTPS proxy setup."
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

# ============================================================
divider "Step 6: Portainer Agent"
# ============================================================

PORTAINER_ENABLED=""
PORTAINER_URL=""
PORTAINER_EDGE_ID=""
PORTAINER_EDGE_KEY=""

echo "  If you have a Portainer instance, the bootstrap can install"
echo "  Portainer Edge Agents in both LXCs for monitoring."
echo ""
read -rp "$(echo -e "  ${CYAN}Install Portainer agents? [y/N]${NC}: ")" portainer_choice
if [[ "${portainer_choice,,}" == "y" ]]; then
  PORTAINER_ENABLED="true"
  echo ""
  echo -e "  ${DIM}Get the Edge key from: Portainer > Environments > Add > Edge Agent${NC}"
  echo ""
  prompt PORTAINER_URL      "Portainer server URL (e.g. https://portainer.local:9443)" ""
  prompt PORTAINER_EDGE_KEY "Edge key" ""
else
  PORTAINER_ENABLED="false"
fi

# ============================================================
divider "Step 7: Nginx Proxy Manager"
# ============================================================

NPM_ENABLED=""
NPM_API_URL=""
NPM_API_EMAIL=""
NPM_API_PASSWORD=""
NPM_CERT_ID=""

echo "  If you have Nginx Proxy Manager, the bootstrap can configure"
echo "  HTTPS proxy entries for the staging environment."
echo ""
read -rp "$(echo -e "  ${CYAN}Configure NPM proxies? [y/N]${NC}: ")" npm_choice
if [[ "${npm_choice,,}" == "y" ]]; then
  NPM_ENABLED="true"
  echo ""
  prompt       NPM_API_URL      "NPM API URL (e.g. http://192.168.200.10:81)" ""
  prompt       NPM_API_EMAIL    "NPM admin email" ""
  prompt_secret NPM_API_PASSWORD "NPM admin password"
  echo ""
  echo -e "  ${DIM}If you have a wildcard cert for *.preview.grocyscan.ssiops.com,${NC}"
  echo -e "  ${DIM}enter its ID from NPM > SSL Certificates. Leave blank to skip.${NC}"
  echo ""
  prompt NPM_CERT_ID "Wildcard certificate ID (blank to skip)" "0"
else
  NPM_ENABLED="false"
fi

# ============================================================
divider "Step 8: Homepage Dashboard"
# ============================================================

HOMEPAGE_ENABLED=""
HOMEPAGE_PORT="3010"
HOMEPAGE_DOMAIN=""
PROXMOX_URL=""

echo "  Homepage is a self-hosted dashboard that shows all active"
echo "  previews, staging, production, and tools in one page."
echo "  Preview stacks auto-appear/disappear via Docker labels."
echo ""
read -rp "$(echo -e "  ${CYAN}Install Homepage dashboard? [Y/n]${NC}: ")" hp_choice
if [[ "${hp_choice,,}" != "n" ]]; then
  HOMEPAGE_ENABLED="true"
  prompt HOMEPAGE_PORT   "Homepage port" "3010"
  prompt HOMEPAGE_DOMAIN "Homepage domain (blank to skip NPM proxy)" "ci.grocyscan.ssiops.com"
  prompt PROXMOX_URL     "Proxmox web UI URL" "https://proxmox.local:8006"
else
  HOMEPAGE_ENABLED="false"
fi

# ============================================================
divider "Step 9: Monitoring Tools"
# ============================================================

DOZZLE_ENABLED=""
DOZZLE_PORT="8080"

echo "  Additional monitoring tools for the runner LXCs:"
echo ""
echo -e "    ${GREEN}Dozzle${NC}       — Web UI for Docker container logs (deploy LXC)"
echo -e "    ${GREEN}lazydocker${NC}   — CLI dashboard for Docker (deploy LXC)"
echo -e "    ${GREEN}htop${NC}         — System monitor (both LXCs)"
echo ""
read -rp "$(echo -e "  ${CYAN}Install monitoring tools? [Y/n]${NC}: ")" mon_choice
if [[ "${mon_choice,,}" != "n" ]]; then
  DOZZLE_ENABLED="true"
  prompt DOZZLE_PORT "Dozzle web UI port" "8080"
else
  DOZZLE_ENABLED="false"
fi

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
echo -e "  ${BOLD}Extras:${NC}"
echo "    Portainer:  ${PORTAINER_ENABLED}"
echo "    NPM:        ${NPM_ENABLED}"
echo "    Homepage:   ${HOMEPAGE_ENABLED}"
echo "    Monitoring: ${DOZZLE_ENABLED}"
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

# CI LXC gets nesting+keyctl too (needed if Portainer agent uses Docker)
CI_FEATURES="nesting=1"
if [[ "$PORTAINER_ENABLED" == "true" ]]; then
  CI_FEATURES="nesting=1,keyctl=1"
fi
create_lxc "${CI_CTID}" "${CI_NAME}" "${CI_IP}" 2 4096 30 "${CI_FEATURES}" "${CI_PASSWORD}"
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

# ---- Install preview-status.sh on deploy runner ----
info "Installing preview-status.sh on deploy runner..."
pct exec "${DEPLOY_CTID}" -- bash -c "
  curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/scripts/preview-status.sh
  chmod +x preview-status.sh
  mv preview-status.sh /usr/local/bin/preview-status
"
ok "preview-status installed (run: ssh root@${DEPLOY_IP} preview-status)"

# ============================================================
# Portainer Edge Agent
# ============================================================
if [[ "$PORTAINER_ENABLED" == "true" && -n "$PORTAINER_EDGE_KEY" ]]; then
  divider "Installing Portainer Edge Agents"

  for PA_CTID in "${CI_CTID}" "${DEPLOY_CTID}"; do
    PA_NAME=$(pct exec "${PA_CTID}" -- hostname 2>/dev/null || echo "ct-${PA_CTID}")
    info "Installing Portainer agent in CT ${PA_CTID} (${PA_NAME})..."

    # Ensure Docker is available (CI LXC may not have it from the runner setup)
    HAS_DOCKER=$(pct exec "${PA_CTID}" -- bash -c "command -v docker && echo yes || echo no" 2>/dev/null)
    if [[ "$HAS_DOCKER" != *"yes"* ]]; then
      info "  Installing Docker in CT ${PA_CTID} for Portainer agent..."
      pct exec "${PA_CTID}" -- bash -c "
        apt-get install -y -qq ca-certificates curl gnupg
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
        chmod a+r /etc/apt/keyrings/docker.asc
        CODENAME=\$(. /etc/os-release && echo \"\$VERSION_CODENAME\")
        curl -sf \"https://download.docker.com/linux/debian/dists/\${CODENAME}/Release\" >/dev/null 2>&1 || CODENAME=bookworm
        echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \${CODENAME} stable\" \
          > /etc/apt/sources.list.d/docker.list
        apt-get update -qq
        apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
        systemctl enable --now docker
        usermod -aG docker runner 2>/dev/null || true
      " 2>&1 | tail -3
    fi

    # Run Portainer Edge Agent container
    pct exec "${PA_CTID}" -- bash -c "
      docker rm -f portainer_edge_agent 2>/dev/null || true
      docker run -d \
        --name portainer_edge_agent \
        --restart always \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /var/lib/docker/volumes:/var/lib/docker/volumes \
        -v /:/host \
        -v portainer_agent_data:/data \
        -e EDGE=1 \
        -e EDGE_ID='${PA_CTID}' \
        -e EDGE_KEY='${PORTAINER_EDGE_KEY}' \
        -e EDGE_INSECURE_POLL=1 \
        -e PORTAINER_URL='${PORTAINER_URL}' \
        portainer/agent:latest
    " 2>&1 | tail -2

    ok "Portainer agent running in CT ${PA_CTID}"
  done
fi

# ============================================================
# Nginx Proxy Manager — configure staging proxy
# ============================================================
if [[ "$NPM_ENABLED" == "true" && -n "$NPM_API_URL" ]]; then
  divider "Configuring Nginx Proxy Manager"

  # Download npm-proxy.sh into the deploy LXC
  pct exec "${DEPLOY_CTID}" -- bash -c "
    curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/scripts/npm-proxy.sh
    chmod +x npm-proxy.sh
  "

  # Test NPM connectivity
  info "Testing NPM API connectivity..."
  NPM_HEALTH=$(pct exec "${DEPLOY_CTID}" -- bash -c "
    export NPM_API_URL='${NPM_API_URL}'
    export NPM_API_EMAIL='${NPM_API_EMAIL}'
    export NPM_API_PASSWORD='${NPM_API_PASSWORD}'
    bash /root/npm-proxy.sh health 2>&1
  " 2>/dev/null) || true
  echo "    ${NPM_HEALTH}"

  # Create staging proxy: dev.grocyscan.ssiops.com → deploy_ip:9000
  info "Creating staging proxy: dev.grocyscan.ssiops.com → ${DEPLOY_IP}:9000"
  pct exec "${DEPLOY_CTID}" -- bash -c "
    export NPM_API_URL='${NPM_API_URL}'
    export NPM_API_EMAIL='${NPM_API_EMAIL}'
    export NPM_API_PASSWORD='${NPM_API_PASSWORD}'
    export NPM_CERT_ID='${NPM_CERT_ID:-0}'
    bash /root/npm-proxy.sh create dev.grocyscan.ssiops.com '${DEPLOY_IP}' 9000 2>&1
  " 2>/dev/null && ok "Staging proxy created" || warn "Staging proxy creation failed (staging may not be deployed yet — proxy will be created on first deploy)"

  # Note about preview proxies
  info "Preview proxies (pr-N.preview.grocyscan.ssiops.com) will be"
  info "created automatically by GitHub Actions on each PR."
fi

# ============================================================
# Monitoring tools
# ============================================================
if [[ "$DOZZLE_ENABLED" == "true" ]]; then
  divider "Installing monitoring tools"

  # ---- htop on both LXCs ----
  for MON_CTID in "${CI_CTID}" "${DEPLOY_CTID}"; do
    info "Installing htop in CT ${MON_CTID}..."
    pct exec "${MON_CTID}" -- apt-get install -y -qq htop 2>&1 | tail -1
  done
  ok "htop installed in both LXCs"

  # ---- Dozzle on deploy LXC (Docker log viewer) ----
  info "Installing Dozzle (Docker log viewer) in CT ${DEPLOY_CTID}..."
  pct exec "${DEPLOY_CTID}" -- bash -c "
    docker rm -f dozzle 2>/dev/null || true
    docker run -d \
      --name dozzle \
      --restart unless-stopped \
      -v /var/run/docker.sock:/var/run/docker.sock:ro \
      -p ${DOZZLE_PORT}:8080 \
      amir20/dozzle:latest
  " 2>&1 | tail -1
  ok "Dozzle running at http://${DEPLOY_IP}:${DOZZLE_PORT}"

  # ---- lazydocker on deploy LXC (CLI dashboard) ----
  info "Installing lazydocker in CT ${DEPLOY_CTID}..."
  pct exec "${DEPLOY_CTID}" -- bash -c "
    curl -sL https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash 2>&1
    # Move to /usr/local/bin if installed to home dir
    if [[ -f /root/.local/bin/lazydocker ]]; then
      mv /root/.local/bin/lazydocker /usr/local/bin/lazydocker
    fi
    # Also install for runner user
    if [[ -f /usr/local/bin/lazydocker ]]; then
      chmod +x /usr/local/bin/lazydocker
    fi
  " 2>&1 | tail -2
  ok "lazydocker installed (run: ssh root@${DEPLOY_IP} lazydocker)"

  # ---- lazydocker on CI LXC too if it has Docker ----
  HAS_DOCKER_CI=$(pct exec "${CI_CTID}" -- bash -c "command -v docker >/dev/null 2>&1 && echo yes || echo no" 2>/dev/null)
  if [[ "$HAS_DOCKER_CI" == *"yes"* ]]; then
    info "Installing lazydocker in CT ${CI_CTID}..."
    pct exec "${CI_CTID}" -- bash -c "
      curl -sL https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash 2>&1
      [[ -f /root/.local/bin/lazydocker ]] && mv /root/.local/bin/lazydocker /usr/local/bin/lazydocker
      chmod +x /usr/local/bin/lazydocker 2>/dev/null || true
    " 2>&1 | tail -1
    ok "lazydocker installed in CI LXC"
  fi
fi

# ============================================================
# Homepage Dashboard
# ============================================================
if [[ "$HOMEPAGE_ENABLED" == "true" ]]; then
  divider "Installing Homepage Dashboard"

  # Download homepage configs and compose file into the deploy LXC
  info "Downloading Homepage configuration..."
  pct exec "${DEPLOY_CTID}" -- bash -c "
    mkdir -p /opt/homepage
    cd /opt/homepage
    curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/docker/docker-compose.homepage.yml
    mkdir -p homepage
    for f in settings.yaml services.yaml docker.yaml widgets.yaml bookmarks.yaml; do
      curl -sL -o homepage/\$f https://raw.githubusercontent.com/w-gitops/grocyscan/main/docker/homepage/\$f
    done
  "

  # Build the environment file for Homepage
  PORTAINER_URL_VAL="${PORTAINER_URL:-}"
  NPM_URL_VAL="${NPM_API_URL:-}"
  DOZZLE_PORT_VAL="${DOZZLE_PORT:-8080}"

  info "Starting Homepage container..."
  pct exec "${DEPLOY_CTID}" -- bash -c "
    cd /opt/homepage
    cat > .env << 'HPEOF'
HOMEPAGE_PORT=${HOMEPAGE_PORT}
HOMEPAGE_VAR_PROD_URL=https://grocyscan.ssiops.com
HOMEPAGE_VAR_PROD_HEALTH_URL=http://192.168.200.37:3334/health
HOMEPAGE_VAR_STAGING_URL=https://dev.grocyscan.ssiops.com
HOMEPAGE_VAR_GITHUB_URL=https://github.com/${GITHUB_REPO}
HOMEPAGE_VAR_DEPLOY_IP=${DEPLOY_IP}
HOMEPAGE_VAR_DOZZLE_PORT=${DOZZLE_PORT_VAL}
HOMEPAGE_VAR_PORTAINER_URL=${PORTAINER_URL_VAL}
HOMEPAGE_VAR_NPM_URL=${NPM_URL_VAL}
HOMEPAGE_VAR_PROXMOX_URL=${PROXMOX_URL:-https://proxmox.local:8006}
HPEOF

    docker compose -f docker-compose.homepage.yml up -d
  " 2>&1 | tail -3

  ok "Homepage running at http://${DEPLOY_IP}:${HOMEPAGE_PORT}"

  # Create NPM proxy for Homepage if domain provided
  if [[ -n "$HOMEPAGE_DOMAIN" && "$NPM_ENABLED" == "true" ]]; then
    info "Creating NPM proxy for Homepage: ${HOMEPAGE_DOMAIN}"
    pct exec "${DEPLOY_CTID}" -- bash -c "
      export NPM_API_URL='${NPM_API_URL}'
      export NPM_API_EMAIL='${NPM_API_EMAIL}'
      export NPM_API_PASSWORD='${NPM_API_PASSWORD}'
      export NPM_CERT_ID='${NPM_CERT_ID:-0}'
      bash /root/npm-proxy.sh create '${HOMEPAGE_DOMAIN}' '${DEPLOY_IP}' ${HOMEPAGE_PORT} 2>&1
    " 2>/dev/null && ok "Homepage proxy: https://${HOMEPAGE_DOMAIN}" \
      || warn "Homepage NPM proxy failed — accessible via HTTP"
  fi
fi

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
if [[ "$PORTAINER_ENABLED" == "true" ]]; then
  echo -e "  ${BOLD}Portainer:${NC}"
  echo "    Agents running in both LXCs"
  echo "    Server: ${PORTAINER_URL}"
  echo ""
fi

if [[ "$NPM_ENABLED" == "true" ]]; then
  echo -e "  ${BOLD}Nginx Proxy Manager:${NC}"
  echo "    API: ${NPM_API_URL}"
  echo "    Staging proxy: dev.grocyscan.ssiops.com → ${DEPLOY_IP}:9000"
  echo "    Preview proxies: created automatically per PR"
  echo ""
fi

if [[ "$HOMEPAGE_ENABLED" == "true" ]]; then
  echo -e "  ${BOLD}Dashboard:${NC}"
  if [[ -n "$HOMEPAGE_DOMAIN" && "$NPM_ENABLED" == "true" ]]; then
    echo "    Homepage: https://${HOMEPAGE_DOMAIN}"
  else
    echo "    Homepage: http://${DEPLOY_IP}:${HOMEPAGE_PORT}"
  fi
  echo "    Previews auto-appear/disappear via Docker labels"
  echo ""
fi

echo -e "  ${BOLD}Debugging:${NC}"
echo "    Preview dashboard:  ssh root@${DEPLOY_IP} preview-status"
echo "    Preview logs:       ssh root@${DEPLOY_IP} preview-status logs pr-<N>"
echo "    Preview inspect:    ssh root@${DEPLOY_IP} preview-status inspect pr-<N>"
echo ""

if [[ "$DOZZLE_ENABLED" == "true" ]]; then
  echo -e "  ${BOLD}Monitoring:${NC}"
  echo "    Dozzle (logs):  http://${DEPLOY_IP}:${DOZZLE_PORT}"
  echo "    lazydocker:     ssh root@${DEPLOY_IP} lazydocker"
  echo "    htop:           ssh root@<IP> htop"
  echo ""
fi

echo -e "  ${BOLD}Remaining setup:${NC}"
echo ""

REMAINING_STEP=0
next_step() { REMAINING_STEP=$((REMAINING_STEP + 1)); echo "  ${REMAINING_STEP}."; }

echo -n "$(next_step)" && echo " Add GitHub Secrets (repo Settings > Secrets > Actions):"
echo "     DEPLOY_SSH_KEY      — ed25519 private key for production (192.168.200.37)"
echo "     DEPLOY_HOST         — 192.168.200.37"
if [[ "$NPM_ENABLED" == "true" ]]; then
  echo "     NPM_API_URL         — ${NPM_API_URL}"
  echo "     NPM_API_EMAIL       — ${NPM_API_EMAIL}"
  echo "     NPM_API_PASSWORD    — (already configured)"
  echo "     NPM_CERT_ID         — ${NPM_CERT_ID:-0}"
else
  echo "     NPM_API_URL         — http://<npm-host>:81"
  echo "     NPM_API_EMAIL       — NPM admin email"
  echo "     NPM_API_PASSWORD    — NPM admin password"
  echo "     NPM_CERT_ID         — wildcard cert ID in NPM (optional)"
fi
echo ""

echo -n "$(next_step)" && echo " Add wildcard DNS records:"
echo "     *.preview.grocyscan.ssiops.com → ${DEPLOY_IP}"
echo "     dev.grocyscan.ssiops.com       → ${DEPLOY_IP}"
echo ""

echo -n "$(next_step)" && echo " Create the dev branch (if it doesn't exist):"
echo "     git checkout main && git checkout -b dev && git push -u origin dev"
echo ""

echo -n "$(next_step)" && echo " Push a PR targeting dev — the full pipeline will run!"
echo ""
echo -e "${BOLD}============================================${NC}"
