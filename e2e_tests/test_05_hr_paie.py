# -*- coding: utf-8 -*-
"""Test 05: RH & Paie module."""
from conftest import click_menu


def test_bulletins_list(logged_in_page):
    """Bulletins de paie list loads."""
    page = logged_in_page
    click_menu(page, "RH Terrain", "Bulletins de paie")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    assert page.locator('.o_error_dialog').count() == 0
    records = page.locator('.o_data_row')
    assert records.count() >= 1, "No bulletins displayed"


def test_pointage_list(logged_in_page):
    """Pointage chantier list loads."""
    page = logged_in_page
    click_menu(page, "RH Terrain", "Pointage chantier")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    assert page.locator('.o_error_dialog').count() == 0
