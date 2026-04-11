# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Suivi Carburant',
    'version': '17.0.1.0.1',
    'category': 'TelecomERP',
    'summary': 'Suivi consommation carburant par vehicule et projet',
    'description': """
TelecomERP — Suivi Carburant
=============================
Suivi des pleins carburant des vehicules terrain :

- Saisie du plein (date, vehicule, station, litres, prix, kilometrage)
- Rattachement obligatoire au projet et lot
- Creation automatique d'une ecriture de cout (telecom.cost.entry)
- Vues analyse : pivot et graphique par vehicule / projet / mois
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_fleet',
        'telecom_cost',
        'telecom_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/telecom_carburant_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 16,
}
