# Self-Hosted Runner Setup for GrocyScan

This document describes how to set up a self-hosted GitHub Actions runner for running Playwright E2E tests.

## Why Self-Hosted?

- **Faster execution**: No queue time, dedicated resources
- **Cost savings**: No GitHub Actions minutes consumed
- **Network access**: Can access internal services (Grocy, databases)
- **Persistent browser cache**: Faster Playwright browser installation

---

## Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 20 GB | 50+ GB SSD |
| Network | Stable connection | Low latency to GitHub |

---

## Software Requirements

### Operating System

- Ubuntu 22.04 LTS (recommended)
- Debian 11+
- Other Linux distributions with systemd

### Required Software

```bash
# System packages
sudo apt-get update
sudo apt-get install -y \
  curl \
  git \
  wget \
  ca-certificates \
  gnupg \
  lsb-release \
  build-essential

# Docker (for database services)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Playwright browser dependencies
npx playwright install-deps
```

### Playwright Browsers

```bash
# Install Playwright browsers globally
npx playwright install

# Or install to a specific location
PLAYWRIGHT_BROWSERS_PATH=/opt/playwright npx playwright install
```

---

## Runner Installation

### 1. Create Runner User

```bash
sudo useradd -m -s /bin/bash github-runner
sudo usermod -aG docker github-runner
```

### 2. Download Runner

```bash
# Switch to runner user
sudo -i -u github-runner

# Create directory
mkdir actions-runner && cd actions-runner

# Download latest runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf actions-runner-linux-x64-2.311.0.tar.gz
```

### 3. Configure Runner

Get the registration token from:
`https://github.com/[owner]/[repo]/settings/actions/runners/new`

```bash
./config.sh --url https://github.com/[owner]/grocyscan \
  --token YOUR_TOKEN \
  --name grocyscan-runner \
  --labels self-hosted,linux,x64,playwright \
  --work _work
```

### 4. Install as Service

```bash
sudo ./svc.sh install github-runner
sudo ./svc.sh start
```

---

## Runner Labels

Configure these labels for the runner:

| Label | Description |
|-------|-------------|
| `self-hosted` | Required for self-hosted runners |
| `linux` | Operating system |
| `x64` | Architecture |
| `playwright` | Has Playwright browsers installed |
| `grocyscan` | Project-specific (optional) |

---

## Environment Setup

### Environment Variables

Create `/home/github-runner/.env`:

```bash
# Playwright browser path (optional, for cached browsers)
PLAYWRIGHT_BROWSERS_PATH=/opt/playwright

# Node.js memory limit
NODE_OPTIONS=--max-old-space-size=4096

# Python
PYTHON_PATH=/usr/bin/python3.12
```

### Browser Cache

To speed up Playwright browser installation:

```bash
# Create shared browser directory
sudo mkdir -p /opt/playwright
sudo chown github-runner:github-runner /opt/playwright

# Pre-install browsers
PLAYWRIGHT_BROWSERS_PATH=/opt/playwright npx playwright install --with-deps
```

---

## Workflow Configuration

### Using Self-Hosted Runner

Update `.github/workflows/ui-tests.yml`:

```yaml
jobs:
  ui:
    name: Playwright UI
    # Use self-hosted runner with playwright label
    runs-on: [self-hosted, linux, x64, playwright]
    
    # Or fall back to GitHub-hosted if self-hosted unavailable
    # runs-on: ${{ github.event.inputs.runner || 'ubuntu-latest' }}
```

### Conditional Runner Selection

```yaml
on:
  workflow_dispatch:
    inputs:
      runner:
        description: 'Runner to use'
        required: false
        default: 'ubuntu-latest'
        type: choice
        options:
          - ubuntu-latest
          - self-hosted

jobs:
  ui:
    runs-on: ${{ github.event.inputs.runner || 'ubuntu-latest' }}
```

### Browser Caching

```yaml
- name: Cache Playwright browsers
  uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: playwright-${{ runner.os }}-${{ hashFiles('frontend/package-lock.json') }}
    restore-keys: |
      playwright-${{ runner.os }}-

- name: Install Playwright browsers
  if: steps.playwright-cache.outputs.cache-hit != 'true'
  run: npx playwright install --with-deps
  working-directory: frontend
```

---

## Security Considerations

### Network Isolation

1. **Firewall**: Only allow outbound connections to:
   - `github.com` (runner communication)
   - `registry.npmjs.org` (npm packages)
   - `pypi.org` (Python packages)
   - Internal services (Grocy, database)

2. **No public access**: Runner should not be accessible from internet

### Runner Permissions

1. **Least privilege**: Runner user should only have required permissions
2. **Docker isolation**: Tests run in isolated containers
3. **Secret management**: Use GitHub Secrets, not local files

### Updates

```bash
# Keep runner updated
cd /home/github-runner/actions-runner
./svc.sh stop
./config.sh remove --token YOUR_TOKEN
# Download and configure new version
./svc.sh install
./svc.sh start
```

---

## Monitoring

### Runner Status

```bash
# Check service status
sudo systemctl status actions.runner.*.service

# View logs
journalctl -u actions.runner.*.service -f
```

### Health Checks

Create a simple health check script:

```bash
#!/bin/bash
# /home/github-runner/health-check.sh

# Check runner service
systemctl is-active --quiet actions.runner.*.service || exit 1

# Check Docker
docker info > /dev/null 2>&1 || exit 1

# Check Playwright browsers
PLAYWRIGHT_BROWSERS_PATH=/opt/playwright npx playwright --version > /dev/null 2>&1 || exit 1

echo "OK"
```

---

## Troubleshooting

### Runner Not Picking Up Jobs

1. Check runner status: `sudo systemctl status actions.runner.*.service`
2. Check labels match workflow `runs-on`
3. Check GitHub Actions settings for runner visibility

### Playwright Timeouts

1. Increase timeouts in `playwright.config.js`
2. Check system resources: `htop`, `free -m`
3. Check network connectivity

### Docker Permission Issues

```bash
# Add runner to docker group
sudo usermod -aG docker github-runner

# Restart runner service
sudo systemctl restart actions.runner.*.service
```

### Browser Installation Fails

```bash
# Install all dependencies
sudo npx playwright install-deps

# Install browsers with dependencies
npx playwright install --with-deps chromium
```

---

## Migration Checklist

When migrating from GitHub-hosted to self-hosted:

- [ ] Set up runner machine with required specs
- [ ] Install all required software
- [ ] Configure runner with correct labels
- [ ] Test runner with manual workflow dispatch
- [ ] Update workflow to use self-hosted runner
- [ ] Monitor first few CI runs
- [ ] Set up alerting for runner failures
- [ ] Document runner maintenance procedures

---

## Resources

- [GitHub Actions Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Playwright CI Guide](https://playwright.dev/docs/ci)
- [Runner Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#hardening-for-self-hosted-runners)
