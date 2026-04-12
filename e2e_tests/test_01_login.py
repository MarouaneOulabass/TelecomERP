# -*- coding: utf-8 -*-
"""Test 01: Login and home page."""


def test_login_page_loads(page, base_url):
    """Login page is accessible and has the form."""
    page.goto(f"{base_url}/web/login")
    page.wait_for_load_state("networkidle")
    assert page.locator('input[name="login"]').is_visible()
    assert page.locator('input[name="password"]').is_visible()
    assert page.locator('button[type="submit"]').is_visible()


def test_login_success(logged_in_page):
    """Admin can login successfully."""
    page = logged_in_page
    # Should be on the main app, not login page
    assert "/web/login" not in page.url
    # Should see the navbar
    assert page.locator(".o_main_navbar").is_visible()


def test_welcome_page(logged_in_page, base_url):
    """Welcome page loads with stats."""
    page = logged_in_page
    page.goto(f"{base_url}/telecom/welcome")
    page.wait_for_load_state("networkidle")
    content = page.content()
    assert "TelecomERP" in content
    assert "Sites" in content or "sites" in content
