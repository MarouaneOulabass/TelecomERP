# -*- coding: utf-8 -*-
"""Telecom dunning / reminder model."""

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

RELANCE_LEVELS = [
    ('relance_1', _('Relance amiable (niveau 1)')),
    ('relance_2', _('Relance formelle (niveau 2)')),
    ('mise_en_demeure', _('Mise en demeure')),
]

RELANCE_MODES = [
    ('email', _('E-mail')),
    ('courrier', _('Courrier')),
    ('telephone', _('Téléphone')),
]

RELANCE_STATES = [
    ('draft', _('Brouillon')),
    ('sent', _('Envoyée')),
]


class TelecomRelance(models.Model):
    """Dunning / payment reminder linked to an overdue invoice."""

    _name = 'telecom.relance'
    _description = 'Relance de paiement'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Facture',
        required=True,
        ondelete='cascade',
        domain="[('move_type', 'in', ['out_invoice', 'out_refund']), ('state', '=', 'posted')]",
        tracking=True,
        help="Facture client concernée par la relance.",
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Client',
        related='invoice_id.partner_id',
        store=True,
        readonly=True,
    )

    date = fields.Date(
        string='Date de relance',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    level = fields.Selection(
        selection=RELANCE_LEVELS,
        string='Niveau',
        required=True,
        default='relance_1',
        tracking=True,
        help=(
            "Niveau de la relance :\n"
            "- Relance amiable : premier rappel courtois\n"
            "- Relance formelle : rappel avec mise en garde\n"
            "- Mise en demeure : dernière relance avant action juridique"
        ),
    )

    mode = fields.Selection(
        selection=RELANCE_MODES,
        string='Mode d\'envoi',
        required=True,
        default='email',
        tracking=True,
    )

    notes = fields.Text(
        string='Notes',
        help="Observations complémentaires sur la relance.",
    )

    state = fields.Selection(
        selection=RELANCE_STATES,
        string='État',
        default='draft',
        required=True,
        tracking=True,
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Devise',
        related='invoice_id.currency_id',
        store=True,
        readonly=True,
    )

    amount_residual = fields.Monetary(
        string='Montant restant dû',
        related='invoice_id.amount_residual',
        store=True,
        readonly=True,
        currency_field='currency_id',
    )

    # -- Actions ---------------------------------------------------------------

    def action_send(self):
        """Mark the relance as sent and update the parent invoice counters."""
        for relance in self:
            if relance.state == 'sent':
                raise UserError(_("Cette relance a déjà été envoyée."))
            relance.state = 'sent'
            invoice = relance.invoice_id
            invoice.relance_count = len(
                invoice.relance_ids.filtered(lambda r: r.state == 'sent')
            )
            invoice.last_relance_date = relance.date

    def action_reset_draft(self):
        """Reset relance to draft state."""
        for relance in self:
            relance.state = 'draft'
