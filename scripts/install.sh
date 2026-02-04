#!/bin/bash
# GrocyScan Installation Script for Debian/Ubuntu

set -e

echo "=== GrocyScan Installation Script ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./install.sh)"
    exit 1
fi

# Configuration
INSTALL_DIR="/opt/grocyscan"
SERVICE_USER="grocyscan"
PYTHON_VERSION="3.11"

echo "Installing system dependencies..."
apt-get update
apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git

echo ""
echo "Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$SERVICE_USER"
fi

echo ""
echo "Creating installation directory..."
mkdir -p "$INSTALL_DIR"
chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

echo ""
echo "Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE USER grocyscan WITH PASSWORD 'changeme';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE grocyscan OWNER grocyscan;" 2>/dev/null || true

echo ""
echo "Creating virtual environment..."
cd "$INSTALL_DIR"
sudo -u "$SERVICE_USER" python${PYTHON_VERSION} -m venv venv

echo ""
echo "Installing Python dependencies..."
sudo -u "$SERVICE_USER" ./venv/bin/pip install --upgrade pip
sudo -u "$SERVICE_USER" ./venv/bin/pip install -r requirements.txt

echo ""
echo "Creating configuration..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    cp .env.example .env
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -base64 32)
    sed -i "s/GROCYSCAN_SECRET_KEY=.*/GROCYSCAN_SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/GROCYSCAN_ENV=.*/GROCYSCAN_ENV=production/" .env
    sed -i "s/DATABASE_URL=.*/DATABASE_URL=postgresql+asyncpg:\/\/grocyscan:changeme@localhost:5432\/grocyscan/" .env
    echo ""
    echo "IMPORTANT: Edit $INSTALL_DIR/.env to configure:"
    echo "  - DATABASE_URL (change password)"
    echo "  - GROCY_API_URL"
    echo "  - GROCY_API_KEY"
    echo "  - AUTH_PASSWORD_HASH (run: ./venv/bin/python scripts/generate_password_hash.py)"
fi

echo ""
echo "Running database migrations..."
sudo -u "$SERVICE_USER" ./venv/bin/alembic upgrade head

echo ""
echo "Creating systemd service..."
cat > /etc/systemd/system/grocyscan.service << EOF
[Unit]
Description=GrocyScan Barcode Scanner
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python -m app.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "Configuring nginx..."
cat > /etc/nginx/sites-available/grocyscan << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:3334;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/grocyscan /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo ""
echo "Starting services..."
systemctl daemon-reload
systemctl enable grocyscan
systemctl start grocyscan
systemctl reload nginx

echo ""
echo "=== Installation Complete ==="
echo ""
echo "GrocyScan is running at: http://localhost"
echo ""
echo "Next steps:"
echo "1. Edit $INSTALL_DIR/.env with your configuration"
echo "2. Generate password hash: cd $INSTALL_DIR && ./venv/bin/python scripts/generate_password_hash.py"
echo "3. Restart service: systemctl restart grocyscan"
echo ""
echo "Useful commands:"
echo "  - View logs: journalctl -u grocyscan -f"
echo "  - Restart: systemctl restart grocyscan"
echo "  - Status: systemctl status grocyscan"
