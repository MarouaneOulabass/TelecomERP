# -*- coding: utf-8 -*-
"""Test 10: Global — no error dialogs on any page navigation."""
import pytest


# All sidebar menu items to click through
MENU_PATHS = [
    ["Sites télécom"],
    ["Bons d'Intervention"],
    ["Bulletins de paie"],
    ["Pointage chantier"],
    ["Habilitations"],
    ["Dotations EPI"],
    ["Équipements"],
    ["Outillages terrain"],
    ["Véhicules"],
    ["Lots"],
    ["PV de réception"],
    ["Appels d'Offres"],
    ["Contrats"],
    ["Cautions bancaires"],
    ["Situations de travaux"],
    ["Décomptes"],
    ["Avances de démarrage"],
    ["Saisie des coûts"],
    ["Cockpit de Rentabilité"],
]


@pytest.mark.parametrize("menu_text", [m[0] for m in MENU_PATHS])
def test_menu_no_error(logged_in_page, menu_text):
    """Each menu item loads without error dialog."""
    page = logged_in_page
    # Open TelecomERP menu
    page.click('.o_menu_entry:has-text("TelecomERP")')
    page.wait_for_timeout(500)

    # Try to find and click the menu item
    menu_item = page.locator(f'a:has-text("{menu_text}")')
    if menu_item.count() > 0:
        menu_item.first.click()
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")

        # Check no error dialog
        error_count = page.locator('.o_error_dialog').count()
        assert error_count == 0, f"Error dialog on '{menu_text}'"

        # Check no "Internal Server Error" text
        content = page.content()
        assert "Internal Server Error" not in content, f"500 error on '{menu_text}'"
