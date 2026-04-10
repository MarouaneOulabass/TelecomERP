#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# TelecomERP — Script de non-régression BDD avant déploiement
#
# Usage:
#   bash bin/pre-deploy-tests.sh                  # tous les tests
#   bash bin/pre-deploy-tests.sh --module site     # un module spécifique
#   bash bin/pre-deploy-tests.sh --smoke           # tests smoke uniquement
#   bash bin/pre-deploy-tests.sh --report          # génère rapport HTML
#
# Doit être exécuté depuis la racine du projet :
#   cd /path/to/Telecomerp && bash bin/pre-deploy-tests.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/test-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

MODULE=""
SMOKE_ONLY=false
HTML_REPORT=false

# ─── Parse arguments ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --module)   MODULE="$2"; shift 2 ;;
        --smoke)    SMOKE_ONLY=true; shift ;;
        --report)   HTML_REPORT=true; shift ;;
        *)          echo "Argument inconnu: $1"; exit 1 ;;
    esac
done

# ─── Banner ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       TelecomERP — Suite BDD pre-deployment                  ║${NC}"
echo -e "${BLUE}║       $(date '+%Y-%m-%d %H:%M:%S')                                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Verify Docker Compose is running ────────────────────────────────────────
echo -e "${YELLOW}[1/4] Vérification de l'environnement Docker...${NC}"
if ! docker compose ps --services --filter "status=running" 2>/dev/null | grep -q "odoo"; then
    echo -e "${RED}✗ Le service Odoo n'est pas démarré.${NC}"
    echo "  Lancez d'abord: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Service Odoo actif${NC}"

# ─── Install test dependencies inside container ───────────────────────────────
echo ""
echo -e "${YELLOW}[2/4] Installation des dépendances de test...${NC}"
docker compose exec -T odoo pip install -q \
    pytest>=7.4 \
    pytest-bdd>=7.1 \
    pytest-cov>=4.1 \
    pytest-html>=4.1 \
    pytest-sugar>=1.0 \
    freezegun>=1.4
echo -e "${GREEN}✓ Dépendances installées${NC}"

# ─── Build pytest command ─────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[3/4] Construction de la commande pytest...${NC}"

PYTEST_ARGS=(
    "/mnt/extra-addons"
    "--tb=short"
    "-v"
    "--color=yes"
)

if [[ -n "$MODULE" ]]; then
    PYTEST_ARGS+=("-m" "$MODULE")
    echo "  Filtre module: ${MODULE}"
fi

if [[ "$SMOKE_ONLY" == "true" ]]; then
    PYTEST_ARGS+=("-m" "smoke")
    echo "  Mode: smoke tests uniquement"
fi

if [[ "$HTML_REPORT" == "true" ]]; then
    mkdir -p "${REPORT_DIR}"
    REPORT_FILE="${REPORT_DIR}/bdd_report_${TIMESTAMP}.html"
    PYTEST_ARGS+=("--html=${REPORT_FILE}" "--self-contained-html")
    echo "  Rapport HTML: ${REPORT_FILE}"
fi

# Coverage
PYTEST_ARGS+=(
    "--cov=/mnt/extra-addons"
    "--cov-report=term-missing"
    "--cov-report=html:/tmp/coverage_${TIMESTAMP}"
)

echo -e "${GREEN}✓ Commande construite${NC}"

# ─── Run tests ────────────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/4] Exécution de la suite BDD...${NC}"
echo ""

EXIT_CODE=0
MSYS_NO_PATHCONV=1 docker compose exec -T \
    -e ODOO_RC=/etc/odoo/odoo.conf \
    -e ODOO_DB=telecomerp \
    odoo \
    /usr/bin/python3 -m pytest "${PYTEST_ARGS[@]}" \
    || EXIT_CODE=$?

# ─── Results ─────────────────────────────────────────────────────────────────
echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓  TOUS LES TESTS BDD PASSENT — Déploiement autorisé        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗  ÉCHEC BDD — Déploiement BLOQUÉ                           ║${NC}"
    echo -e "${RED}║     Corrigez les scénarios en échec avant de déployer.        ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
fi
echo ""

exit $EXIT_CODE
