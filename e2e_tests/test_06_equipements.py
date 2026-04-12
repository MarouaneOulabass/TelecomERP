# -*- coding: utf-8 -*-
"""Test 06: Equipements + Flotte."""


def test_equipements_list(logged_in_page):
    """Equipements list loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    eq_menu = page.locator('a:has-text("Équipements")')
    if eq_menu.count() > 0:
        eq_menu.first.click()
        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle")
        assert page.locator('.o_error_dialog').count() == 0


def test_vehicules_list(logged_in_page):
    """Vehicules list loads."""
    page = logged_in_page
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)
    veh_menu = page.locator('a:has-text("Véhicules")')
    if veh_menu.count() > 0:
        veh_menu.first.click()
        page.wait_for_timeout(1500)
        page.wait_for_load_state("networkidle")
        assert page.locator('.o_error_dialog').count() == 0
