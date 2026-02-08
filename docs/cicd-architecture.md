# GrocyScan / HomeBot CI/CD Architecture

## Quickstart — Bootstrap from Zero

Everything below assumes you have a Proxmox 9 VE host and a GitHub repo.
Run these commands to go from nothing to working CI/CD runners.

```bash
# ─── ON YOUR PROXMOX HOST ───────────────────────────────────
# 1. Download the LXC provisioner
curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/create-lxc.sh
chmod +x create-lxc.sh

# 2. Create two LXCs (interactive — prompts for everything):
bash create-lxc.sh                   # or pass flags: --profile ci --ctid 11250 --ip ...

# 3. Or create both non-interactively:
bash create-lxc.sh --profile ci     --ctid 11250 --ip 192.168.200.50/24 --gw 192.168.200.2
bash create-lxc.sh --profile deploy --ctid 11251 --ip 192.168.200.51/24 --gw 192.168.200.2

# ─── GET A RUNNER TOKEN (from any machine with gh CLI) ──────
gh api -X POST repos/w-gitops/grocyscan/actions/runners/registration-token --jq .token

# ─── INSIDE EACH LXC (SSH in, then run) ─────────────────────
# Interactive mode (prompts for token, profile, name):
curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/setup-runner.sh
bash setup-runner.sh

# Or non-interactive:
bash setup-runner.sh \
  --github-url https://github.com/w-gitops/grocyscan \
  --runner-token <TOKEN> \
  --runner-name grocyscan-ci \
  --profile ci

# ─── GITHUB SECRETS (repo Settings > Secrets > Actions) ─────
# DEPLOY_SSH_KEY      — ed25519 private key for production server
# DEPLOY_HOST         — 192.168.200.37
# NPM_API_URL         — http://<npm-host>:81
# NPM_API_EMAIL       — admin email for NPM
# NPM_API_PASSWORD    — admin password for NPM
# NPM_CERT_ID         — wildcard cert ID in NPM (optional)

# ─── CREATE DEV BRANCH (once, from main) ────────────────────
git checkout main && git checkout -b dev && git push -u origin dev
```

That's it. Push a PR targeting `dev` and the full pipeline runs.

---

## Overview

Hybrid CI/CD pipeline: **Docker for ephemeral environments** (previews, staging),
**bare install for production** (rsync + systemd). Self-hosted Proxmox runners for
Playwright and deploy jobs. Nginx Proxy Manager provides HTTPS for all environments.

```
                         ┌─────────────────┐
                         │  Developer /     │
                         │  Cursor Agent    │
                         └───────┬─────────┘
                                 │ git push
                                 ▼
                       ┌─────────────────────┐
                       │      GitHub         │
                       └───────┬─────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
     ┌─────────────┐   ┌─────────────┐   ┌──────────────┐
     │  CI Tests   │   │   Docker    │   │   Deploy     │
     │  (pytest +  │   │   Build     │   │  (preview /  │
     │  Playwright)│   │   (GHCR)    │   │  staging /   │
     │             │   │             │   │  production) │
     └──────┬──────┘   └─────────────┘   └──────┬───────┘
            │                                     │
            │  self-hosted                        │  self-hosted (Docker)
            │  (bare install)                     │  + SSH (bare install)
            ▼                                     ▼
     ┌─────────────────────────────────────────────────┐
     │              Proxmox VE Cluster                 │
     │                                                 │
     │  ┌───────────────┐    ┌───────────────────┐     │
     │  │  CI Runner    │    │  Deploy Runner    │     │
     │  │  proxmox-ci   │    │  proxmox,preview  │     │
     │  │               │    │                   │     │
     │  │  Python 3.12  │    │  Docker           │     │
     │  │  Node 20      │    │  Docker Compose   │     │
     │  │  Playwright   │    │  npm-proxy.sh     │     │
     │  │  (bare metal) │    │                   │     │
     │  └───────────────┘    └────────┬──────────┘     │
     │                                │                 │
     │         ┌──────────────────────┤                 │
     │         ▼                      ▼                 │
     │  ┌─────────────┐    ┌──────────────────┐        │
     │  │  Previews   │    │  Staging (dev)   │        │
     │  │  Docker per │    │  Docker :dev     │        │
     │  │  PR branch  │    │  port 9000       │        │
     │  └─────────────┘    └──────────────────┘        │
     │                                                 │
     │  ┌──────────────────────────────────┐           │
     │  │  Nginx Proxy Manager             │           │
     │  │  *.preview.grocyscan.ssiops.com  │           │
     │  │  dev.grocyscan.ssiops.com        │           │
     │  │  (wildcard cert, auto-managed)   │           │
     │  └──────────────────────────────────┘           │
     │                                                 │
     │  ┌──────────────────────────────────┐           │
     │  │  Production (192.168.200.37)     │           │
     │  │  Bare install: rsync + systemd   │           │
     │  │  grocyscan.ssiops.com            │           │
     │  └──────────────────────────────────┘           │
     └─────────────────────────────────────────────────┘
```

## Branching Model

```
feature/* ──PR──► dev ──PR──► main
                   │           │
                   ▼           ▼
               Staging      Production
          (Docker, :dev)   (bare install)
```

| Branch | Purpose | Deploy Target | Method |
|--------|---------|---------------|--------|
| `feature/*` | Development work | Preview per PR | Docker on Proxmox |
| `dev` | Integration / staging | Persistent staging | Docker on Proxmox |
| `main` | Production release | Production server | Bare install (rsync + systemd) |

**Rules:**
- Feature branches PR into `dev`, never directly to `main`
- `dev` merges to `main` when ready for production release
- `main` is always deployable

## Hybrid Deploy Strategy

| What | Method | Why |
|------|--------|-----|
| **Preview envs** | Docker Compose | Isolation: each PR gets its own stack (app + Postgres + Redis) with ephemeral tmpfs storage. Easy cleanup. |
| **Staging (dev)** | Docker Compose | Same as preview but persistent. Runs `:dev` image on fixed port 9000. |
| **Production** | Bare install (rsync + systemd) | Fast iteration, no Docker overhead, direct filesystem access, journalctl logs, simple debugging. |
| **CI tests** | Bare install on runner | No Docker overhead for Python/Node. Playwright runs natively with pre-installed browsers. Fast pip/npm cache. |

## Self-Hosted Runners (Proxmox LXCs)

Runners are Debian 13 (Trixie) LXC containers on Proxmox. LXCs are preferred
over VMs for near-native performance, fast boot, and low resource overhead.

### LXC Specifications

| LXC | Profile | CPU | RAM | Disk | Proxmox Features | Purpose |
|-----|---------|-----|-----|------|-------------------|---------|
| `grocyscan-ci` | `ci` | 2 vCPU | 4 GB | 30 GB | (default) | pytest + Playwright |
| `grocyscan-deploy` | `deploy` | 2 vCPU | 4 GB | 50 GB | **nesting=1, keyctl=1** | Docker preview/staging |
| `grocyscan-runner` | `all` | 4 vCPU | 6 GB | 50 GB | **nesting=1, keyctl=1** | Combined (single LXC) |

**Important**: The `deploy` and `all` profiles require Docker-in-LXC support.
In Proxmox, the LXC must have `nesting=1` and `keyctl=1` enabled:
```bash
pct set <CTID> --features nesting=1,keyctl=1
```

### CI Runner (`proxmox-ci`)

Runs pytest and Playwright. Bare-metal Python, Node, and Chromium — no Docker
overhead during test execution. Python/Node are Debian-native packages.

```
Labels: self-hosted, linux, x64, proxmox-ci
Installs: Python 3 (Debian native), Node 20, Playwright Chromium system deps
Used by: tests.yml, ui-tests.yml
```

### Deploy Runner (`proxmox`, `preview`)

Runs preview/staging Docker Compose stacks and manages NPM proxy entries.

```
Labels: self-hosted, linux, x64, proxmox, preview
Installs: Docker CE, Docker Compose plugin
Used by: preview-deploy.yml, preview-cleanup.yml, deploy-dev.yml
```

### Setup

Both scripts live in the repo at `infrastructure/` but need to run on
machines that don't have it checked out. Curl them from GitHub raw.

```
https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/create-lxc.sh
https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/setup-runner.sh
```

#### Step 1: Create LXCs (run on the Proxmox host)

```bash
curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/create-lxc.sh
chmod +x create-lxc.sh

# Interactive (prompts for everything):
bash create-lxc.sh

# Or with flags:
bash create-lxc.sh --profile ci     --ctid 11250 --ip 192.168.200.50/24 --gw 192.168.200.2
bash create-lxc.sh --profile deploy --ctid 11251 --ip 192.168.200.51/24 --gw 192.168.200.2
```

#### Step 2: Install the runner (SSH into each LXC)

```bash
# Get a runner token (from any machine with gh CLI):
gh api -X POST repos/w-gitops/grocyscan/actions/runners/registration-token --jq .token

# --- CI LXC ---
ssh root@192.168.200.50
curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/setup-runner.sh

# Interactive (prompts for token, profile, name):
bash setup-runner.sh

# Or with flags:
bash setup-runner.sh \
  --github-url https://github.com/w-gitops/grocyscan \
  --runner-token <TOKEN> \
  --runner-name grocyscan-ci \
  --profile ci

# --- Deploy LXC ---
ssh root@192.168.200.51
curl -sLO https://raw.githubusercontent.com/w-gitops/grocyscan/main/infrastructure/setup-runner.sh
bash setup-runner.sh   # interactive, or pass --flags
```

#### Step 3: Login to GHCR (deploy LXC only)

```bash
ssh root@192.168.200.51
su - runner
echo $GITHUB_PAT | docker login ghcr.io -u <username> --password-stdin
```

### Why LXCs, Not VMs

- **Performance**: Near-native CPU/IO — no hypervisor overhead
- **Resources**: ~100MB base RAM vs ~500MB for a VM with kernel
- **Boot time**: Seconds vs minutes
- **Playwright**: All browser dependencies are userspace libraries, no kernel modules needed
- **Docker-in-LXC**: Works perfectly on Proxmox 9 with nesting+keyctl enabled
- **Swarm**: Not used — preview stacks are single-node Compose projects, Swarm adds
  complexity without benefit here

## Nginx Proxy Manager Integration

Each preview/staging deployment gets a proper HTTPS URL via the NPM API.

### How It Works

1. Preview deploys call `scripts/npm-proxy.sh create` to register a proxy host
2. NPM forwards `pr-N.preview.grocyscan.ssiops.com` → `runner-ip:10000+N`
3. On PR close, `scripts/npm-proxy.sh delete` removes the proxy
4. Staging has a permanent proxy: `dev.grocyscan.ssiops.com` → `runner-ip:9000`

### Prerequisites

1. **NPM instance** running and accessible from the runners (e.g. Docker container on Proxmox)
2. **Wildcard DNS**: `*.preview.grocyscan.ssiops.com` → runner IP, `dev.grocyscan.ssiops.com` → runner IP
3. **Wildcard SSL certificate** configured in NPM (recommended: DNS challenge via Cloudflare/etc.)
4. **GitHub Secrets**:

| Secret | Description | Example |
|--------|-------------|---------|
| `NPM_API_URL` | NPM API base URL | `http://192.168.200.10:81` |
| `NPM_API_EMAIL` | NPM admin email | `admin@example.com` |
| `NPM_API_PASSWORD` | NPM admin password | (password) |
| `NPM_CERT_ID` | Wildcard certificate ID in NPM | `5` (from NPM SSL Certificates page) |

### Manual Usage

```bash
export NPM_API_URL=http://192.168.200.10:81
export NPM_API_EMAIL=admin@example.com
export NPM_API_PASSWORD=changeme

# List all proxy hosts
./scripts/npm-proxy.sh list

# Create a proxy
./scripts/npm-proxy.sh create pr-42.preview.grocyscan.ssiops.com 192.168.200.50 10042

# Delete a proxy
./scripts/npm-proxy.sh delete pr-42.preview.grocyscan.ssiops.com

# Check NPM health
./scripts/npm-proxy.sh health
```

## Workflows Reference

| Workflow | Trigger | Runner | Purpose |
|----------|---------|--------|---------|
| `tests.yml` | PR to dev/main | **Self-hosted** (proxmox-ci) | Pytest with Postgres + Redis |
| `ui-tests.yml` | PR to dev/main | **Self-hosted** (proxmox-ci) | Playwright E2E (bare install) |
| `docker-build.yml` | Push to dev/main | GitHub-hosted | Build & push GHCR image |
| `preview-deploy.yml` | PR to dev/main | Self-hosted (proxmox) | Docker preview + NPM HTTPS proxy |
| `preview-cleanup.yml` | PR closed | Self-hosted (proxmox) | Tear down preview + delete proxy |
| `deploy-dev.yml` | Push to dev | Self-hosted (proxmox) | Deploy staging Docker stack |
| `deploy-production.yml` | Push to main | GitHub-hosted (SSH) | Bare install rsync + systemd |

All workflows support `workflow_dispatch` for manual runs.

## Environments & URLs

| Environment | URL | Method | Credentials |
|-------------|-----|--------|-------------|
| Production | `https://grocyscan.ssiops.com` | Bare install on 192.168.200.37 | (production creds) |
| Staging | `https://dev.grocyscan.ssiops.com` | Docker `:dev` on Proxmox runner | `admin` / `test` |
| Preview PR #N | `https://pr-N.preview.grocyscan.ssiops.com` | Docker `:pr-N` on Proxmox runner | `admin` / `test` |
| Local dev | `http://localhost:3334` / `:3335` | uvicorn + vite dev | (local creds) |

## Port Allocation

| Environment | API Port | Postgres Port |
|-------------|----------|---------------|
| Production | 3334 | 5432 (native) |
| Staging (dev) | 9000 | 9001 |
| Preview PR #N | 10000+N | 15000+N |
| Local dev | 3334/3335 | 5432 |

## GitHub Secrets Required

| Secret | Used By | Description |
|--------|---------|-------------|
| `DEPLOY_SSH_KEY` | deploy-production | SSH private key (ed25519) for production server |
| `DEPLOY_HOST` | deploy-production | Production server IP (default: 192.168.200.37) |
| `DEPLOY_USER` | deploy-production | SSH user (default: root) |
| `NPM_API_URL` | preview-deploy, preview-cleanup, deploy-dev | NPM API base URL |
| `NPM_API_EMAIL` | preview-deploy, preview-cleanup, deploy-dev | NPM admin email |
| `NPM_API_PASSWORD` | preview-deploy, preview-cleanup, deploy-dev | NPM admin password |
| `NPM_CERT_ID` | preview-deploy, deploy-dev | Wildcard certificate ID in NPM |

For **Cursor Cloud Agents**, add in Cursor Dashboard (Cloud Agents > Secrets):

| Secret | Description |
|--------|-------------|
| `GH_TOKEN` | GitHub token (already provided by Cursor) |

## Security Notes

1. **SSH keys**: Dedicated ed25519 deploy keys, not personal keys
2. **NPM credentials**: Stored as GitHub Secrets, never in code
3. **Preview isolation**: Each preview runs in its own Docker network with tmpfs storage
4. **Preview cleanup**: Automatic teardown on PR close prevents resource/proxy leaks
5. **Runner security**: Self-hosted runners on private Proxmox network, not exposed to internet
6. **GHCR tokens**: Use fine-grained PATs with minimal scope
