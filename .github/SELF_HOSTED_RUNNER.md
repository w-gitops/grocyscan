# Self-Hosted GitHub Actions Runner Setup

This guide covers setting up a self-hosted GitHub Actions runner for running Playwright UI tests.

## Benefits of Self-Hosted Runner

- **Faster Execution**: Pre-installed browsers, no download wait
- **Consistent Environment**: Control over OS and dependencies
- **Cost Savings**: No minutes usage for private repos
- **Custom Resources**: More CPU/RAM for parallel tests
- **Network Access**: Direct access to internal services

## Hardware Requirements

### Minimum
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space
- Ubuntu 22.04 LTS (recommended)

### Recommended
- 4+ CPU cores
- 8+ GB RAM
- 50+ GB SSD
- Dedicated VM or container

## Software Requirements

- Node.js 18+ (LTS recommended)
- npm 9+
- Git
- Playwright browsers
- Docker (optional, for service containers)

## Installation Steps

### 1. Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install dependencies for Playwright
sudo apt install -y \
  libnss3 \
  libnspr4 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libasound2

# Install Docker (optional)
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker $USER
```

### 2. Create Runner User

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash github-runner
sudo usermod -aG docker github-runner

# Switch to runner user
sudo su - github-runner
```

### 3. Install GitHub Actions Runner

```bash
# Create directory
mkdir actions-runner && cd actions-runner

# Download latest runner (check GitHub for current version)
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Get registration token from GitHub repo settings
# Settings > Actions > Runners > New self-hosted runner

# Configure runner
./config.sh --url https://github.com/YOUR_ORG/YOUR_REPO \
  --token YOUR_REGISTRATION_TOKEN \
  --labels self-hosted,Linux,X64,playwright \
  --name grocyscan-playwright-runner
```

### 4. Configure as Service

```bash
# Install service
sudo ./svc.sh install github-runner

# Start service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

### 5. Pre-install Playwright Browsers

```bash
# As github-runner user
cd /home/github-runner
mkdir playwright-cache
cd playwright-cache

# Initialize npm project
npm init -y
npm install @playwright/test

# Install browsers
npx playwright install --with-deps

# Verify installation
npx playwright --version
```

## Runner Labels

Configure these labels for your runner:

| Label | Purpose |
|-------|---------|
| `self-hosted` | Required for self-hosted runners |
| `Linux` | OS type |
| `X64` | Architecture |
| `playwright` | Custom label for Playwright jobs |

## Workflow Configuration

Update `.github/workflows/ui-tests.yml` to use self-hosted runner:

```yaml
name: UI Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      runner:
        description: 'Runner type'
        required: false
        default: 'ubuntu-latest'
        type: choice
        options:
          - ubuntu-latest
          - self-hosted

jobs:
  test:
    runs-on: ${{ github.event.inputs.runner || 'ubuntu-latest' }}
    
    steps:
      - uses: actions/checkout@v4
      
      # Skip browser install on self-hosted (pre-installed)
      - name: Install Playwright Browsers
        if: ${{ !contains(runner.labels, 'self-hosted') }}
        run: npx playwright install --with-deps
        working-directory: frontend
```

## Environment Variables

Set these in runner environment or workflow:

```bash
# In runner's .bashrc or .profile
export PLAYWRIGHT_BROWSERS_PATH=/home/github-runner/playwright-cache/node_modules/.cache/ms-playwright
export CI=true
```

Or in workflow:

```yaml
env:
  PLAYWRIGHT_BROWSERS_PATH: /home/github-runner/playwright-cache/node_modules/.cache/ms-playwright
```

## Browser Caching Strategy

### Option 1: Pre-installed Browsers (Recommended)

Browsers are installed once on the runner and reused:

```bash
# Update browsers periodically
cd /home/github-runner/playwright-cache
npm update @playwright/test
npx playwright install --with-deps
```

### Option 2: Cached in Workflow

Use GitHub Actions cache:

```yaml
- name: Cache Playwright browsers
  uses: actions/cache@v4
  with:
    path: ~/.cache/ms-playwright
    key: playwright-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
```

## Security Considerations

### Network Isolation
- Use firewall rules to limit outbound access
- Consider running in isolated network segment

### Secrets Management
- Don't store secrets in runner environment
- Use GitHub Secrets exclusively

### Runner Updates
```bash
# Check for updates
cd /home/github-runner/actions-runner
./config.sh --check

# Update runner
sudo ./svc.sh stop
# Download and extract new version
sudo ./svc.sh start
```

### Repository Access
- Configure runner for specific repository only
- Use ephemeral runners for sensitive repos

## Monitoring

### Logs Location
```bash
# Runner logs
/home/github-runner/actions-runner/_diag/

# Service logs
sudo journalctl -u actions.runner.YOUR_ORG-YOUR_REPO.grocyscan-playwright-runner
```

### Health Check Script

```bash
#!/bin/bash
# /home/github-runner/health-check.sh

# Check runner service
if systemctl is-active --quiet actions.runner.*; then
  echo "Runner service: OK"
else
  echo "Runner service: FAILED"
  exit 1
fi

# Check browsers
if /home/github-runner/playwright-cache/node_modules/.bin/playwright --version > /dev/null 2>&1; then
  echo "Playwright: OK"
else
  echo "Playwright: FAILED"
  exit 1
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -lt 90 ]; then
  echo "Disk usage: OK ($DISK_USAGE%)"
else
  echo "Disk usage: WARNING ($DISK_USAGE%)"
fi
```

## Troubleshooting

### Runner Not Picking Up Jobs

1. Check runner is online in GitHub UI
2. Verify labels match workflow
3. Check service status: `sudo ./svc.sh status`
4. Review logs: `journalctl -u actions.runner.*`

### Browser Launch Failures

```bash
# Check dependencies
ldd /path/to/chrome | grep "not found"

# Install missing deps
sudo apt install -y <missing-package>

# Run Playwright debug
DEBUG=pw:browser npx playwright test
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R github-runner:github-runner /home/github-runner

# Fix permissions
chmod -R 755 /home/github-runner/actions-runner
```

### Out of Memory

```bash
# Add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Maintenance Schedule

| Task | Frequency |
|------|-----------|
| Update runner | Monthly |
| Update browsers | With Playwright updates |
| Clear old artifacts | Weekly |
| Review logs | Daily |
| Security patches | As released |

## Backup and Recovery

### Backup Runner Config
```bash
# Backup
tar czf runner-backup.tar.gz \
  /home/github-runner/actions-runner/.credentials \
  /home/github-runner/actions-runner/.runner

# Restore
tar xzf runner-backup.tar.gz -C /
```

### Quick Recovery
1. Provision new server
2. Install dependencies
3. Restore config backup
4. Or re-register runner with new token
