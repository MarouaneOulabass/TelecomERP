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
    page.goto(f"{base_url}/web/login")
    page.wait_for_load_state("networkidle")

    # Fill login form
    page.fill('input[name="login"]', ADMIN_LOGIN)
    page.fill('input[name="password"]', ADMIN_PASSWORD)
    page.click('button[type="submit"]')

    # Wait for main interface to load
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    return page
