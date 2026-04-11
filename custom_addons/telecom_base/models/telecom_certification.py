from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class TelecomCertification(models.Model):
    """
    Certifications and accreditations for partners (subcontractors, suppliers).
    E.g.: ANRT approval, ONEE qualification, ISO 9001, etc.
    """
    _name = 'telecom.certification'
    _description = 'Certification / Agrément partenaire'
    _order = 'date_expiration asc, name'
    _rec_name = 'name'

    partner_id = fields.Many2one(
        'res.partner',
        string='Partenaire',
        required=True,
        ondelete='cascade',
        index=True,
    )
    name = fields.Char(string='Certification', required=True)
    certification_type = fields.Selection(
        selection=[
            ('anrt', 'Agrément ANRT'),
            ('onee', 'Qualification ONEE'),
            ('iso_9001', 'ISO 9001'),
            ('iso_14001', 'ISO 14001'),
            ('iso_45001', 'ISO 45001'),
            ('qualibat', 'Qualibat'),
            ('other', 'Autre'),
        ],
        string='Type',
        required=True,
        default='other',
    )
    reference = fields.Char(string='Référence / N° certificat')
    date_obtention = fields.Date(string="Date d'obtention")
    date_expiration = fields.Date(string="Date d'expiration")
    organisme = fields.Char(string='Organisme certificateur')
    document = fields.Binary(string='Document (PDF/scan)')
    document_filename = fields.Char()
    notes = fields.Text(string='Observations')
    state = fields.Selection(
        selection=[
            ('valid', 'Valide'),
            ('expiring_soon', 'Expire bientôt'),
            ('expired', 'Expiré'),
        ],
        string='Statut',
        compute='_compute_state',
        store=True,
    )

    @api.depends('date_expiration')
    def _compute_state(self):
        today = date.today()
        for rec in self:
            if not rec.date_expiration:
                rec.state = 'valid'
            elif rec.date_expiration < today:
                rec.state = 'expired'
            elif (rec.date_expiration - today).days <= 60:
                rec.state = 'expiring_soon'
            else:
                rec.state = 'valid'

    @api.constrains('date_obtention', 'date_expiration')
    def _check_dates(self):
        for rec in self:
            if rec.date_obtention and rec.date_expiration:
                if rec.date_expiration < rec.date_obtention:
                    raise ValidationError(
                        _("La date d'expiration doit être postérieure à la date d'obtention.")
                    )
