# -*- coding: utf-8 -*-
"""Test 09: Reporting + Cockpit rentabilite."""
from conftest import click_menu


def test_cockpit_rentabilite(logged_in_page):
    """Cockpit de rentabilite loads."""
    page = logged_in_page
    click_menu(page, "Coûts", "Cockpit de Rentabilité")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    assert page.locator('.o_error_dialog').count() == 0


def test_analyse_couts(logged_in_page):
    """Analyse des couts pivot/graph loads."""
    page = logged_in_page
    click_menu(page, "Coûts", "Analyse des coûts")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    assert page.locator('.o_error_dialog').count() == 0
