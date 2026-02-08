# GrocyScan / HomeBot CI/CD Architecture

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

## Self-Hosted Runners

Two runner profiles on Proxmox (can be one VM with `--profile all` or separate VMs):

### CI Runner (`proxmox-ci`)

Runs pytest and Playwright. Bare-metal Python, Node, and browsers — no Docker overhead during test execution.

```
Labels: self-hosted, linux, x64, proxmox-ci
Installs: Python 3.12, Node 20, Playwright Chromium system deps
Used by: tests.yml, ui-tests.yml
```

### Deploy Runner (`proxmox`, `preview`)

Runs preview/staging Docker stacks and manages NPM proxy entries.

```
Labels: self-hosted, linux, x64, proxmox, preview
Installs: Docker, Docker Compose
Used by: preview-deploy.yml, preview-cleanup.yml, deploy-dev.yml
```

### Setup

```bash
# Option A: Two separate VMs
bash infrastructure/setup-runner.sh \
  --github-url https://github.com/w-gitops/grocyscan \
  --runner-token <TOKEN> \
  --runner-name grocyscan-ci \
  --profile ci

bash infrastructure/setup-runner.sh \
  --github-url https://github.com/w-gitops/grocyscan \
  --runner-token <TOKEN> \
  --runner-name grocyscan-deploy \
  --profile deploy

# Option B: One VM that does everything
bash infrastructure/setup-runner.sh \
  --github-url https://github.com/w-gitops/grocyscan \
  --runner-token <TOKEN> \
  --runner-name grocyscan-all \
  --profile all
```

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
