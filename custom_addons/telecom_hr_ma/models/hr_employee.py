# -*- coding: utf-8 -*-
"""
hr_employee.py
==============
Extends hr.employee with Moroccan telecom-specific fields:
- Terrain profile (specialties, level, zone)
- Safety habilitations and EPI tracking (via smart buttons)
- Moroccan payroll identifiers (CIN, CNSS, AMO, CIMR)
"""

from datetime import date, timedelta
from odoo import api, fields, models

# Moroccan regions (12 wilayas) — same list as telecom_site
WILAYA_SELECTION = [
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
]


class HrEmployee(models.Model):
    """Extend hr.employee with telecom terrain + Moroccan payroll fields."""

    _inherit = 'hr.employee'

    # ------------------------------------------------------------------
    # Terrain profile
    # ------------------------------------------------------------------

    telecom_technicien = fields.Boolean(
        string='Technicien terrain',
        default=False,
        help='Cocher si cet employé est un technicien terrain TelecomERP.',
        tracking=True,
    )

    specialite_ids = fields.Many2many(
        comodel_name='telecom.specialite',
        relation='hr_employee_specialite_rel',
        column1='employee_id',
        column2='specialite_id',
        string='Spécialités techniques',
    )

    niveau_technicien = fields.Selection(
        selection=[
            ('junior', 'Junior'),
            ('confirme', 'Confirmé'),
            ('senior', 'Senior'),
            ('expert', 'Expert'),
        ],
        string='Niveau technicien',
        tracking=True,
    )

    zone_intervention = fields.Selection(
        selection=WILAYA_SELECTION,
        string="Zone d'intervention",
        help='Région principale d\'affectation du technicien.',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Relations (One2many) — defined in habilitation/epi models
    # ------------------------------------------------------------------

    habilitation_ids = fields.One2many(
        comodel_name='telecom.habilitation.employee',
        inverse_name='employee_id',
        string='Habilitations',
    )

    epi_dotation_ids = fields.One2many(
        comodel_name='telecom.epi.dotation',
        inverse_name='employee_id',
        string='Dotations EPI',
    )

    # ------------------------------------------------------------------
    # Computed counters / indicators
    # ------------------------------------------------------------------

    habilitation_count = fields.Integer(
        string='Habilitations',
        compute='_compute_habilitation_count',
    )

    epi_count = fields.Integer(
        string='EPI',
        compute='_compute_epi_count',
    )

    habilitations_expiring = fields.Boolean(
        string='Habilitations expirant bientôt',
        compute='_compute_habilitations_expiring',
        store=True,
        help='Vrai si une habilitation expire dans les 60 jours.',
    )

    @api.depends('habilitation_ids')
    def _compute_habilitation_count(self):
        for emp in self:
            emp.habilitation_count = len(emp.habilitation_ids)

    @api.depends('epi_dotation_ids')
    def _compute_epi_count(self):
        for emp in self:
            emp.epi_count = len(emp.epi_dotation_ids)

    @api.depends('habilitation_ids.state')
    def _compute_habilitations_expiring(self):
        for emp in self:
            emp.habilitations_expiring = any(
                h.state in ('expiring_soon', 'expired')
                for h in emp.habilitation_ids
            )

    # ------------------------------------------------------------------
    # Moroccan payroll identifiers
    # ------------------------------------------------------------------

    cin = fields.Char(
        string='CIN',
        help='Carte Identité Nationale marocaine.',
    )

    cnss_number = fields.Char(
        string='N° CNSS',
        help='Numéro d\'immatriculation CNSS de l\'employé.',
    )

    amo_number = fields.Char(
        string='N° AMO',
        help='Numéro AMO (Assurance Maladie Obligatoire).',
    )

    cimr_taux = fields.Float(
        string='Taux CIMR salarié (%)',
        digits=(5, 2),
        default=0.0,
        help='Taux de cotisation CIMR salarié en pourcentage (ex: 3.0 pour 3%).',
    )

    cimr_taux_patronal = fields.Float(
        string='Taux CIMR patronal (%)',
        digits=(5, 2),
        default=0.0,
        help='Taux de cotisation CIMR employeur en pourcentage.',
    )

    nbr_parts_ir = fields.Float(
        string='Parts IR (charges de famille)',
        digits=(3, 1),
        default=1.0,
        help='Nombre de parts IR : 1 = célibataire, +0.5 par enfant à charge (max déduction = 360 MAD/mois).',
    )
