# -*- coding: utf-8 -*-
"""Test 07: Commercial — AO, Contrats, Finance."""
from conftest import click_menu


def test_ao_list(logged_in_page):
    """Appels d'offres list/kanban loads."""
    page = logged_in_page
    click_menu(page, "Commercial", "Appels d'Offres")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    assert page.locator('.o_error_dialog').count() == 0


def test_contrats_list(logged_in_page):
    """Contrats list loads."""
    page = logged_in_page
    click_menu(page, "Contrats", "Contrats")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    assert page.locator('.o_error_dialog').count() == 0


def test_couts_list(logged_in_page):
    """Saisie des couts loads."""
    page = logged_in_page
    click_menu(page, "Coûts", "Saisie des coûts")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    assert page.locator('.o_error_dialog').count() == 0
    records = page.locator('.o_data_row')
    assert records.count() >= 1, "No cost entries"
