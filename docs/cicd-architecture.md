# GrocyScan / HomeBot CI/CD Architecture

## Overview

This document describes the CI/CD pipeline architecture for GrocyScan (HomeBot). The design
supports automated testing, branch preview deployments, and production deployment — all
accessible to both **Cursor Desktop** and **Cursor Cloud** agents.

```
                         ┌─────────────────┐
                         │  Developer /     │
                         │  Cursor Agent    │
                         └───────┬─────────┘
                                 │ git push
                                 ▼
                       ┌─────────────────────┐
                       │      GitHub         │
                       │  (w-gitops/grocy...) │
                       └───────┬─────────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
          ┌────────────┐ ┌──────────┐ ┌──────────────┐
          │  CI Tests  │ │  Docker  │ │   Preview    │
          │ (GH-hosted)│ │  Build   │ │   Deploy     │
          │ pytest +   │ │  (GHCR)  │ │ (self-hosted │
          │ Playwright │ │          │ │   runner)    │
          └────────────┘ └──────────┘ └──────┬───────┘
                                             │
                                             ▼
                               ┌─────────────────────────┐
                               │   Proxmox VE Cluster    │
                               │                         │
                               │  ┌─────────────────┐    │
                               │  │  Runner VM       │    │
                               │  │  (GH Actions     │    │
                               │  │   self-hosted)   │    │
                               │  └────────┬────────┘    │
                               │           │              │
                               │  ┌────────▼────────┐    │
                               │  │  Preview Envs   │    │
                               │  │  (Docker stacks │    │
                               │  │   per branch)   │    │
                               │  └─────────────────┘    │
                               │                         │
                               │  ┌─────────────────┐    │
                               │  │  Production     │    │
                               │  │  (192.168.200.37)│    │
                               │  └─────────────────┘    │
                               └─────────────────────────┘
```

## Components

### 1. GitHub-Hosted CI (Tests + Lint)

Runs on every PR against `dev` or `main`:
- **Pytest** — Python unit/integration tests with Postgres + Redis services
- **Playwright** — End-to-end UI tests against a full stack

These run on `ubuntu-latest` (free GitHub-hosted runners) and don't require
any self-hosted infrastructure.

### 2. Docker Image Build (GHCR)

Triggers on:
- **Push to any branch** — Tagged as `ghcr.io/w-gitops/grocyscan:<branch-slug>`
- **Push to main** — Also tagged as `ghcr.io/w-gitops/grocyscan:latest`
- **PR events** — Build but don't push (validation only)

The multi-stage Dockerfile builds both the Vue frontend and Python backend into
a single image. This means the Docker image is self-contained and production-ready.

### 3. Preview Deployments (Self-Hosted Runner on Proxmox)

When a PR is opened or updated:
1. GitHub Actions triggers a job on the self-hosted runner
2. The runner pulls the branch-tagged Docker image from GHCR
3. A full stack (app + Postgres + Redis) is spun up with unique ports
4. The preview URL is posted as a PR comment
5. When the PR is closed, the stack is torn down

**Port allocation**: `API = 10000 + PR_NUMBER`, `Postgres = 15000 + PR_NUMBER`

### 4. Production Deployment

When code is merged to `main`:
1. Docker image is built and pushed to GHCR as `:latest`
2. A deployment job SSHs into the production server (`192.168.200.37`)
3. Pulls the latest image and restarts the stack
4. Runs health checks to verify deployment
5. Posts deployment status

### 5. Cursor Agent Integration

**Cursor Cloud agents** (no local network access):
- Push code to a branch → CI runs automatically
- Use `gh run list` / `gh run view --log` to check CI status
- Preview URLs appear as PR comments — agents can reference these
- The `scripts/cursor-deploy.sh` script works via GitHub Actions dispatch

**Cursor Desktop agents** (local network access):
- Same GitHub Actions flow as above
- Can also SSH directly to preview/production servers
- Can run `scripts/deploy.sh` for direct deployment
- Can run `scripts/cursor-deploy.sh` which auto-detects the environment

---

## Infrastructure Setup

### Prerequisites

1. **Proxmox VE 9 cluster** with at least one node
2. **GitHub repository** at `w-gitops/grocyscan`
3. **GitHub Personal Access Token** with `repo` and `packages` scopes

### Step 1: Create the Runner VM on Proxmox

Use the bootstrap script to create and configure a VM:

```bash
# On your Proxmox host or a machine with Proxmox API access:
bash infrastructure/setup-runner.sh
```

This creates:
- An Ubuntu 24.04 LXC container (or VM) on Proxmox
- Docker + Docker Compose installed
- GitHub Actions runner registered
- Nginx reverse proxy for preview URLs (optional)

### Step 2: Register the Self-Hosted Runner

After the VM is created, SSH in and register the GitHub Actions runner:

```bash
ssh root@<RUNNER_IP>
cd /opt/actions-runner
./config.sh --url https://github.com/w-gitops/grocyscan \
  --token <RUNNER_TOKEN> \
  --labels self-hosted,linux,x64,proxmox,preview \
  --name grocyscan-runner \
  --work _work
```

Get the runner token from:
**GitHub → Settings → Actions → Runners → New self-hosted runner**

### Step 3: Configure GitHub Secrets

Add these secrets in your GitHub repository settings
(**Settings → Secrets and variables → Actions**):

| Secret | Description | Example |
|--------|-------------|---------|
| `DEPLOY_SSH_KEY` | SSH private key for production server | (ed25519 key) |
| `DEPLOY_HOST` | Production server IP | `192.168.200.37` |
| `DEPLOY_USER` | SSH user on production server | `root` |
| `PREVIEW_HOST` | Runner/preview server IP | (runner VM IP) |
| `GHCR_TOKEN` | GitHub PAT for pulling images | (PAT with packages scope) |

For **Cursor Cloud Agents**, also add these in the Cursor Dashboard
(**Cloud Agents → Secrets**):

| Secret | Description |
|--------|-------------|
| `DEPLOY_SSH_KEY` | Same SSH key (if agents need direct deploy) |
| `GH_TOKEN` | GitHub token for `gh` CLI operations |

### Step 4: Configure Production Server for Docker Deployment

On `192.168.200.37`:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Login to GHCR
echo "<GITHUB_PAT>" | docker login ghcr.io -u <USERNAME> --password-stdin

# Create deployment directory
mkdir -p /opt/grocyscan-docker
cp docker/docker-compose.prod.yml /opt/grocyscan-docker/docker-compose.yml

# Create .env with production values
cp .env.example /opt/grocyscan-docker/.env
# Edit .env with production values...
```

---

## Workflow Reference

### Branch Workflow

```
feature branch ──push──► CI Tests (GH-hosted)
                    ├──► Docker Build → GHCR (branch tag)
                    └──► Preview Deploy (self-hosted runner)
                              │
                              ▼
                    Preview URL posted as PR comment
                              │
                         ┌────┴────┐
                         │ Review  │
                         │ & Test  │
                         └────┬────┘
                              │
                    PR merged to main
                              │
                    ├──► Docker Build → GHCR (:latest)
                    └──► Production Deploy (SSH)
                              │
                    Preview env cleaned up
```

### Available GitHub Actions Workflows

| Workflow | Trigger | Runner | Purpose |
|----------|---------|--------|---------|
| `tests.yml` | PR to dev/main | GitHub-hosted | Pytest |
| `ui-tests.yml` | PR to dev/main | GitHub-hosted | Playwright E2E |
| `docker-build.yml` | Push to any branch | GitHub-hosted | Build & push image |
| `preview-deploy.yml` | PR opened/updated | Self-hosted (Proxmox) | Deploy preview env |
| `preview-cleanup.yml` | PR closed | Self-hosted (Proxmox) | Tear down preview env |
| `deploy-production.yml` | Push to main | GitHub-hosted + SSH | Deploy to production |

### Manual Triggers

All workflows support `workflow_dispatch` for manual runs:

```bash
# Trigger preview deploy manually
gh workflow run preview-deploy.yml -f pr_number=42

# Trigger production deploy manually
gh workflow run deploy-production.yml

# Check workflow status
gh run list --workflow=deploy-production.yml
gh run view <RUN_ID> --log
```

---

## Port Allocation Scheme

| Environment | API Port | Description |
|-------------|----------|-------------|
| Production | 3334 | `192.168.200.37:3334` |
| Dev (local) | 3334/3335 | Backend/frontend dev servers |
| Preview PR #N | 10000+N | `<RUNNER_IP>:1000N` |

Preview URLs follow the pattern: `http://<RUNNER_IP>:<10000+PR_NUMBER>`

---

## Security Notes

1. **SSH keys**: Use dedicated deploy keys (ed25519), not personal keys
2. **GHCR tokens**: Use fine-grained PATs with minimal scope (packages:read)
3. **Preview isolation**: Each preview runs in its own Docker network
4. **Secrets in CI**: All sensitive values are in GitHub Secrets, never in code
5. **Runner security**: The self-hosted runner should be on a private network
6. **Preview cleanup**: Automatic teardown on PR close prevents resource leaks
