from odoo import api, fields, models


class AccountMove(models.Model):
    """Extend account.move with Moroccan legal fields and RAS (Retenue à la Source) logic."""

    _inherit = 'account.move'

    # ── RAS — Retenue à la Source ──────────────────────────────────────────

    ras_applicable = fields.Boolean(
        string='RAS applicable',
        default=False,
        help=(
            "Cocher si la retenue à la source (RAS) de 10 % s'applique à cette facture "
            "(prestations de services soumises à la RAS au Maroc)."
        ),
    )
    ras_amount = fields.Monetary(
        string='Montant RAS (10 %)',
        compute='_compute_ras_amount',
        store=True,
        currency_field='currency_id',
        help="Montant de la retenue à la source calculé à 10 % du total HT.",
    )
    ras_certificate_number = fields.Char(
        string='N° certificat de retenue',
        help="Numéro du certificat de retenue à la source délivré par le client.",
    )

    # ── Moroccan legal mentions (read from partner) ────────────────────────

    ice_client = fields.Char(
        string='ICE client',
        related='partner_id.ice',
        store=True,
        readonly=True,
        help="Identifiant Commun de l'Entreprise du client (affiché sur la facture).",
    )
    if_client = fields.Char(
        string='IF client',
        related='partner_id.if_number',
        store=True,
        readonly=True,
        help="Identifiant Fiscal (IF) du client.",
    )
    rc_client = fields.Char(
        string='RC client',
        related='partner_id.rc_number',
        store=True,
        readonly=True,
        help="Registre de Commerce (RC) du client.",
    )
    invoice_legal_mentions = fields.Text(
        string='Mentions légales',
        compute='_compute_invoice_legal_mentions',
        store=True,
        help="Mentions légales obligatoires à imprimer sur la facture (ICE, IF, RC, Patente, Capital social).",
    )

    # ── Computed fields ────────────────────────────────────────────────────

    @api.depends('ras_applicable', 'amount_untaxed')
    def _compute_ras_amount(self):
        """Compute RAS = 10 % of the untaxed amount when RAS is applicable."""
        for move in self:
            if move.ras_applicable and move.amount_untaxed:
                move.ras_amount = move.amount_untaxed * 0.10
            else:
                move.ras_amount = 0.0

    @api.depends(
        'partner_id',
        'partner_id.ice',
        'partner_id.if_number',
        'partner_id.rc_number',
        'partner_id.patente',
        'partner_id.capital_social',
        'partner_id.forme_juridique',
    )
    def _compute_invoice_legal_mentions(self):
        """Build the full legal mentions string from partner data."""
        forme_label = dict(
            self.env['res.partner'].fields_get(
                allfields=['forme_juridique']
            )['forme_juridique']['selection']
        )
        for move in self:
            partner = move.partner_id
            if not partner:
                move.invoice_legal_mentions = ''
                continue

            parts = []

            # Legal form and capital
            forme = forme_label.get(partner.forme_juridique or '', '')
            if forme:
                parts.append(forme)
            if partner.capital_social:
                currency_symbol = 'MAD'
                if (
                    hasattr(partner, 'capital_currency_id')
                    and partner.capital_currency_id
                ):
                    currency_symbol = partner.capital_currency_id.name or 'MAD'
                parts.append(
                    "Capital social : {:,.2f} {}".format(
                        partner.capital_social, currency_symbol
                    )
                )

            # Moroccan identifiers
            if partner.ice:
                parts.append("ICE : {}".format(partner.ice))
            if partner.if_number:
                parts.append("IF : {}".format(partner.if_number))
            if partner.rc_number:
                parts.append("RC : {}".format(partner.rc_number))
            if partner.patente:
                parts.append("Patente : {}".format(partner.patente))

            move.invoice_legal_mentions = " | ".join(parts) if parts else ''

    # ── Onchange helpers ───────────────────────────────────────────────────

    @api.onchange('partner_id')
    def _onchange_partner_id_ras(self):
        """Auto-suggest RAS when partner type is subcontractor (sous-traitant) or service provider."""
        if self.partner_id and self.partner_id.partner_type in ('subcontractor', 'other'):
            # Suggest RAS for service-type partners; the user can override
            self.ras_applicable = True
        elif self.partner_id and self.partner_id.partner_type not in (False, None, ''):
            # Known non-service types: operators, lessors, equipment suppliers
            if self.partner_id.partner_type in ('operator', 'lessor', 'supplier', 'public_org'):
                self.ras_applicable = False
