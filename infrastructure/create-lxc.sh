#!/usr/bin/env bash
# ============================================================
# GrocyScan — Proxmox LXC Provisioner
# ============================================================
# Run this ON the Proxmox host to create Debian 13 (Trixie) LXC
# containers for GitHub Actions runners.
#
# Creates an unprivileged LXC with:
#   - Debian 13 (Trixie) template
#   - nesting + keyctl enabled (required for Docker-in-LXC)
#   - Static IP or DHCP
#   - SSH root access with key
#
# After creation, SSH into the LXC and run setup-runner.sh to
# install the GitHub Actions runner.
#
# Usage (run on Proxmox host):
#   bash create-lxc.sh --profile ci
#   bash create-lxc.sh --profile deploy
#   bash create-lxc.sh --profile all
#   bash create-lxc.sh --profile all --ctid 200 --ip 192.168.200.50/24 --gw 192.168.200.1
#
# Profiles:
#   ci      2 vCPU, 4GB RAM, 30GB — for pytest + Playwright
#   deploy  2 vCPU, 4GB RAM, 50GB — for Docker preview/staging stacks
#   all     4 vCPU, 6GB RAM, 50GB — combined CI + deploy
# ============================================================

set -euo pipefail

# ---- Defaults ----
PROFILE="all"
CTID=""                  # Auto-detect next available if empty
HOSTNAME=""              # Auto-set from profile if empty
STORAGE="local-lvm"      # Proxmox storage for rootfs
TEMPLATE_STORAGE="local" # Where CT templates are stored
IP="dhcp"                # Static IP (CIDR) or "dhcp"
GATEWAY=""               # Required if static IP
NAMESERVER="1.1.1.1"
SSH_PUBKEY=""            # Path to SSH public key to inject
BRIDGE="vmbr0"
PASSWORD=""              # Root password (generated if empty)
DEBIAN_VERSION="13"
TEMPLATE_NAME="debian-13-standard"  # Proxmox template name prefix

# ---- Parse Arguments ----
while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)   PROFILE="$2"; shift 2 ;;
    --ctid)      CTID="$2"; shift 2 ;;
    --hostname)  HOSTNAME="$2"; shift 2 ;;
    --storage)   STORAGE="$2"; shift 2 ;;
    --ip)        IP="$2"; shift 2 ;;
    --gw)        GATEWAY="$2"; shift 2 ;;
    --ssh-key)   SSH_PUBKEY="$2"; shift 2 ;;
    --bridge)    BRIDGE="$2"; shift 2 ;;
    --password)  PASSWORD="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 --profile <ci|deploy|all> [options]"
      echo ""
      echo "Options:"
      echo "  --ctid      NUM       Container ID (auto-detect if omitted)"
      echo "  --hostname  NAME      Hostname (auto-set from profile)"
      echo "  --storage   STORE     Proxmox storage (default: local-lvm)"
      echo "  --ip        IP/CIDR   Static IP or 'dhcp' (default: dhcp)"
      echo "  --gw        IP        Gateway (required for static IP)"
      echo "  --ssh-key   PATH      SSH public key file to inject"
      echo "  --bridge    NAME      Network bridge (default: vmbr0)"
      echo "  --password  PASS      Root password (generated if omitted)"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ---- Validate ----
if ! command -v pct &>/dev/null; then
  echo "ERROR: pct not found — this script must run on a Proxmox host"
  exit 1
fi

# ---- Profile-based sizing ----
case "$PROFILE" in
  ci)
    CORES=2; MEMORY=4096; SWAP=1024; DISK="30"
    [[ -z "$HOSTNAME" ]] && HOSTNAME="grocyscan-ci"
    FEATURES="nesting=1"  # No Docker, but nesting doesn't hurt
    ;;
  deploy)
    CORES=2; MEMORY=4096; SWAP=1024; DISK="50"
    [[ -z "$HOSTNAME" ]] && HOSTNAME="grocyscan-deploy"
    FEATURES="nesting=1,keyctl=1"  # Required for Docker-in-LXC
    ;;
  all)
    CORES=4; MEMORY=6144; SWAP=2048; DISK="50"
    [[ -z "$HOSTNAME" ]] && HOSTNAME="grocyscan-runner"
    FEATURES="nesting=1,keyctl=1"  # Required for Docker-in-LXC
    ;;
  *)
    echo "ERROR: Unknown profile '$PROFILE' (use ci, deploy, or all)"
    exit 1
    ;;
esac

# Auto-detect next CTID
if [[ -z "$CTID" ]]; then
  CTID=$(pvesh get /cluster/nextid 2>/dev/null || echo "200")
  echo "Auto-assigned CTID: ${CTID}"
fi

# Generate password if not provided
if [[ -z "$PASSWORD" ]]; then
  PASSWORD=$(openssl rand -base64 16 2>/dev/null || head -c 16 /dev/urandom | base64)
fi

# ---- Download Debian template if needed ----
echo "============================================"
echo "  Creating LXC: ${HOSTNAME} (CT ${CTID})"
echo "============================================"
echo "  Profile:  ${PROFILE}"
echo "  Cores:    ${CORES}"
echo "  Memory:   ${MEMORY}MB"
echo "  Disk:     ${DISK}GB"
echo "  Features: ${FEATURES}"
echo "  Network:  ${IP} on ${BRIDGE}"
echo "============================================"

# Find or download the Debian template
TEMPLATE=$(pveam list "${TEMPLATE_STORAGE}" 2>/dev/null \
  | grep -i "${TEMPLATE_NAME}" \
  | sort -V \
  | tail -1 \
  | awk '{print $1}')

if [[ -z "$TEMPLATE" ]]; then
  echo ""
  echo "Downloading Debian ${DEBIAN_VERSION} template..."
  pveam update
  # Find the available template name
  TEMPLATE_DL=$(pveam available --section system 2>/dev/null \
    | grep -i "debian-${DEBIAN_VERSION}" \
    | head -1 \
    | awk '{print $2}')

  if [[ -z "$TEMPLATE_DL" ]]; then
    # Fallback: try debian-12 if 13 isn't available yet
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
    echo "ERROR: --gw is required when using a static IP"
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

# Add SSH key if provided
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
  # Allow root login with password (for initial setup)
  sed -i 's/^#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
  sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
  systemctl restart ssh
"

echo ""
echo "============================================"
echo "  LXC Created Successfully!"
echo "============================================"
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
  echo "     curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/dev/infrastructure/setup-runner.sh"
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
