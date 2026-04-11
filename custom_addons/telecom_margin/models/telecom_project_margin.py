# -*- coding: utf-8 -*-
"""
Cockpit de rentabilité — Vue SQL agrégée
==========================================
Vue read-only qui calcule la marge par projet et par lot
en temps réel depuis les coûts saisis et le budget prévisionnel.
"""
from odoo import api, fields, models, tools


class TelecomProjectMargin(models.Model):
    """SQL view: real-time margin per project and lot."""

    _name = 'telecom.project.margin'
    _description = 'Marge projet (cockpit rentabilité)'
    _auto = False
    _order = 'project_id, lot_id'

    project_id = fields.Many2one('project.project', string='Projet', readonly=True)
    lot_id = fields.Many2one('telecom.lot', string='Lot', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Client', readonly=True)

    # Budget
    budget_prevu = fields.Float(string='Budget prévisionnel HT', readonly=True)

    # Costs
    cout_total = fields.Float(string='Coûts engagés HT', readonly=True)
    cout_main_oeuvre = fields.Float(string="Main d'oeuvre", readonly=True)
    cout_materiel = fields.Float(string='Matériel', readonly=True)
    cout_sous_traitance = fields.Float(string='Sous-traitance', readonly=True)
    cout_carburant = fields.Float(string='Carburant', readonly=True)
    cout_autres = fields.Float(string='Autres coûts', readonly=True)
    nb_cost_entries = fields.Integer(string='Nb saisies', readonly=True)
    nb_task_missing = fields.Integer(string='Sans tâche', readonly=True)

    # Revenue (from situations de travaux)
    revenu_facture = fields.Float(string='Revenus facturés HT', readonly=True)

    # Margin
    marge_absolue = fields.Float(string='Marge (MAD)', readonly=True)
    marge_pct = fields.Float(string='Marge (%)', readonly=True)

    # Health
    health = fields.Selection([
        ('green', 'Sain (> 15%)'),
        ('yellow', 'Attention (5-15%)'),
        ('red', 'Critique (< 5%)'),
        ('unknown', 'Pas de budget'),
    ], string='Santé', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # SQL direct : create/replace the SQL view backing this read-only model (_auto = False)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    p.id AS project_id,
                    l.id AS lot_id,
                    p.partner_id AS partner_id,

                    -- Budget: montant_total from linked contract (first found)
                    COALESCE(
                        (SELECT c.montant_total
                         FROM telecom_contract c
                         JOIN telecom_decompte d ON d.contract_id = c.id
                         WHERE d.project_id = p.id
                         LIMIT 1),
                        0
                    ) AS budget_prevu,

                    -- Costs by category
                    COALESCE(SUM(ce.amount), 0) AS cout_total,
                    COALESCE(SUM(CASE WHEN ct.category = 'main_oeuvre' THEN ce.amount ELSE 0 END), 0) AS cout_main_oeuvre,
                    COALESCE(SUM(CASE WHEN ct.category = 'materiel' THEN ce.amount ELSE 0 END), 0) AS cout_materiel,
                    COALESCE(SUM(CASE WHEN ct.category = 'sous_traitance' THEN ce.amount ELSE 0 END), 0) AS cout_sous_traitance,
                    COALESCE(SUM(CASE WHEN ct.category = 'carburant' THEN ce.amount ELSE 0 END), 0) AS cout_carburant,
                    COALESCE(SUM(CASE WHEN ct.category NOT IN ('main_oeuvre','materiel','sous_traitance','carburant') THEN ce.amount ELSE 0 END), 0) AS cout_autres,
                    COUNT(ce.id) AS nb_cost_entries,
                    COALESCE(SUM(CASE WHEN ce.task_id IS NULL THEN 1 ELSE 0 END), 0) AS nb_task_missing,

                    -- Revenue from situations
                    COALESCE(
                        (SELECT SUM(s.montant_situation_ht)
                         FROM telecom_situation s
                         WHERE s.project_id = p.id AND s.state IN ('facture','paye')),
                        0
                    ) AS revenu_facture,

                    -- Margin
                    COALESCE(
                        (SELECT SUM(s.montant_situation_ht)
                         FROM telecom_situation s
                         WHERE s.project_id = p.id AND s.state IN ('facture','paye')),
                        0
                    ) - COALESCE(SUM(ce.amount), 0) AS marge_absolue,

                    CASE
                        WHEN COALESCE(
                            (SELECT SUM(s.montant_situation_ht)
                             FROM telecom_situation s
                             WHERE s.project_id = p.id AND s.state IN ('facture','paye')),
                            0
                        ) > 0 THEN
                            ROUND((
                                COALESCE(
                                    (SELECT SUM(s.montant_situation_ht)
                                     FROM telecom_situation s
                                     WHERE s.project_id = p.id AND s.state IN ('facture','paye')),
                                    0
                                ) - COALESCE(SUM(ce.amount), 0)
                            ) / NULLIF(
                                COALESCE(
                                    (SELECT SUM(s.montant_situation_ht)
                                     FROM telecom_situation s
                                     WHERE s.project_id = p.id AND s.state IN ('facture','paye')),
                                    0
                                ), 0
                            ) * 100, 1)
                        ELSE 0
                    END AS marge_pct,

                    CASE
                        WHEN COALESCE(
                            (SELECT c.montant_total
                             FROM telecom_contract c
                             JOIN telecom_decompte d ON d.contract_id = c.id
                             WHERE d.project_id = p.id
                             LIMIT 1),
                            0
                        ) = 0 THEN 'unknown'
                        WHEN (
                            COALESCE(
                                (SELECT SUM(s.montant_situation_ht)
                                 FROM telecom_situation s
                                 WHERE s.project_id = p.id AND s.state IN ('facture','paye')),
                                0
                            ) - COALESCE(SUM(ce.amount), 0)
                        ) / NULLIF(
                            COALESCE(
                                (SELECT c.montant_total
                                 FROM telecom_contract c
                                 JOIN telecom_decompte d ON d.contract_id = c.id
                                 WHERE d.project_id = p.id
                                 LIMIT 1),
                                0
                            ), 0
                        ) * 100 > 15 THEN 'green'
                        WHEN (
                            COALESCE(
                                (SELECT SUM(s.montant_situation_ht)
                                 FROM telecom_situation s
                                 WHERE s.project_id = p.id AND s.state IN ('facture','paye')),
                                0
                            ) - COALESCE(SUM(ce.amount), 0)
                        ) / NULLIF(
                            COALESCE(
                                (SELECT c.montant_total
                                 FROM telecom_contract c
                                 JOIN telecom_decompte d ON d.contract_id = c.id
                                 WHERE d.project_id = p.id
                                 LIMIT 1),
                                0
                            ), 0
                        ) * 100 >= 5 THEN 'yellow'
                        ELSE 'red'
                    END AS health

                FROM project_project p
                LEFT JOIN telecom_lot l ON l.project_id = p.id
                LEFT JOIN telecom_cost_entry ce ON ce.project_id = p.id
                    AND (ce.lot_id = l.id OR l.id IS NULL)
                LEFT JOIN telecom_cost_type ct ON ct.id = ce.cost_type_id
                GROUP BY p.id, l.id, p.partner_id
            )
        """)

    def action_open_costs(self):
        self.ensure_one()
        domain = [('project_id', '=', self.project_id.id)]
        if self.lot_id:
            domain.append(('lot_id', '=', self.lot_id.id))
        return {
            'type': 'ir.actions.act_window',
            'name': f'Coûts — {self.project_id.name}',
            'res_model': 'telecom.cost.entry',
            'view_mode': 'tree,form,pivot',
            'domain': domain,
        }
