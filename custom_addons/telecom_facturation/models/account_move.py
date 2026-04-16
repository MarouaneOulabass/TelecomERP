# -*- coding: utf-8 -*-
"""Extend account.move with telecom-specific invoicing fields."""

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

TELECOM_INVOICE_TYPES = [
    ('standard', _('Standard')),
    ('situation', _('Situation de travaux')),
    ('decompte', _('Décompte')),
    ('avoir', _('Avoir')),
]


class AccountMove(models.Model):
    """Extend account.move with telecom project linkage and payment delay tracking."""

    _inherit = 'account.move'

    # -- Telecom project linkage -----------------------------------------------

    telecom_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Projet télécom',
        tracking=True,
        help="Projet télécom principal associé à cette facture.",
    )

    telecom_type = fields.Selection(
        selection=TELECOM_INVOICE_TYPES,
        string='Type facturation télécom',
        default='standard',
        tracking=True,
        help=(
            "Type de facturation télécom :\n"
            "- Standard : facture classique\n"
            "- Situation de travaux : facturation progressive\n"
            "- Décompte : décompte marché public\n"
            "- Avoir : note de crédit"
        ),
    )

    # -- Payment delay tracking ------------------------------------------------

    payment_delay_days = fields.Integer(
        string='Retard paiement (jours)',
        compute='_compute_payment_delay',
        store=True,
        help="Nombre de jours depuis la date d'échéance de la facture.",
    )

    payment_delay_alert = fields.Boolean(
        string='Alerte délai paiement',
        compute='_compute_payment_delay',
        store=True,
        help="Vrai si le retard de paiement dépasse 60 jours (loi 69-21).",
    )

    # -- Relance tracking ------------------------------------------------------

    relance_count = fields.Integer(
        string='Nombre de relances',
        default=0,
        tracking=True,
        help="Nombre total de relances envoyées pour cette facture.",
    )

    last_relance_date = fields.Date(
        string='Dernière relance',
        tracking=True,
        help="Date de la dernière relance envoyée.",
    )

    relance_ids = fields.One2many(
        comodel_name='telecom.relance',
        inverse_name='invoice_id',
        string='Relances',
        help="Historique des relances pour cette facture.",
    )

    # -- Computed methods ------------------------------------------------------

    @api.depends('invoice_date_due', 'payment_state', 'state')
    def _compute_payment_delay(self):
        """Compute overdue days and alert flag (loi 69-21: 60 days max)."""
        today = fields.Date.context_today(self)
        for move in self:
            if (
                move.state == 'posted'
                and move.payment_state in ('not_paid', 'partial')
                and move.invoice_date_due
                and move.invoice_date_due < today
            ):
                delta = (today - move.invoice_date_due).days
                move.payment_delay_days = delta
                move.payment_delay_alert = delta > 60
            else:
                move.payment_delay_days = 0
                move.payment_delay_alert = False
