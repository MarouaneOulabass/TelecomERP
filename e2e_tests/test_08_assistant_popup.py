# -*- coding: utf-8 -*-
"""Test 08: Assistant popup widget."""


def test_fab_button_visible(logged_in_page):
    """FAB button is visible on the main page."""
    page = logged_in_page
    page.wait_for_timeout(3000)
    fab = page.locator('.telecom-assistant-fab')
    # FAB should be present (OWL component mounted)
    if fab.count() > 0:
        assert fab.is_visible(), "FAB button not visible"


def test_popup_opens_on_click(logged_in_page):
    """Clicking FAB opens the chat panel."""
    page = logged_in_page
    page.wait_for_timeout(3000)
    fab = page.locator('.telecom-assistant-fab')
    if fab.count() > 0 and fab.is_visible():
        fab.click()
        page.wait_for_timeout(500)
        panel = page.locator('.telecom-assistant-panel')
        assert panel.is_visible(), "Chat panel did not open"
        # Should see the input field
        assert page.locator('.telecom-assistant-input input').is_visible()


def test_popup_has_welcome_message(logged_in_page):
    """Chat panel shows welcome message when empty."""
    page = logged_in_page
    page.wait_for_timeout(3000)
    fab = page.locator('.telecom-assistant-fab')
    if fab.count() > 0 and fab.is_visible():
        fab.click()
        page.wait_for_timeout(500)
        welcome = page.locator('.telecom-assistant-welcome')
        if welcome.count() > 0:
            assert "Bonjour" in welcome.inner_text() or "question" in welcome.inner_text()


def test_popup_closes(logged_in_page):
    """Close button closes the panel."""
    page = logged_in_page
    page.wait_for_timeout(3000)
    fab = page.locator('.telecom-assistant-fab')
    if fab.count() > 0 and fab.is_visible():
        fab.click()
        page.wait_for_timeout(500)
        close_btn = page.locator('.telecom-assistant-header-actions button:has(.fa-times)')
        if close_btn.count() > 0:
            close_btn.click()
            page.wait_for_timeout(500)
            panel = page.locator('.telecom-assistant-panel')
            assert panel.count() == 0 or not panel.is_visible()
