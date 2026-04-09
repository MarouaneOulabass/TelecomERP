# -*- coding: utf-8 -*-
"""
report_finance_analysis.py
===========================
SQL view model: Financial KPI analysis.

Aggregates telecom.situation (situations de travaux) and telecom.decompte
(décomptes CCAG) per project and calendar month.  The view exposes:
  - Amounts billed (situations) and settled (decomptes)
  - Overdue payment counts (délai légal 60 jours, loi 69-21)

This model is read-only (_auto = False).  The underlying tables
telecom_situation and telecom_decompte are created by telecom_finance_ma.
The view uses CREATE OR REPLACE, so it is safe to reinstall at any time.

NOTE: telecom.situation carries the fields:
    project_id (Many2one project.project), state, net_a_payer (Monetary),
    delai_depasse (Boolean), company_id, date_situation (Date)

telecom.decompte carries:
    project_id, state, net_a_regler (Monetary), delai_depasse (Boolean),
    company_id, date_decompte (Date)

These are the field names declared in the telecom_finance_ma module spec.
If the tables do not yet exist (module not installed), the view creation
is deferred silently by catching the ProgrammingError.
"""

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ReportTelecomFinanceAnalysis(models.Model):
    """Financial KPI analysis — aggregated per project/month (SQL view)."""

    _name = 'report.telecom.finance.analysis'
    _description = 'Analyse financière projets'
    _auto = False
    _rec_name = 'project_name'
    _order = 'year desc, month desc'

    # ------------------------------------------------------------------
    # Dimension fields
    # ------------------------------------------------------------------

    project_id = fields.Many2one(
        'project.project',
        string='Projet',
        readonly=True,
    )
    project_name = fields.Char(
        string='Nom du projet',
        readonly=True,
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
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
    # Measure fields — situations de travaux
    # ------------------------------------------------------------------

    nb_situations = fields.Integer(
        string='Nb situations',
        readonly=True,
    )
    montant_situation_ht_total = fields.Float(
        string='Total situations HT (MAD)',
        digits=(16, 2),
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Measure fields — décomptes
    # ------------------------------------------------------------------

    nb_decomptes = fields.Integer(
        string='Nb décomptes',
        readonly=True,
    )
    net_a_regler_total = fields.Float(
        string='Total net à régler (MAD)',
        digits=(16, 2),
        readonly=True,
    )

    # ------------------------------------------------------------------
    # Measure fields — délais dépassés (loi 69-21)
    # ------------------------------------------------------------------

    nb_delais_depasses = fields.Integer(
        string='Nb délais dépassés',
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
        """
        Create or replace the PostgreSQL view for financial analysis.

        The view is a UNION ALL of situations and decomptes, both grouped
        by project + month.  If the source tables do not yet exist (e.g.
        telecom_finance_ma not installed), the creation is skipped and a
        warning is logged — the view will be created on the next upgrade.
        """
        # Set a savepoint so that a failed CREATE VIEW can be rolled back
        # without aborting the whole transaction (allows module install to
        # continue even when telecom_finance_ma tables are absent).
        self._cr.execute("SAVEPOINT report_finance_view")
        try:
            self._cr.execute("""
                CREATE OR REPLACE VIEW report_telecom_finance_analysis AS (
                    SELECT
                        -- Stable row identifier: combine type flag + record id
                        -- Situations rows: positive id range
                        sit.id                                          AS id,
                        sit.project_id                                  AS project_id,
                        pp.name                                         AS project_name,
                        pp.partner_id                                   AS client_id,
                        to_char(sit.date_situation, 'YYYY-MM')         AS month,
                        to_char(sit.date_situation, 'YYYY')            AS year,
                        1                                               AS nb_situations,
                        COALESCE(sit.net_a_payer, 0.0)                 AS montant_situation_ht_total,
                        0                                               AS nb_decomptes,
                        0.0                                             AS net_a_regler_total,
                        CASE WHEN sit.delai_depasse THEN 1 ELSE 0 END  AS nb_delais_depasses,
                        sit.company_id                                  AS company_id
                    FROM telecom_situation sit
                    LEFT JOIN project_project pp ON pp.id = sit.project_id
                    WHERE sit.state NOT IN ('annule', 'brouillon')

                    UNION ALL

                    SELECT
                        -- Decomptes rows: use negative id to avoid collision
                        -dec.id                                         AS id,
                        dec.project_id                                  AS project_id,
                        pp2.name                                        AS project_name,
                        pp2.partner_id                                  AS client_id,
                        to_char(dec.date_decompte, 'YYYY-MM')          AS month,
                        to_char(dec.date_decompte, 'YYYY')             AS year,
                        0                                               AS nb_situations,
                        0.0                                             AS montant_situation_ht_total,
                        1                                               AS nb_decomptes,
                        COALESCE(dec.net_a_regler, 0.0)                AS net_a_regler_total,
                        CASE WHEN dec.delai_depasse THEN 1 ELSE 0 END  AS nb_delais_depasses,
                        dec.company_id                                  AS company_id
                    FROM telecom_decompte dec
                    LEFT JOIN project_project pp2 ON pp2.id = dec.project_id
                    WHERE dec.state NOT IN ('annule', 'brouillon')
                )
            """)
            self._cr.execute("RELEASE SAVEPOINT report_finance_view")
        except Exception as exc:
            # Source tables from telecom_finance_ma may not exist yet.
            # Roll back to the savepoint so the transaction stays valid,
            # log a warning, and continue — the view will be (re)created
            # when telecom_finance_ma is properly installed and this module
            # is upgraded.
            self._cr.execute("ROLLBACK TO SAVEPOINT report_finance_view")
            _logger.warning(
                "report.telecom.finance.analysis: could not create SQL view "
                "(telecom_finance_ma tables may be missing). "
                "Error: %s", exc
            )
