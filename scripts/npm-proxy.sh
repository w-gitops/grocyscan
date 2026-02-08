#!/usr/bin/env bash
# ============================================================
# Nginx Proxy Manager — API Helper
# ============================================================
# Manages HTTPS proxy hosts via the NPM REST API.
# Used by CI/CD workflows to create/delete proxy entries for
# preview deployments.
#
# Prerequisites:
#   - NPM instance accessible from the runner
#   - Wildcard DNS: *.preview.grocyscan.ssiops.com → runner IP
#   - (Optional) Wildcard SSL certificate pre-configured in NPM
#
# Environment variables (set via GitHub Secrets or .env):
#   NPM_API_URL      - NPM API base URL  (e.g. http://192.168.200.10:81)
#   NPM_API_EMAIL    - NPM admin email
#   NPM_API_PASSWORD - NPM admin password
#   NPM_CERT_ID      - (Optional) Wildcard certificate ID in NPM
#
# Usage:
#   ./scripts/npm-proxy.sh create  <domain> <forward_host> <forward_port>
#   ./scripts/npm-proxy.sh delete  <domain>
#   ./scripts/npm-proxy.sh list
#   ./scripts/npm-proxy.sh find    <domain>
#   ./scripts/npm-proxy.sh health
#
# Examples:
#   ./scripts/npm-proxy.sh create pr-42.preview.grocyscan.ssiops.com 127.0.0.1 10042
#   ./scripts/npm-proxy.sh delete pr-42.preview.grocyscan.ssiops.com
#   ./scripts/npm-proxy.sh find   pr-42.preview.grocyscan.ssiops.com
# ============================================================

set -euo pipefail

# ---- Configuration ----
NPM_API_URL="${NPM_API_URL:?NPM_API_URL is required (e.g. http://192.168.200.10:81)}"
NPM_API_EMAIL="${NPM_API_EMAIL:?NPM_API_EMAIL is required}"
NPM_API_PASSWORD="${NPM_API_PASSWORD:?NPM_API_PASSWORD is required}"
NPM_CERT_ID="${NPM_CERT_ID:-0}"  # 0 = no cert / Let's Encrypt, >0 = existing cert ID

# ---- Helpers ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[NPM]${NC} $*" >&2; }
ok()    { echo -e "${GREEN}[NPM]${NC} $*" >&2; }
warn()  { echo -e "${YELLOW}[NPM]${NC} $*" >&2; }
err()   { echo -e "${RED}[NPM]${NC} $*" >&2; }

# ---- Authentication ----
# Gets a JWT token from NPM. Caches in a temp file for the session.
TOKEN_CACHE="/tmp/.npm-proxy-token-$$"
trap 'rm -f "$TOKEN_CACHE"' EXIT

get_token() {
  if [[ -f "$TOKEN_CACHE" ]]; then
    cat "$TOKEN_CACHE"
    return
  fi

  info "Authenticating with NPM at ${NPM_API_URL}..."
  local response
  response=$(curl -sf -X POST "${NPM_API_URL}/api/tokens" \
    -H "Content-Type: application/json" \
    -d "{
      \"identity\": \"${NPM_API_EMAIL}\",
      \"secret\": \"${NPM_API_PASSWORD}\"
    }" 2>/dev/null) || {
    err "Authentication failed. Check NPM_API_URL, NPM_API_EMAIL, NPM_API_PASSWORD."
    return 1
  }

  local token
  token=$(echo "$response" | jq -r '.token // empty')
  if [[ -z "$token" ]]; then
    err "No token in response: ${response}"
    return 1
  fi

  echo "$token" > "$TOKEN_CACHE"
  echo "$token"
}

# Authenticated API call
npm_api() {
  local method="$1"
  local endpoint="$2"
  shift 2
  local token
  token=$(get_token) || return 1

  curl -sf -X "$method" "${NPM_API_URL}/api/${endpoint}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${token}" \
    "$@"
}

# ---- Commands ----

cmd_create() {
  local domain="${1:?Usage: npm-proxy.sh create <domain> <forward_host> <forward_port>}"
  local forward_host="${2:?Usage: npm-proxy.sh create <domain> <forward_host> <forward_port>}"
  local forward_port="${3:?Usage: npm-proxy.sh create <domain> <forward_host> <forward_port>}"

  info "Creating proxy: ${domain} → ${forward_host}:${forward_port}"

  # Check if proxy already exists
  local existing_id
  existing_id=$(cmd_find "$domain" 2>/dev/null || echo "")
  if [[ -n "$existing_id" && "$existing_id" != "0" ]]; then
    info "Proxy for ${domain} already exists (ID: ${existing_id}). Updating..."
    cmd_update "$existing_id" "$domain" "$forward_host" "$forward_port"
    return
  fi

  # Build the proxy host payload
  local ssl_forced="false"
  local cert_id=0
  local letsencrypt_agree="false"
  local letsencrypt_email=""
  local http2="false"
  local hsts="false"

  if [[ "${NPM_CERT_ID}" -gt 0 ]]; then
    # Use pre-configured wildcard certificate
    cert_id="${NPM_CERT_ID}"
    ssl_forced="true"
    http2="true"
    hsts="true"
    info "Using wildcard certificate ID: ${cert_id}"
  fi

  local payload
  payload=$(jq -n \
    --arg domain "$domain" \
    --arg host "$forward_host" \
    --argjson port "$forward_port" \
    --argjson cert_id "$cert_id" \
    --argjson ssl_forced "$ssl_forced" \
    --argjson http2 "$http2" \
    --argjson hsts "$hsts" \
    '{
      domain_names: [$domain],
      forward_scheme: "http",
      forward_host: $host,
      forward_port: $port,
      certificate_id: $cert_id,
      ssl_forced: $ssl_forced,
      http2_support: $http2,
      hsts_enabled: $hsts,
      hsts_subdomains: false,
      block_exploits: true,
      caching_enabled: false,
      allow_websocket_upgrade: true,
      access_list_id: 0,
      advanced_config: "",
      meta: {
        letsencrypt_agree: false,
        dns_challenge: false
      },
      locations: []
    }')

  local response
  response=$(npm_api POST "nginx/proxy-hosts" -d "$payload") || {
    err "Failed to create proxy host for ${domain}"
    return 1
  }

  local new_id
  new_id=$(echo "$response" | jq -r '.id // empty')
  if [[ -n "$new_id" ]]; then
    ok "Proxy created: ${domain} → ${forward_host}:${forward_port} (ID: ${new_id})"
    # Output the ID for use by callers
    echo "$new_id"
  else
    err "Unexpected response: ${response}"
    return 1
  fi
}

cmd_update() {
  local proxy_id="${1:?proxy_id required}"
  local domain="${2:?domain required}"
  local forward_host="${3:?forward_host required}"
  local forward_port="${4:?forward_port required}"

  local ssl_forced="false"
  local cert_id=0
  local http2="false"
  local hsts="false"

  if [[ "${NPM_CERT_ID}" -gt 0 ]]; then
    cert_id="${NPM_CERT_ID}"
    ssl_forced="true"
    http2="true"
    hsts="true"
  fi

  local payload
  payload=$(jq -n \
    --arg domain "$domain" \
    --arg host "$forward_host" \
    --argjson port "$forward_port" \
    --argjson cert_id "$cert_id" \
    --argjson ssl_forced "$ssl_forced" \
    --argjson http2 "$http2" \
    --argjson hsts "$hsts" \
    '{
      domain_names: [$domain],
      forward_scheme: "http",
      forward_host: $host,
      forward_port: $port,
      certificate_id: $cert_id,
      ssl_forced: $ssl_forced,
      http2_support: $http2,
      hsts_enabled: $hsts,
      hsts_subdomains: false,
      block_exploits: true,
      caching_enabled: false,
      allow_websocket_upgrade: true,
      access_list_id: 0,
      advanced_config: "",
      meta: {
        letsencrypt_agree: false,
        dns_challenge: false
      },
      locations: []
    }')

  npm_api PUT "nginx/proxy-hosts/${proxy_id}" -d "$payload" > /dev/null || {
    err "Failed to update proxy host ${proxy_id}"
    return 1
  }

  ok "Proxy updated: ${domain} → ${forward_host}:${forward_port} (ID: ${proxy_id})"
  echo "$proxy_id"
}

cmd_delete() {
  local domain="${1:?Usage: npm-proxy.sh delete <domain>}"

  info "Deleting proxy for: ${domain}"

  local proxy_id
  proxy_id=$(cmd_find "$domain" 2>/dev/null || echo "")

  if [[ -z "$proxy_id" || "$proxy_id" == "0" ]]; then
    warn "No proxy found for ${domain}. Nothing to delete."
    return 0
  fi

  npm_api DELETE "nginx/proxy-hosts/${proxy_id}" > /dev/null || {
    err "Failed to delete proxy host ${proxy_id} (${domain})"
    return 1
  }

  ok "Proxy deleted: ${domain} (ID: ${proxy_id})"
}

cmd_find() {
  local domain="${1:?Usage: npm-proxy.sh find <domain>}"

  local hosts
  hosts=$(npm_api GET "nginx/proxy-hosts") || {
    err "Failed to list proxy hosts"
    return 1
  }

  local proxy_id
  proxy_id=$(echo "$hosts" | jq -r \
    --arg domain "$domain" \
    '[.[] | select(.domain_names[] == $domain)] | first | .id // empty')

  if [[ -n "$proxy_id" ]]; then
    info "Found proxy for ${domain}: ID ${proxy_id}"
    echo "$proxy_id"
  else
    return 1
  fi
}

cmd_list() {
  info "Listing all proxy hosts..."

  local hosts
  hosts=$(npm_api GET "nginx/proxy-hosts") || {
    err "Failed to list proxy hosts"
    return 1
  }

  echo "$hosts" | jq -r '.[] | "\(.id)\t\(.domain_names | join(","))\t\(.forward_scheme)://\(.forward_host):\(.forward_port)\t\(if .enabled == 1 then "enabled" else "disabled" end)"' \
    | column -t -s $'\t' -N "ID,DOMAINS,FORWARD,STATUS" 2>/dev/null \
    || echo "$hosts" | jq -r '.[] | "ID=\(.id) \(.domain_names | join(",")) → \(.forward_scheme)://\(.forward_host):\(.forward_port)"'
}

cmd_health() {
  info "Checking NPM API at ${NPM_API_URL}..."

  local status
  status=$(curl -sf -o /dev/null -w "%{http_code}" "${NPM_API_URL}/api/" 2>/dev/null || echo "000")

  if [[ "$status" == "401" || "$status" == "200" ]]; then
    ok "NPM API reachable (HTTP ${status})"

    # Try to authenticate
    local token
    token=$(get_token 2>/dev/null) && {
      ok "Authentication successful"
      # Count existing hosts
      local count
      count=$(npm_api GET "nginx/proxy-hosts" 2>/dev/null | jq 'length' 2>/dev/null || echo "?")
      info "Active proxy hosts: ${count}"
    } || {
      warn "Authentication failed — check credentials"
    }
  else
    err "NPM API not reachable at ${NPM_API_URL} (HTTP ${status})"
    return 1
  fi
}

# ---- Main ----
COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
  create)  cmd_create "$@" ;;
  update)  cmd_update "$@" ;;
  delete)  cmd_delete "$@" ;;
  find)    cmd_find "$@" ;;
  list)    cmd_list ;;
  health)  cmd_health ;;
  help|-h|--help)
    echo "Usage: $(basename "$0") <command> [args]"
    echo ""
    echo "Commands:"
    echo "  create <domain> <forward_host> <forward_port>  Create/update proxy host"
    echo "  delete <domain>                                Delete proxy host"
    echo "  find   <domain>                                Find proxy host ID"
    echo "  list                                           List all proxy hosts"
    echo "  health                                         Check NPM API connectivity"
    echo ""
    echo "Environment variables:"
    echo "  NPM_API_URL       NPM API base URL (e.g. http://192.168.200.10:81)"
    echo "  NPM_API_EMAIL     NPM admin email"
    echo "  NPM_API_PASSWORD  NPM admin password"
    echo "  NPM_CERT_ID       (Optional) Wildcard certificate ID for SSL"
    ;;
  *)
    err "Unknown command: ${COMMAND}"
    echo "Run with 'help' for usage."
    exit 1
    ;;
esac
