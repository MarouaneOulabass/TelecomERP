# -*- coding: utf-8 -*-
"""Test 07: Commercial — AO, Contrats, Finance."""


def test_ao_list(logged_in_page):
    """Appels d'offres list/kanban loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    ao_menu = page.locator('a:has-text("Appels d\'Offres")')
    if ao_menu.count() > 0:
        ao_menu.first.click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")
        assert page.locator('.o_error_dialog').count() == 0


def test_contrats_list(logged_in_page):
    """Contrats list loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    ct_menu = page.locator('a:has-text("Contrats")')
    if ct_menu.count() > 0:
        ct_menu.first.click()
        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle")
        assert page.locator('.o_error_dialog').count() == 0


def test_couts_list(logged_in_page):
    """Saisie des couts loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    cost_menu = page.locator('a:has-text("Saisie des coûts")')
    if cost_menu.count() > 0:
        cost_menu.first.click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")
        assert page.locator('.o_error_dialog').count() == 0
        records = page.locator('.o_data_row')
        assert records.count() >= 1, "No cost entries"
