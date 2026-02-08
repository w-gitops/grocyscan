#!/usr/bin/env bash
# ============================================================
# GrocyScan — Proxmox LXC Provisioner
# ============================================================
# Run this ON the Proxmox host to create Debian 13 (Trixie) LXC
# containers for GitHub Actions runners.
#
# Two modes:
#   Interactive:  bash create-lxc.sh           (prompts for values)
#   CLI flags:    bash create-lxc.sh --profile ci --ctid 11250 ...
#
# Any value provided as a flag skips its prompt in interactive mode.
#
# Profiles:
#   ci      2 vCPU, 4GB RAM, 30GB — for pytest + Playwright
#   deploy  2 vCPU, 4GB RAM, 50GB — for Docker preview/staging stacks
#   all     4 vCPU, 6GB RAM, 50GB — combined CI + deploy
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
PROFILE=""
CTID=""
HOSTNAME=""
STORAGE="local-lvm"
TEMPLATE_STORAGE="local"
IP=""
GATEWAY="192.168.200.2"
NAMESERVER="1.1.1.1"
SSH_PUBKEY=""
BRIDGE="vmbr0"
PASSWORD=""
DEBIAN_VERSION="13"
TEMPLATE_NAME="debian-13-standard"
INTERACTIVE=false

# ---- Parse Arguments ----
if [[ $# -eq 0 ]]; then
  INTERACTIVE=true
fi

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)           PROFILE="$2"; shift 2 ;;
    --ctid)              CTID="$2"; shift 2 ;;
    --hostname)          HOSTNAME="$2"; shift 2 ;;
    --storage)           STORAGE="$2"; shift 2 ;;
    --template-storage)  TEMPLATE_STORAGE="$2"; shift 2 ;;
    --ip)                IP="$2"; shift 2 ;;
    --gw)                GATEWAY="$2"; shift 2 ;;
    --nameserver)        NAMESERVER="$2"; shift 2 ;;
    --ssh-key)           SSH_PUBKEY="$2"; shift 2 ;;
    --bridge)            BRIDGE="$2"; shift 2 ;;
    --password)          PASSWORD="$2"; shift 2 ;;
    -i|--interactive)    INTERACTIVE=true; shift ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Run with no arguments for interactive mode, or pass flags:"
      echo ""
      echo "Options:"
      echo "  --profile      PROFILE  ci | deploy | all"
      echo "  --ctid         NUM      Container ID"
      echo "  --hostname     NAME     Hostname (auto-set from profile)"
      echo "  --storage      STORE    Proxmox rootfs storage (default: local-lvm)"
      echo "  --ip           IP/CIDR  Static IP (e.g. 192.168.200.50/24) or 'dhcp'"
      echo "  --gw           IP       Gateway (default: 192.168.200.2)"
      echo "  --nameserver   IP       DNS server (default: 1.1.1.1)"
      echo "  --ssh-key      PATH     SSH public key file to inject"
      echo "  --bridge       NAME     Network bridge (default: vmbr0)"
      echo "  --password     PASS     Root password (generated if omitted)"
      echo "  -i, --interactive       Force interactive prompts"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ---- Validate environment ----
if ! command -v pct &>/dev/null; then
  echo "ERROR: pct not found — this script must run on a Proxmox host"
  exit 1
fi

# ---- Interactive prompts ----
# Each prompt only fires if the value wasn't already set by a CLI flag.

prompt() {
  local var_name="$1"
  local prompt_text="$2"
  local default="$3"
  local current_val="${!var_name}"

  if [[ -n "$current_val" ]]; then
    return  # Already set via CLI flag
  fi

  if [[ -n "$default" ]]; then
    read -rp "$(echo -e "${CYAN}${prompt_text}${NC} ${DIM}[${default}]${NC}: ")" input
    eval "${var_name}=\"${input:-$default}\""
  else
    read -rp "$(echo -e "${CYAN}${prompt_text}${NC}: ")" input
    eval "${var_name}=\"${input}\""
  fi
}

if [[ "$INTERACTIVE" == true ]] || [[ -z "$PROFILE" ]]; then
  echo ""
  echo -e "${BOLD}============================================${NC}"
  echo -e "${BOLD}  GrocyScan — LXC Provisioner${NC}"
  echo -e "${BOLD}============================================${NC}"
  echo ""

  # ---- Profile selection ----
  if [[ -z "$PROFILE" ]]; then
    echo -e "${BOLD}Select runner profile:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} ci      — pytest + Playwright    (2 vCPU, 4GB RAM, 30GB)"
    echo -e "  ${GREEN}2)${NC} deploy  — Docker previews/staging (2 vCPU, 4GB RAM, 50GB, nesting)"
    echo -e "  ${GREEN}3)${NC} all     — Combined CI + deploy    (4 vCPU, 6GB RAM, 50GB, nesting)"
    echo ""
    read -rp "$(echo -e "${CYAN}Profile [1/2/3]${NC} ${DIM}[3]${NC}: ")" profile_choice
    case "${profile_choice:-3}" in
      1|ci)     PROFILE="ci" ;;
      2|deploy) PROFILE="deploy" ;;
      3|all)    PROFILE="all" ;;
      *) echo "Invalid choice, using 'all'"; PROFILE="all" ;;
    esac
  fi
  echo ""

  # ---- Network ----
  echo -e "${BOLD}Network configuration:${NC}"
  echo ""
  prompt IP        "  Static IP (CIDR, e.g. 192.168.200.50/24)" ""
  if [[ -n "$IP" && "$IP" != "dhcp" ]]; then
    prompt GATEWAY   "  Gateway" "192.168.200.2"
  fi
  prompt BRIDGE     "  Bridge" "vmbr0"
  prompt NAMESERVER "  DNS server" "1.1.1.1"
  echo ""

  # ---- Container ID ----
  # Auto-suggest from IP using 11200+octet formula
  SUGGESTED_CTID=""
  if [[ -n "$IP" && "$IP" != "dhcp" ]]; then
    LAST_OCTET=$(echo "$IP" | grep -oP '\d+\.\d+\.\d+\.\K\d+' || echo "")
    if [[ -n "$LAST_OCTET" ]]; then
      SUGGESTED_CTID=$((11200 + LAST_OCTET))
    fi
  fi
  if [[ -z "$SUGGESTED_CTID" ]]; then
    SUGGESTED_CTID=$(pvesh get /cluster/nextid 2>/dev/null || echo "200")
  fi

  echo -e "${BOLD}Container settings:${NC}"
  echo ""
  prompt CTID     "  Container ID (CTID)" "$SUGGESTED_CTID"
  prompt HOSTNAME "  Hostname" ""
  prompt STORAGE  "  Rootfs storage" "local-lvm"
  echo ""

  # ---- Optional ----
  echo -e "${BOLD}Optional:${NC}"
  echo ""
  prompt SSH_PUBKEY "  SSH public key file (blank to skip)" ""
  prompt PASSWORD   "  Root password (blank to generate)" ""
  echo ""
fi

# ---- Profile-based sizing ----
case "$PROFILE" in
  ci)
    CORES=2; MEMORY=4096; SWAP=1024; DISK="30"
    [[ -z "$HOSTNAME" ]] && HOSTNAME="grocyscan-ci"
    FEATURES="nesting=1"
    ;;
  deploy)
    CORES=2; MEMORY=4096; SWAP=1024; DISK="50"
    [[ -z "$HOSTNAME" ]] && HOSTNAME="grocyscan-deploy"
    FEATURES="nesting=1,keyctl=1"
    ;;
  all)
    CORES=4; MEMORY=6144; SWAP=2048; DISK="50"
    [[ -z "$HOSTNAME" ]] && HOSTNAME="grocyscan-runner"
    FEATURES="nesting=1,keyctl=1"
    ;;
  *)
    echo "ERROR: Unknown profile '$PROFILE' (use ci, deploy, or all)"
    exit 1
    ;;
esac

# Auto-detect CTID if still empty
if [[ -z "$CTID" ]]; then
  CTID=$(pvesh get /cluster/nextid 2>/dev/null || echo "200")
fi

# Default to DHCP if no IP given
if [[ -z "$IP" ]]; then
  IP="dhcp"
fi

# Generate password if not provided
if [[ -z "$PASSWORD" ]]; then
  PASSWORD=$(openssl rand -base64 16 2>/dev/null || head -c 16 /dev/urandom | base64)
fi

# ---- Confirmation ----
echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  Creating LXC: ${HOSTNAME} (CT ${CTID})${NC}"
echo -e "${BOLD}============================================${NC}"
echo -e "  Profile:   ${GREEN}${PROFILE}${NC}"
echo -e "  Cores:     ${CORES}"
echo -e "  Memory:    ${MEMORY}MB"
echo -e "  Disk:      ${DISK}GB"
echo -e "  Features:  ${FEATURES}"
echo -e "  IP:        ${IP}"
if [[ "$IP" != "dhcp" ]]; then
  echo -e "  Gateway:   ${GATEWAY}"
fi
echo -e "  Bridge:    ${BRIDGE}"
echo -e "  Storage:   ${STORAGE}"
echo -e "${BOLD}============================================${NC}"

if [[ "$INTERACTIVE" == true ]]; then
  echo ""
  read -rp "$(echo -e "${YELLOW}Proceed? [Y/n]${NC}: ")" confirm
  if [[ "${confirm,,}" == "n" ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# ---- Download Debian template if needed ----
TEMPLATE=$(pveam list "${TEMPLATE_STORAGE}" 2>/dev/null \
  | grep -i "${TEMPLATE_NAME}" \
  | sort -V \
  | tail -1 \
  | awk '{print $1}')

if [[ -z "$TEMPLATE" ]]; then
  echo ""
  echo "Downloading Debian ${DEBIAN_VERSION} template..."
  pveam update
  TEMPLATE_DL=$(pveam available --section system 2>/dev/null \
    | grep -i "debian-${DEBIAN_VERSION}" \
    | head -1 \
    | awk '{print $2}')

  if [[ -z "$TEMPLATE_DL" ]]; then
    echo "  Debian ${DEBIAN_VERSION} template not found, trying Debian 12 (Bookworm)..."
    TEMPLATE_DL=$(pveam available --section system 2>/dev/null \
      | grep -i "debian-12" \
      | head -1 \
      | awk '{print $2}')
    if [[ -z "$TEMPLATE_DL" ]]; then
      echo "ERROR: No Debian template found. Download manually:"
      echo "  pveam download ${TEMPLATE_STORAGE} debian-13-standard_13.0-1_amd64.tar.zst"
      exit 1
    fi
  fi

  pveam download "${TEMPLATE_STORAGE}" "${TEMPLATE_DL}"
  TEMPLATE="${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE_DL}"
fi

echo "Using template: ${TEMPLATE}"

# ---- Build network config ----
if [[ "$IP" == "dhcp" ]]; then
  NET_CONFIG="name=eth0,bridge=${BRIDGE},ip=dhcp"
else
  if [[ -z "$GATEWAY" ]]; then
    echo "ERROR: Gateway is required when using a static IP"
    exit 1
  fi
  NET_CONFIG="name=eth0,bridge=${BRIDGE},ip=${IP},gw=${GATEWAY}"
fi

# ---- Create LXC ----
echo ""
echo "Creating container..."

PCT_ARGS=(
  "${CTID}"
  "${TEMPLATE}"
  --hostname "${HOSTNAME}"
  --cores "${CORES}"
  --memory "${MEMORY}"
  --swap "${SWAP}"
  --rootfs "${STORAGE}:${DISK}"
  --net0 "${NET_CONFIG}"
  --nameserver "${NAMESERVER}"
  --features "${FEATURES}"
  --ostype debian
  --unprivileged 1
  --password "${PASSWORD}"
  --start 0
  --onboot 1
)

if [[ -n "$SSH_PUBKEY" && -f "$SSH_PUBKEY" ]]; then
  PCT_ARGS+=(--ssh-public-keys "${SSH_PUBKEY}")
fi

pct create "${PCT_ARGS[@]}"

echo "Container ${CTID} created."

# ---- Start LXC ----
echo "Starting container..."
pct start "${CTID}"
sleep 3

# Wait for network
echo "Waiting for network..."
LXC_IP=""
for i in $(seq 1 30); do
  LXC_IP=$(pct exec "${CTID}" -- hostname -I 2>/dev/null | awk '{print $1}')
  if [[ -n "$LXC_IP" ]]; then
    break
  fi
  sleep 1
done

if [[ -z "$LXC_IP" ]]; then
  echo "WARNING: Could not detect LXC IP. Check network config."
  LXC_IP="(unknown)"
fi

# ---- Enable SSH ----
echo "Enabling SSH..."
pct exec "${CTID}" -- bash -c "
  apt-get update -qq
  apt-get install -y -qq openssh-server curl
  systemctl enable --now ssh
  sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
  sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
  systemctl restart ssh
"

echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${GREEN}  LXC Created Successfully!${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""
echo "  CTID:     ${CTID}"
echo "  Hostname: ${HOSTNAME}"
echo "  IP:       ${LXC_IP}"
echo "  Profile:  ${PROFILE}"
echo "  Password: ${PASSWORD}"
echo ""
echo "  SSH:      ssh root@${LXC_IP}"
echo ""
echo "  Next steps:"
echo "  1. SSH into the LXC:"
echo "     ssh root@${LXC_IP}"
echo ""
echo "  2. Get a runner registration token:"
echo "     gh api -X POST repos/w-gitops/grocyscan/actions/runners/registration-token --jq .token"
echo ""
echo "  3. Download and run the runner setup script:"
  echo "     curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/setup-runner.sh"
echo "     bash setup-runner.sh \\"
echo "       --github-url https://github.com/w-gitops/grocyscan \\"
echo "       --runner-token <TOKEN> \\"
echo "       --runner-name ${HOSTNAME} \\"
echo "       --profile ${PROFILE}"
echo ""
if [[ "$PROFILE" == "deploy" || "$PROFILE" == "all" ]]; then
  echo "  4. Login to GHCR (inside the LXC):"
  echo "     echo \$PAT | docker login ghcr.io -u <username> --password-stdin"
  echo ""
fi
echo "============================================"
