#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# TelecomERP — Server Setup Script (Hetzner CPX22 / Ubuntu 22.04+)
#
# Usage:  ssh root@65.108.146.17 'bash -s' < deploy/setup-server.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

echo "═══════════════════════════════════════════════════════"
echo "  TelecomERP — Configuration serveur de production"
echo "═══════════════════════════════════════════════════════"

# ── 1. System update ─────────────────────────────────────────────────────────
echo "[1/6] Mise à jour du système..."
apt-get update -qq && apt-get upgrade -y -qq

# ── 2. Install Docker ────────────────────────────────────────────────────────
echo "[2/6] Installation de Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi
echo "  Docker $(docker --version | awk '{print $3}')"

# ── 3. Install Docker Compose plugin ─────────────────────────────────────────
echo "[3/6] Vérification Docker Compose..."
if ! docker compose version &>/dev/null; then
    apt-get install -y -qq docker-compose-plugin
fi
echo "  $(docker compose version)"

# ── 4. Firewall ──────────────────────────────────────────────────────────────
echo "[4/6] Configuration firewall..."
apt-get install -y -qq ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
echo "  Firewall actif (SSH + HTTP + HTTPS)"

# ── 5. Create app directory ─────────────────────────────────────────────────
echo "[5/6] Préparation du répertoire /opt/telecomerp..."
mkdir -p /opt/telecomerp
cd /opt/telecomerp

# ── 6. Swap (CPX22 has 4GB RAM — add 2GB swap for safety) ────────────────────
echo "[6/6] Configuration swap..."
if ! swapon --show | grep -q swapfile; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "  Swap 2GB activé"
else
    echo "  Swap déjà configuré"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Serveur prêt ! Prochaine étape :"
echo "  rsync les fichiers puis docker compose up -d"
echo "═══════════════════════════════════════════════════════"
