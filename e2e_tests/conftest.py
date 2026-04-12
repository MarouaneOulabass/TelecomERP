# -*- coding: utf-8 -*-
"""
TelecomERP — Playwright E2E Test Configuration
================================================
"""
import pytest

BASE_URL = "https://erp.kleanse.fr"
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin"


def click_menu(page, section_text, item_text=None):
    """Click a TelecomERP section menu, then optionally a submenu item.

    In Odoo 17 the top navbar uses:
      - ``a.o_menu_brand`` for the app name (TelecomERP)
      - ``.o_menu_sections button.dropdown-toggle`` for each section
      - ``.dropdown-menu .dropdown-item`` for submenu items
    """
    section = page.locator(
        f'.o_menu_sections button.dropdown-toggle:has-text("{section_text}")'
    )
    if section.count() > 0:
        section.first.click()
        page.wait_for_timeout(500)
        if item_text:
            item = page.locator(
                f'.dropdown-menu .dropdown-item:has-text("{item_text}")'
            )
            if item.count() > 0:
                item.first.click()
                page.wait_for_timeout(2000)


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
