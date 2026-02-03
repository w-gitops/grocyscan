# GrocyScan Deploy Script
# Syncs code to remote server and restarts the service
#
# Usage: .\scripts\deploy.ps1

$REMOTE_HOST = "root@192.168.200.37"
$REMOTE_PATH = "/opt/grocyscan"

Write-Host "Deploying GrocyScan to $REMOTE_HOST..." -ForegroundColor Cyan

# Sync app code (excluding venv, __pycache__, etc.)
Write-Host "Syncing code..." -ForegroundColor Yellow
scp -r app/* "${REMOTE_HOST}:${REMOTE_PATH}/app/"

# Sync migrations if changed
Write-Host "Syncing migrations..." -ForegroundColor Yellow
scp -r migrations/* "${REMOTE_HOST}:${REMOTE_PATH}/migrations/"

# Sync requirements if changed
scp requirements.txt "${REMOTE_HOST}:${REMOTE_PATH}/"

# Restart service
Write-Host "Restarting service..." -ForegroundColor Yellow
ssh $REMOTE_HOST "systemctl restart grocyscan"

# Check status
Write-Host "Checking status..." -ForegroundColor Yellow
ssh $REMOTE_HOST "systemctl status grocyscan --no-pager | head -15"

# Test health
Write-Host ""
Write-Host "Testing health endpoint..." -ForegroundColor Yellow
ssh $REMOTE_HOST "curl -s http://localhost:3334/api/health"

Write-Host ""
Write-Host "Deploy complete!" -ForegroundColor Green
