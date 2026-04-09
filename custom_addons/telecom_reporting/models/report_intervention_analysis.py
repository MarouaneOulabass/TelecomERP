# -*- coding: utf-8 -*-
"""
report_intervention_analysis.py
================================
SQL view model: Intervention KPI analysis.

Aggregates one row per telecom.intervention record, joining with telecom.site
to expose geographical and categorical dimensions for pivot/graph analysis.

This model is read-only (_auto = False) — no INSERT/UPDATE/DELETE allowed.
The underlying PostgreSQL view is created/replaced in init().
"""

from odoo import fields, models


class ReportTelecomInterventionAnalysis(models.Model):
    """Intervention KPI analysis — one row per intervention (SQL view)."""

    _name = 'report.telecom.intervention.analysis'
    _description = 'Analyse interventions terrain'
    _auto = False
    _rec_name = 'site_name'
    _order = 'date_planifiee desc'

    # ------------------------------------------------------------------
    # Dimension fields
    # ------------------------------------------------------------------

    site_id = fields.Many2one(
        'telecom.site',
        string='Site',
        readonly=True,
    )
    site_name = fields.Char(
        string='Nom du site',
        readonly=True,
    )
    wilaya = fields.Selection(
        selection=[
            ('casablanca_settat', 'Casablanca-Settat'),
            ('rabat_sale_kenitra', 'Rabat-Salé-Kénitra'),
            ('marrakech_safi', 'Marrakech-Safi'),
            ('fes_meknes', 'Fès-Meknès'),
            ('tanger_tetouan_alhoceima', 'Tanger-Tétouan-Al Hoceïma'),
            ('souss_massa', 'Souss-Massa'),
            ('draa_tafilalet', 'Drâa-Tafilalet'),
            ('beni_mellal_khenifra', 'Béni Mellal-Khénifra'),
            ('oriental', "L'Oriental"),
            ('guelmim_oued_noun', 'Guelmim-Oued Noun'),
            ('laayoune_sakia_el_hamra', 'Laâyoune-Sakia El Hamra'),
            ('dakhla_oued_ed_dahab', 'Dakhla-Oued Ed-Dahab'),
        ],
        string='Région (Wilaya)',
        readonly=True,
    )
    intervention_type = fields.Selection(
        selection=[
            ('preventive', 'Préventive'),
            ('corrective', 'Corrective (dépannage)'),
            ('installation', 'Installation / Mise en service'),
            ('audit', 'Audit technique'),
            ('depose', 'Dépose équipement'),
        ],
        string="Type d'intervention",
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('planifie', 'Planifié'),
            ('en_cours', 'En cours'),
            ('termine', 'Terminé (terrain)'),
            ('valide', 'Validé (chef)'),
            ('facture', 'Facturé'),
            ('annule', 'Annulé'),
        ],
        string='État',
        readonly=True,
    )
    date_planifiee = fields.Date(
        string='Date planifiée',
        readonly=True,
    )
    month = fields.Char(
        string='Mois (YYYY-MM)',
        readonly=True,
    )
    year = fields.Char(
        string='Année',
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Measure fields
    # ------------------------------------------------------------------

    count_total = fields.Integer(
        string='Nb interventions',
        readonly=True,
    )
    count_sla_depasse = fields.Integer(
        string='Nb SLA dépassés',
        readonly=True,
    )
    duree_moyenne = fields.Float(
        string='Durée réelle (h)',
        digits=(8, 2),
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Company
    # ------------------------------------------------------------------

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        readonly=True,
    )

    # ------------------------------------------------------------------
    # SQL view initialisation
    # ------------------------------------------------------------------

    def init(self):
        """Create or replace the PostgreSQL view backing this model."""
        self._cr.execute("""
            CREATE OR REPLACE VIEW report_telecom_intervention_analysis AS (
                SELECT
                    ti.id                                         AS id,
                    ti.site_id                                    AS site_id,
                    ts.name                                       AS site_name,
                    ts.wilaya                                     AS wilaya,
                    ti.intervention_type                          AS intervention_type,
                    ti.state                                      AS state,
                    ti.date_planifiee::date                       AS date_planifiee,
                    to_char(ti.date_planifiee, 'YYYY-MM')        AS month,
                    to_char(ti.date_planifiee, 'YYYY')           AS year,
                    1                                             AS count_total,
                    CASE WHEN ti.sla_depasse THEN 1 ELSE 0 END   AS count_sla_depasse,
                    COALESCE(ti.duree_reelle, 0.0)               AS duree_moyenne,
                    ti.company_id                                 AS company_id
                FROM telecom_intervention ti
                LEFT JOIN telecom_site ts ON ts.id = ti.site_id
                WHERE ti.active = TRUE
            )
        """)
