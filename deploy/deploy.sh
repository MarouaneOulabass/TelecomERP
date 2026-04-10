#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# TelecomERP — Deploy to production server
#
# Usage:  bash deploy/deploy.sh
# Requires: SSH access to root@65.108.146.17
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SERVER="root@65.108.146.17"
REMOTE_DIR="/opt/telecomerp"

echo "═══════════════════════════════════════════════════════"
echo "  TelecomERP — Déploiement production"
echo "  Serveur: $SERVER"
echo "═══════════════════════════════════════════════════════"

# ── 1. Sync files ────────────────────────────────────────────────────────────
echo ""
echo "[1/4] Synchronisation des fichiers..."
rsync -avz --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'test-reports' \
    --exclude '.env' \
    --exclude 'node_modules' \
    ./custom_addons/ "${SERVER}:${REMOTE_DIR}/custom_addons/"

rsync -avz \
    ./deploy/docker-compose.prod.yml "${SERVER}:${REMOTE_DIR}/docker-compose.yml"

rsync -avz \
    ./deploy/config/ "${SERVER}:${REMOTE_DIR}/config/"

rsync -avz \
    ./deploy/nginx/ "${SERVER}:${REMOTE_DIR}/nginx/"

echo "  Fichiers synchronisés"

# ── 2. Create SSL directory (placeholder) ─────────────────────────────────────
echo ""
echo "[2/4] Préparation SSL..."
ssh "$SERVER" "mkdir -p ${REMOTE_DIR}/nginx/ssl"

# ── 3. Start services ───────────────────────────────────────────────────────
echo ""
echo "[3/4] Démarrage des services..."
ssh "$SERVER" "cd ${REMOTE_DIR} && docker compose pull && docker compose up -d"

# ── 4. Wait and init database ───────────────────────────────────────────────
echo ""
echo "[4/4] Initialisation de la base de données..."
echo "  Attente démarrage Odoo (30s)..."
sleep 30

ssh "$SERVER" "cd ${REMOTE_DIR} && docker compose exec -T odoo /usr/bin/python3 /usr/bin/odoo \
    -c /etc/odoo/odoo.conf -d telecomerp \
    -i base,contacts,sale,purchase,stock,account,project,hr,hr_contract,hr_holidays,crm,maintenance \
    --stop-after-init --no-http"

echo "  Modules Odoo natifs installés"

ssh "$SERVER" "cd ${REMOTE_DIR} && docker compose exec -T odoo /usr/bin/python3 /usr/bin/odoo \
    -c /etc/odoo/odoo.conf -d telecomerp \
    -i telecom_base,telecom_localization_ma,telecom_site,telecom_hr_ma,telecom_intervention,telecom_equipment,telecom_fleet,telecom_project,telecom_ao,telecom_contract,telecom_finance_ma,telecom_reporting \
    --stop-after-init --no-http"

echo "  Modules TelecomERP installés"

# ── Done ─────────────────────────────────────────────────────────────────────
ssh "$SERVER" "cd ${REMOTE_DIR} && docker compose restart odoo"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  DÉPLOIEMENT TERMINÉ"
echo ""
echo "  URL : http://65.108.146.17"
echo "  Login : admin"
echo "  Password : admin (à changer !)"
echo "  Master password : TelecomERP@Admin2024!"
echo "═══════════════════════════════════════════════════════"
