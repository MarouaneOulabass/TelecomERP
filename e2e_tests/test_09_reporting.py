# -*- coding: utf-8 -*-
"""Test 09: Reporting + Cockpit rentabilite."""


def test_cockpit_rentabilite(logged_in_page):
    """Cockpit de rentabilite loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    cockpit = page.locator('a:has-text("Cockpit de Rentabilité")')
    if cockpit.count() > 0:
        cockpit.first.click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")
        assert page.locator('.o_error_dialog').count() == 0


def test_analyse_couts(logged_in_page):
    """Analyse des couts pivot/graph loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    analyse = page.locator('a:has-text("Analyse des coûts")')
    if analyse.count() > 0:
        analyse.first.click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")
        assert page.locator('.o_error_dialog').count() == 0
