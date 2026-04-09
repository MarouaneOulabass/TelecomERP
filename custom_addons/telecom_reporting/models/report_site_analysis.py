# -*- coding: utf-8 -*-
"""
report_site_analysis.py
========================
SQL view model: Site portfolio analysis.

Aggregates key metrics per telecom.site record: operator count, technology
count, and intervention counts (total + current month). Used for site-level
KPI dashboards and pivot/graph analysis.

This model is read-only (_auto = False). The PostgreSQL view is created in
init() and uses LEFT JOINs plus subqueries for aggregate metrics.
"""

from odoo import fields, models


class ReportTelecomSiteAnalysis(models.Model):
    """Site portfolio analysis — one row per site (SQL view)."""

    _name = 'report.telecom.site.analysis'
    _description = 'Analyse portefeuille sites'
    _auto = False
    _rec_name = 'name'
    _order = 'name'

    # ------------------------------------------------------------------
    # Dimension fields
    # ------------------------------------------------------------------

    site_id = fields.Many2one(
        'telecom.site',
        string='Site',
        readonly=True,
    )
    name = fields.Char(
        string='Nom du site',
        readonly=True,
    )
    code_interne = fields.Char(
        string='Code interne',
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
    site_type = fields.Selection(
        selection=[
            ('pylone_greenfield', 'Pylône Greenfield'),
            ('rooftop', 'Rooftop'),
            ('shelter', 'Shelter'),
            ('indoor_das', 'Indoor / DAS'),
            ('datacenter', 'Datacenter'),
            ('cabinet_ftth', 'Cabinet FTTH'),
            ('chambre_tirage', 'Chambre de tirage'),
            ('autre', 'Autre'),
        ],
        string='Type de site',
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('prospection', 'Prospection'),
            ('etude', 'Étude technique'),
            ('autorisation', "En cours d'autorisation"),
            ('deploiement', 'Déploiement'),
            ('livre', 'Livré / Opérationnel'),
            ('maintenance', 'En maintenance'),
            ('desactive', 'Désactivé'),
        ],
        string='État',
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Measure fields
    # ------------------------------------------------------------------

    operateur_count = fields.Integer(
        string='Nb opérateurs',
        readonly=True,
    )
    technologie_count = fields.Integer(
        string='Nb technologies',
        readonly=True,
    )
    intervention_count_total = fields.Integer(
        string='Nb interventions (total)',
        readonly=True,
    )
    intervention_count_month = fields.Integer(
        string='Nb interventions (mois courant)',
        readonly=True,
    )
    last_intervention_date = fields.Date(
        string='Dernière intervention',
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
            CREATE OR REPLACE VIEW report_telecom_site_analysis AS (
                SELECT
                    ts.id                                         AS id,
                    ts.id                                         AS site_id,
                    ts.name                                       AS name,
                    ts.code_interne                              AS code_interne,
                    ts.wilaya                                     AS wilaya,
                    ts.site_type                                  AS site_type,
                    ts.state                                      AS state,
                    ts.company_id                                 AS company_id,

                    -- Count of operators linked to the site
                    COALESCE((
                        SELECT COUNT(*)
                        FROM telecom_site_operator_rel rel_op
                        WHERE rel_op.site_id = ts.id
                    ), 0)::INTEGER                               AS operateur_count,

                    -- Count of technologies deployed on the site
                    COALESCE((
                        SELECT COUNT(*)
                        FROM telecom_site_technologie_rel rel_tech
                        WHERE rel_tech.site_id = ts.id
                    ), 0)::INTEGER                               AS technologie_count,

                    -- Total interventions on this site (all time)
                    COALESCE((
                        SELECT COUNT(*)
                        FROM telecom_intervention ti
                        WHERE ti.site_id = ts.id
                          AND ti.active = TRUE
                    ), 0)::INTEGER                               AS intervention_count_total,

                    -- Interventions in the current calendar month
                    COALESCE((
                        SELECT COUNT(*)
                        FROM telecom_intervention ti
                        WHERE ti.site_id = ts.id
                          AND ti.active = TRUE
                          AND date_trunc('month', ti.date_planifiee)
                              = date_trunc('month', NOW())
                    ), 0)::INTEGER                               AS intervention_count_month,

                    -- Date of the most recent intervention
                    (
                        SELECT MAX(ti.date_planifiee)::date
                        FROM telecom_intervention ti
                        WHERE ti.site_id = ts.id
                          AND ti.active = TRUE
                    )                                            AS last_intervention_date

                FROM telecom_site ts
                WHERE ts.active = TRUE
            )
        """)
