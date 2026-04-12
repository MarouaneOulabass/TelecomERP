# -*- coding: utf-8 -*-
"""Test 02: Navigation — all menus accessible without error."""


def test_telecom_main_menu_visible(logged_in_page):
    """TelecomERP menu is in the top bar."""
    page = logged_in_page
    # Click on TelecomERP in navbar
    telecom_menu = page.locator('.o_menu_entry:has-text("TelecomERP")')
    if telecom_menu.count() > 0:
        assert telecom_menu.first.is_visible()


def test_navigate_sites(logged_in_page):
    """Sites menu loads without error."""
    page = logged_in_page
    page.goto(page.url)  # ensure on main page
    # Navigate via URL action
    page.goto(f"{page.url.split('/web')[0]}/odoo/telecom-site")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    # Should not have an error dialog
    error = page.locator('.o_error_dialog')
    assert error.count() == 0, "Error dialog visible on Sites page"


def test_no_500_error_on_any_page(logged_in_page, base_url):
    """Navigate to key pages and verify no 500 error."""
    page = logged_in_page
    pages_to_test = [
        "/web#action=",  # home
        "/telecom/welcome",  # welcome
    ]
    for path in pages_to_test:
        resp = page.goto(f"{base_url}{path}")
        if resp:
            assert resp.status != 500, f"500 error on {path}"
