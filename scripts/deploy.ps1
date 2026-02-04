# GrocyScan Deploy Script
# Syncs code to remote server and restarts the service
#
# Usage: .\scripts\deploy.ps1

$REMOTE_HOST = "root@192.168.200.37"
$REMOTE_PATH = "/opt/grocyscan"
$LOCAL_ENV_FILE = ".env"

Write-Host "Deploying GrocyScan to $REMOTE_HOST..." -ForegroundColor Cyan

# Build Vue frontend (for /app on server)
if (Test-Path "frontend\package.json") {
    Write-Host "Building Vue frontend..." -ForegroundColor Yellow
    Push-Location frontend
    $env:NODE_ENV = "production"
    npm run build 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Frontend build failed. Run: cd frontend; npm run build" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
}

# Sync app code (excluding venv, __pycache__, etc.)
Write-Host "Syncing code..." -ForegroundColor Yellow
scp -r app/* "${REMOTE_HOST}:${REMOTE_PATH}/app/"

# Sync migrations if changed
Write-Host "Syncing migrations..." -ForegroundColor Yellow
scp -r migrations/* "${REMOTE_HOST}:${REMOTE_PATH}/migrations/"

# Alembic config (required for Settings -> Database migrations)
scp alembic.ini "${REMOTE_HOST}:${REMOTE_PATH}/"

# Sync requirements if changed
scp requirements.txt "${REMOTE_HOST}:${REMOTE_PATH}/"

# Sync environment file (if present)
if (Test-Path $LOCAL_ENV_FILE) {
    Write-Host "Syncing environment file..." -ForegroundColor Yellow
    scp $LOCAL_ENV_FILE "${REMOTE_HOST}:${REMOTE_PATH}/.env"
} else {
    Write-Host "No .env found; skipping env sync." -ForegroundColor DarkYellow
}

# Sync Vue frontend build (served at /app)
if (Test-Path "frontend\dist") {
    Write-Host "Syncing frontend dist..." -ForegroundColor Yellow
    ssh $REMOTE_HOST "mkdir -p ${REMOTE_PATH}/frontend"
    scp -r frontend\dist "${REMOTE_HOST}:${REMOTE_PATH}/frontend/"
}

# Install/update Python dependencies in venv (ensures new deps like python-jose are present)
Write-Host "Installing dependencies on server..." -ForegroundColor Yellow
ssh $REMOTE_HOST "cd $REMOTE_PATH && ./venv/bin/pip install -q -r requirements.txt"

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
