# 9. Installation & Operations

## 9.1 Curl Install Script

```bash
#!/bin/bash
# scripts/install.sh
# GrocyScan Installer for Debian/Ubuntu
# Usage: curl -fsSL https://raw.githubusercontent.com/yourusername/grocyscan/main/scripts/install.sh | bash

set -e

GROCYSCAN_USER="grocyscan"
GROCYSCAN_DIR="/opt/grocyscan"
GROCYSCAN_REPO="https://github.com/yourusername/grocyscan.git"
PYTHON_VERSION="3.11"

echo "╔════════════════════════════════════════╗"
echo "║       GrocyScan Installer v1.0         ║"
echo "╚════════════════════════════════════════╝"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run as root or with sudo"
    exit 1
fi

# Install dependencies
apt-get update -qq
apt-get install -y -qq git curl python${PYTHON_VERSION} python${PYTHON_VERSION}-venv

# Create user
useradd -r -s /bin/bash -m -d /home/$GROCYSCAN_USER $GROCYSCAN_USER 2>/dev/null || true

# Clone repository
if [ -d "$GROCYSCAN_DIR" ]; then
    cd $GROCYSCAN_DIR && git pull origin main
else
    git clone $GROCYSCAN_REPO $GROCYSCAN_DIR
fi

# Setup virtual environment
cd $GROCYSCAN_DIR
python${PYTHON_VERSION} -m venv venv
./venv/bin/pip install -r requirements.txt

# Create .env if not exists
if [ ! -f "$GROCYSCAN_DIR/.env" ]; then
    cp $GROCYSCAN_DIR/.env.example $GROCYSCAN_DIR/.env
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-secret-key-change-me/$SECRET_KEY/" $GROCYSCAN_DIR/.env
fi

# Create systemd service
cat > /etc/systemd/system/grocyscan.service << EOF
[Unit]
Description=GrocyScan Barcode Inventory Manager
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$GROCYSCAN_USER
WorkingDirectory=$GROCYSCAN_DIR
Environment="PATH=$GROCYSCAN_DIR/venv/bin"
EnvironmentFile=$GROCYSCAN_DIR/.env
ExecStart=$GROCYSCAN_DIR/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 3334
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable grocyscan

chown -R $GROCYSCAN_USER:$GROCYSCAN_USER $GROCYSCAN_DIR

echo ""
echo "Installation complete!"
echo "Next steps:"
echo "  1. Edit configuration: nano $GROCYSCAN_DIR/.env"
echo "  2. Run migrations: cd $GROCYSCAN_DIR && ./venv/bin/alembic upgrade head"
echo "  3. Start GrocyScan: systemctl start grocyscan"
```

## 9.2 Management Scripts

### Start Script
```bash
#!/bin/bash
# scripts/start.sh
sudo systemctl start grocyscan
systemctl status grocyscan --no-pager
```

### Stop Script
```bash
#!/bin/bash
# scripts/stop.sh
sudo systemctl stop grocyscan
echo "GrocyScan stopped"
```

### Upgrade Script
```bash
#!/bin/bash
# scripts/upgrade.sh
set -e
GROCYSCAN_DIR="/opt/grocyscan"

echo "Stopping GrocyScan..."
sudo systemctl stop grocyscan

echo "Backing up database..."
source $GROCYSCAN_DIR/.env
pg_dump $DATABASE_URL > /tmp/grocyscan_backup_$(date +%Y%m%d_%H%M%S).sql

echo "Pulling latest code..."
cd $GROCYSCAN_DIR && git pull origin main

echo "Updating dependencies..."
./venv/bin/pip install -r requirements.txt

echo "Running migrations..."
./venv/bin/alembic upgrade head

echo "Starting GrocyScan..."
sudo systemctl start grocyscan
```

## 9.3 Docker Compose Production Stack

```yaml
# docker/docker-compose.yml
version: "3.8"

services:
  grocyscan-app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: grocyscan-app
    env_file:
      - ../.env
    environment:
      - DATABASE_URL=postgresql://grocyscan:${DB_PASSWORD}@postgres:5432/grocyscan
      - REDIS_URL=redis://redis:6379/0
    ports:
      - "${GROCYSCAN_PORT:-3334}:3334"
    volumes:
      - grocyscan-data:/app/data
      - grocyscan-logs:/var/log/grocyscan
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3334/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  postgres:
    image: postgres:17-alpine
    container_name: grocyscan-postgres
    environment:
      - POSTGRES_USER=grocyscan
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=grocyscan
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U grocyscan"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: grocyscan-redis
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  grocyscan-data:
  grocyscan-logs:
  postgres-data:
  redis-data:
```

## 9.4 Dockerfile

```dockerfile
# docker/Dockerfile
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -r -s /bin/bash -m grocyscan

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=grocyscan:grocyscan . .

RUN mkdir -p /var/log/grocyscan /app/data \
    && chown -R grocyscan:grocyscan /var/log/grocyscan /app/data

USER grocyscan

EXPOSE 3334

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3334/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3334"]
```

## 9.5 Quick Start

### Using Docker Compose

```bash
# Clone repository
git clone https://github.com/yourusername/grocyscan.git
cd grocyscan

# Copy and edit environment file
cp .env.example .env
nano .env  # Configure your settings

# Start the stack
cd docker
docker-compose up -d

# Access at http://localhost:3334
```

### Using Bare Metal

```bash
# One-line install
curl -fsSL https://raw.githubusercontent.com/yourusername/grocyscan/main/scripts/install.sh | sudo bash

# Configure
sudo nano /opt/grocyscan/.env

# Start
sudo systemctl start grocyscan

# Access at http://YOUR-IP:3334
```

---

## Navigation

- **Previous:** [Observability](08-observability.md)
- **Next:** [Testing Strategy](10-testing-strategy.md)
- **Back to:** [README](README.md)
