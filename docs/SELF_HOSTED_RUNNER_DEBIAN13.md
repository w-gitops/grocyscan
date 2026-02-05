# Self-hosted GitHub Actions runner (Debian 13 LXC on Proxmox)

This guide sets up a private GitHub Actions runner inside a Debian 13 LXC
container. The runner only needs outbound HTTPS; no inbound ports are required.

## Requirements

- Outbound HTTPS access to:
  - github.com
  - api.github.com
  - actions.githubusercontent.com
  - objects.githubusercontent.com
  - uploads.githubusercontent.com
- Proxmox LXC with outbound internet
- If you want Docker inside the LXC:
  - Enable LXC features: nesting=1, keyctl=1
  - Use a privileged container or ensure your Proxmox config supports Docker
- Recommended resources: 2+ vCPU, 4+ GB RAM, 10+ GB disk

## Steps

1) Create a Debian 13 LXC on Proxmox.

2) Log into the container and get a runner token:
   - GitHub repo -> Settings -> Actions -> Runners -> New self-hosted runner
   - Copy the registration token (valid for a short time).

3) Fetch the setup script (from this repo) and run it:

   - Option A: clone the repo
     - git clone https://github.com/w-gitops/grocyscan.git
     - cd grocyscan
     - sudo REPO_URL="https://github.com/w-gitops/grocyscan" \
       RUNNER_TOKEN="YOUR_TOKEN" \
       RUNNER_LABELS="proxmox-ui" \
       bash scripts/setup_self_hosted_runner_debian13.sh

   - Option B: download the script directly (after it is merged to main)
     - curl -fsSL \
       https://raw.githubusercontent.com/w-gitops/grocyscan/main/scripts/setup_self_hosted_runner_debian13.sh \
       -o setup-runner.sh
     - chmod +x setup-runner.sh
     - sudo REPO_URL="https://github.com/w-gitops/grocyscan" \
       RUNNER_TOKEN="YOUR_TOKEN" \
       RUNNER_LABELS="proxmox-ui" \
       ./setup-runner.sh

4) Confirm the runner shows as online:
   - GitHub repo -> Settings -> Actions -> Runners

## Workflow targeting

The UI tests workflow is configured to use:

  runs-on: [self-hosted, linux, x64, proxmox-ui]

If you change the label in the script, update the workflow label to match.

## Playwright dependencies and sudo

The workflow runs:

  npx playwright install --with-deps

This command uses sudo to install OS packages. The setup script enables
passwordless sudo for the runner user by default. If you do not want that:

- Set ALLOW_PASSWORDLESS_SUDO=false when running the setup script, and
- Preinstall Playwright OS dependencies yourself, or update the workflow
  to use `npx playwright install` (no --with-deps).

## Troubleshooting

- Check runner service:
  - systemctl status "actions.runner.*"
  - journalctl -u "actions.runner.*" -f
- Ensure outbound HTTPS is allowed from the LXC.
