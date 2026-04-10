# -*- coding: utf-8 -*-
{
    'name': 'TelecomERP — Reporting & Dashboards',
    'version': '17.0.1.0.0',
    'category': 'TelecomERP',
    'summary': 'Tableaux de bord, KPIs et rapports analytiques croisés pour TelecomERP',
    'description': """
        Module de reporting et tableaux de bord pour TelecomERP :

        * Analyse des interventions terrain (KPIs SLA, durées, types)
        * Analyse du portefeuille de sites (par wilaya, état, opérateur)
        * Analyse financière (situations de travaux, décomptes, délais)
        * Bilan social CNSS/AMO : déclaration mensuelle PDF multi-employés

        Basé sur des vues SQL (_auto=False) pour des agrégations performantes.
        Aucun nouveau modèle métier — uniquement des vues analytiques et rapports.
    """,
    'author': 'TelecomERP',
    'license': 'OPL-1',
    'depends': [
        'telecom_base',
        'telecom_site',
        'telecom_intervention',
        'telecom_hr_ma',
        'telecom_project',
        'telecom_ao',
        'telecom_contract',
        'telecom_equipment',
        'telecom_fleet',
        'telecom_finance_ma',
        'mail',
    ],
    'data': [
        # Security first
        'security/ir.model.access.csv',
        # Data / shortcut actions
        'data/telecom_reporting_actions.xml',
        # Views (ordered: analysis views then menus)
        'views/report_intervention_views.xml',
        'views/report_site_views.xml',
        'views/report_finance_views.xml',
        'views/telecom_dashboard_views.xml',
        # Wizard — before menus
        'wizard/export_operateur_views.xml',
        'views/menu_views.xml',
        # Reports (PDF)
        'report/telecom_bilan_social.xml',
        'report/telecom_bilan_social_annuel.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'sequence': 50,
}
