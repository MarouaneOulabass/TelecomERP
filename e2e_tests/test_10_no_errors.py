# -*- coding: utf-8 -*-
"""Test 10: Global — no error dialogs on any page navigation."""
import pytest
from conftest import click_menu


# All section > submenu item pairs to click through
MENU_PATHS = [
    ("Sites", "Sites télécom"),
    ("Interventions", "Bons d'Intervention"),
    ("RH Terrain", "Bulletins de paie"),
    ("RH Terrain", "Pointage chantier"),
    ("Équipements", "Équipements"),
    ("Flotte", "Véhicules"),
    ("Commercial", "Appels d'Offres"),
    ("Contrats", "Contrats"),
    ("Finance", "Situations de travaux"),
    ("Finance", "Décomptes"),
    ("Coûts", "Saisie des coûts"),
    ("Coûts", "Cockpit de Rentabilité"),
    ("Reporting", "Direction — CA"),
]


@pytest.mark.parametrize(
    "section,item_text",
    MENU_PATHS,
    ids=[f"{s} > {i}" for s, i in MENU_PATHS],
)
def test_menu_no_error(logged_in_page, section, item_text):
    """Each menu item loads without error dialog."""
    page = logged_in_page

    click_menu(page, section, item_text)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Check no error dialog
    error_count = page.locator('.o_error_dialog').count()
    assert error_count == 0, f"Error dialog on '{section} > {item_text}'"

    # Check no "Internal Server Error" text
    content = page.content()
    assert "Internal Server Error" not in content, f"500 error on '{section} > {item_text}'"
