#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# TelecomERP — Run E2E Playwright Tests
#
# Usage:
#   pip install pytest-playwright
#   playwright install chromium
#   bash e2e_tests/run_e2e.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

echo "══════════════════════════════════════════════"
echo "  TelecomERP — Tests E2E Playwright"
echo "══════════════════════════════════════════════"

# Install if needed
pip install -q pytest-playwright 2>/dev/null || true
playwright install chromium 2>/dev/null || true

# Run tests
pytest e2e_tests/ \
    -v \
    --tb=short \
    --headed \
    --browser chromium \
    --slowmo 500

echo "══════════════════════════════════════════════"
echo "  Tests E2E terminés"
echo "══════════════════════════════════════════════"
