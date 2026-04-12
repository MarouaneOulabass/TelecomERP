# -*- coding: utf-8 -*-
"""Test 05: RH & Paie module."""


def test_bulletins_list(logged_in_page):
    """Bulletins de paie list loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    paie_menu = page.locator('a:has-text("Bulletins de paie")')
    if paie_menu.count() > 0:
        paie_menu.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        assert page.locator('.o_error_dialog').count() == 0
        records = page.locator('.o_data_row')
        assert records.count() >= 1, "No bulletins displayed"


def test_pointage_list(logged_in_page):
    """Pointage chantier list loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    ptg_menu = page.locator('a:has-text("Pointage chantier")')
    if ptg_menu.count() > 0:
        ptg_menu.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        assert page.locator('.o_error_dialog').count() == 0
