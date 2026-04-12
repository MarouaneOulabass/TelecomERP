# -*- coding: utf-8 -*-
"""
TelecomERP — Playwright E2E Test Configuration
================================================
"""
import pytest

BASE_URL = "https://erp.kleanse.fr"
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin"


@pytest.fixture(scope="session")
def browser_context_args():
    return {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def logged_in_page(page, base_url):
    """Login and return authenticated page."""
    page.goto(f"{base_url}/web/login", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)

    page.fill('input[name="login"]', ADMIN_LOGIN)
    page.fill('input[name="password"]', ADMIN_PASSWORD)
    page.click('button[type="submit"]')

    # Wait for Odoo web client to load (navbar visible = logged in)
    page.wait_for_selector('.o_main_navbar', timeout=60000)
    page.wait_for_timeout(2000)

    return page
