# -*- coding: utf-8 -*-
"""Test 04: Interventions module."""


def test_interventions_list(logged_in_page):
    """Interventions list loads with records."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    inter_menu = page.locator('a:has-text("Bons d\'Intervention")')
    if inter_menu.count() > 0:
        inter_menu.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        # Should see records (we have 15 demo interventions)
        records = page.locator('.o_data_row, .o_kanban_record')
        assert records.count() >= 1, "No interventions displayed"
        assert page.locator('.o_error_dialog').count() == 0


def test_intervention_form(logged_in_page):
    """Intervention form opens and shows statusbar."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    inter_menu = page.locator('a:has-text("Bons d\'Intervention")')
    if inter_menu.count() > 0:
        inter_menu.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        list_btn = page.locator('.o_switch_view.o_list')
        if list_btn.count() > 0:
            list_btn.click()
            page.wait_for_timeout(1000)
        first_row = page.locator('.o_data_row').first
        if first_row.is_visible():
            first_row.click()
            page.wait_for_timeout(1500)
            assert page.locator('.o_form_view').is_visible()
            # Should have statusbar
            assert page.locator('.o_statusbar_status').count() > 0
