# -*- coding: utf-8 -*-
"""
account.move (inherit) — Moroccan finance extensions
=====================================================
Extends Odoo's account.move (invoice) with:

  - Links to telecom.situation and telecom.decompte
  - 60-day payment deadline tracking (loi 69-21)
  - Alert flag for invoices unpaid after 45 days
"""

from odoo import api, fields, models


class AccountMoveFinanceMA(models.Model):
    """Extend account.move with TelecomERP finance fields."""

    _inherit = 'account.move'

    # ------------------------------------------------------------------
    # Links to TelecomERP finance documents
    # ------------------------------------------------------------------

    situation_id = fields.Many2one(
        comodel_name='telecom.situation',
        string='Situation de travaux',
        copy=False,
        index=True,
        help="Situation de travaux à l'origine de cette facture.",
    )
    decompte_id = fields.Many2one(
        comodel_name='telecom.decompte',
        string='Décompte',
        copy=False,
        index=True,
        help="Décompte de travaux à l'origine de cette facture.",
    )

    # ------------------------------------------------------------------
    # Payment deadline monitoring — loi 69-21
    # ------------------------------------------------------------------

    delai_paiement_legal = fields.Integer(
        string='Jours restants (60j)',
        compute='_compute_delai_paiement_legal',
        help="Nombre de jours restants avant dépassement du délai légal de 60 jours.",
    )
    alerte_delai_paiement = fields.Boolean(
        string='Alerte délai paiement',
        compute='_compute_alerte_delai_paiement',
        store=True,
        help="True si la facture est impayée depuis plus de 45 jours (alerte préventive).",
    )

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------

    @api.depends('invoice_date', 'payment_state', 'move_type')
    def _compute_delai_paiement_legal(self):
        """
        Remaining days before the 60-day legal payment deadline.
        Applicable only to posted customer invoices (out_invoice).
        Returns 0 when already paid or not applicable.
        """
        today = fields.Date.today()
        for move in self:
            if (
                move.move_type == 'out_invoice'
                and move.state == 'posted'
                and move.payment_state not in ('paid', 'in_payment', 'reversed')
                and move.invoice_date
            ):
                elapsed = (today - move.invoice_date).days
                move.delai_paiement_legal = max(0, 60 - elapsed)
            else:
                move.delai_paiement_legal = 0

    @api.depends('invoice_date', 'payment_state', 'move_type', 'state')
    def _compute_alerte_delai_paiement(self):
        """
        Flag invoices posted > 45 days ago and still unpaid.
        Provides a 15-day advance warning before the legal 60-day deadline.
        """
        today = fields.Date.today()
        for move in self:
            if (
                move.move_type == 'out_invoice'
                and move.state == 'posted'
                and move.payment_state not in ('paid', 'in_payment', 'reversed')
                and move.invoice_date
            ):
                elapsed = (today - move.invoice_date).days
                move.alerte_delai_paiement = elapsed > 45
            else:
                move.alerte_delai_paiement = False
