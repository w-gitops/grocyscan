#!/bin/bash
# GrocyScan Deploy Script
# Syncs code to remote server and restarts the service
#
# Usage: ./scripts/deploy.sh

set -e

REMOTE_HOST="root@192.168.200.37"
REMOTE_PATH="/opt/grocyscan"

echo -e "\033[36mDeploying GrocyScan to $REMOTE_HOST...\033[0m"

# Sync with rsync (faster for incremental changes)
echo -e "\033[33mSyncing code...\033[0m"
rsync -avz --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '.env' \
    --exclude 'tests' \
    --exclude '.cursor' \
    --exclude '.ralph' \
    --exclude 'prd' \
    --exclude 'docker' \
    ./ "${REMOTE_HOST}:${REMOTE_PATH}/"

# Install any new dependencies
echo -e "\033[33mChecking dependencies...\033[0m"
ssh $REMOTE_HOST "cd $REMOTE_PATH && ./venv/bin/pip install -q -r requirements.txt"

# Run migrations if needed
echo -e "\033[33mRunning migrations...\033[0m"
ssh $REMOTE_HOST "cd $REMOTE_PATH && ./venv/bin/alembic upgrade head"

# Restart service
echo -e "\033[33mRestarting service...\033[0m"
ssh $REMOTE_HOST "systemctl restart grocyscan"

# Wait and check status
sleep 2
echo -e "\033[33mChecking status...\033[0m"
ssh $REMOTE_HOST "systemctl status grocyscan --no-pager | head -15"

# Test health
echo ""
echo -e "\033[33mTesting health endpoint...\033[0m"
ssh $REMOTE_HOST "curl -s http://localhost:3334/api/health"

echo ""
echo -e "\033[32mDeploy complete!\033[0m"
