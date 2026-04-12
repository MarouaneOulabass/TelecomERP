# -*- coding: utf-8 -*-
"""Test 06: Equipements + Flotte."""
from conftest import click_menu


def test_equipements_list(logged_in_page):
    """Equipements list loads."""
    page = logged_in_page
    click_menu(page, "Équipements", "Équipements")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    assert page.locator('.o_error_dialog').count() == 0


def test_vehicules_list(logged_in_page):
    """Vehicules list loads."""
    page = logged_in_page
    click_menu(page, "Flotte", "Véhicules")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    assert page.locator('.o_error_dialog').count() == 0
