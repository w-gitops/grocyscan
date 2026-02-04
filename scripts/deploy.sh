#!/bin/bash
# GrocyScan Deploy Script
# Syncs code to remote server and restarts the service
#
# Usage: ./scripts/deploy.sh

set -e

REMOTE_HOST="root@192.168.200.37"
REMOTE_PATH="/opt/grocyscan"
LOCAL_ENV_FILE=".env"

echo -e "\033[36mDeploying GrocyScan to $REMOTE_HOST...\033[0m"

# Build Vue frontend (for /app on server)
if [ -f frontend/package.json ]; then
  echo -e "\033[33mBuilding Vue frontend...\033[0m"
  (cd frontend && NODE_ENV=production npm run build) || { echo "Frontend build failed"; exit 1; }
fi

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
    --exclude 'frontend/node_modules' \
    ./ "${REMOTE_HOST}:${REMOTE_PATH}/"

# Sync environment file (if present)
if [ -f "$LOCAL_ENV_FILE" ]; then
  echo -e "\033[33mSyncing environment file...\033[0m"
  scp "$LOCAL_ENV_FILE" "${REMOTE_HOST}:${REMOTE_PATH}/.env"
else
  echo -e "\033[33mNo .env found; skipping env sync.\033[0m"
fi
# Sync built frontend dist (so server has frontend/dist for /app)
if [ -d frontend/dist ]; then
  echo -e "\033[33mSyncing frontend dist...\033[0m"
  ssh $REMOTE_HOST "mkdir -p ${REMOTE_PATH}/frontend"
  rsync -avz frontend/dist/ "${REMOTE_HOST}:${REMOTE_PATH}/frontend/dist/"
fi

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
