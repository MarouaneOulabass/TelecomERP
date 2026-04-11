{
    'name': 'TelecomERP — Rattachement des coûts',
    'version': '17.0.1.0.1',
    'category': 'TelecomERP',
    'summary': 'Rattachement obligatoire des coûts aux projets et lots',
    'description': """
Coeur du cockpit de rentabilité TelecomERP.

Chaque coût opérationnel (main-d'oeuvre, matériel, sous-traitance, carburant,
frais généraux) doit être rattaché à un Projet + Lot. La tâche est optionnelle.

Règle non-négociable : aucun CostEntry sans projet+lot.
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': ['telecom_base', 'telecom_project', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/telecom_cost_type_data.xml',
        'views/telecom_cost_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 15,
}
