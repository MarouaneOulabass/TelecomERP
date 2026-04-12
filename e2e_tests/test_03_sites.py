# -*- coding: utf-8 -*-
"""Test 03: Sites module — list, create, view."""
from conftest import click_menu


def test_sites_list_loads(logged_in_page, base_url):
    """Sites list shows existing sites."""
    page = logged_in_page
    # Navigate to Sites > Sites telecom
    click_menu(page, "Sites", "Sites télécom")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    # Should see a list or kanban with site records
    records = page.locator('.o_data_row, .o_kanban_record')
    # We have 25 demo sites, should see some
    assert records.count() >= 1, "No sites displayed"


def test_site_form_opens(logged_in_page, base_url):
    """Clicking a site opens the form without error."""
    page = logged_in_page
    click_menu(page, "Sites", "Sites télécom")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    # Switch to list view if in kanban
    list_btn = page.locator('.o_switch_view.o_list')
    if list_btn.count() > 0:
        list_btn.click()
        page.wait_for_timeout(1000)
    # Click first record
    first_row = page.locator('.o_data_row').first
    if first_row.is_visible():
        first_row.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        # Should be on form view
        assert page.locator('.o_form_view').is_visible(), "Form view not opened"
        # No error dialog
        assert page.locator('.o_error_dialog').count() == 0
