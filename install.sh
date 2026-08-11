#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

if [ "$(id -u)" -ne 0 ]; then
    echo "❌ This script must be run as root" >&2
    exit 1
fi

if ss -tulnp | grep -q ':80 '; then
    echo "❌ Port 80 is already in use" >&2
    exit 1
fi
if ss -tulnp | grep -q ':443 '; then
    echo "❌ Port 443 is already in use" >&2
    exit 1
fi

if ! command -v docker >/dev/null; then
    echo "🔧 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
fi

if ! docker compose version >/dev/null 2>&1; then
    if ! command -v docker-compose >/dev/null; then
        echo "🔧 Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
fi

# Auto-detect public IP if DOMAIN not set
if [ -z "${DOMAIN:-}" ]; then
    echo "🌐 Detecting server IP..."
    PUBLIC_IP=$(curl -4s --connect-timeout 5 https://ifconfig.io 2>/dev/null || \
                curl -4s --connect-timeout 5 https://icanhazip.com 2>/dev/null || \
                curl -4s --connect-timeout 5 https://ipecho.net/plain 2>/dev/null)
    if [ -n "$PUBLIC_IP" ]; then
        DOMAIN="$PUBLIC_IP"
    else
        DOMAIN="localhost"
    fi
fi

mkdir -p /etc/ctfploy/data
mkdir -p /etc/ctfploy/app

if [ ! -f /etc/ctfploy/.env ]; then
    ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -dc 'A-Za-z0-9')
    SECRET_KEY=$(openssl rand -hex 32)
    cat > /etc/ctfploy/.env <<EOF
ADMIN_PASSWORD=$ADMIN_PASSWORD
SECRET_KEY=$SECRET_KEY
PLATFORM_IMAGE=${PLATFORM_IMAGE:-ctfploy-platform:local}
EOF
else
    source /etc/ctfploy/.env
fi

rsync -a --exclude='.git' "$PROJECT_ROOT/" /etc/ctfploy/app/

cat > /etc/ctfploy/docker-compose.yml <<COMPOSE
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/ctfploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
    depends_on:
      - platform

  platform:
    build:
      context: /etc/ctfploy/app
      dockerfile: Dockerfile
    image: \\${PLATFORM_IMAGE}
    environment:
      ADMIN_PASSWORD: \\${ADMIN_PASSWORD}
      SECRET_KEY: \\${SECRET_KEY}
    volumes:
      - /etc/ctfploy/data:/data
      - /var/run/docker.sock:/var/run/docker.sock
    restart: unless-stopped
COMPOSE

cat > /etc/ctfploy/nginx.conf <<'NGINX'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://platform:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }
}
NGINX

cd /etc/ctfploy
if [ "${PLATFORM_IMAGE}" = "ctfploy-platform:local" ]; then
    docker compose up -d --build
else
    docker compose up -d
fi

echo -e "${GREEN}✅ Conos CTFploy is running!${NC}"
echo -e "Admin panel: http://${DOMAIN}/admin/sign-in"
echo -e "Admin password: ${ADMIN_PASSWORD}"
