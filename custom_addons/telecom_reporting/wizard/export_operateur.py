# -*- coding: utf-8 -*-
"""
export_operateur.py
===================
Wizard that exports intervention data in CSV format suitable for telecom
operators (Maroc Telecom, Orange, Inwi).

Output columns:
  Code_Site, Date_Intervention, Type, Duree_Heures, Statut, Technicien
"""

import base64
import csv
import io

from odoo import api, fields, models
from odoo.exceptions import UserError


class ExportOperateurWizard(models.TransientModel):
    """Wizard to export interventions in operator-compatible CSV format."""

    _name = 'telecom.export.operateur.wizard'
    _description = 'Export interventions format opérateur'

    date_from = fields.Date(
        string='Date début',
        required=True,
    )

    date_to = fields.Date(
        string='Date fin',
        required=True,
    )

    operateur_id = fields.Many2one(
        comodel_name='res.partner',
        string='Opérateur',
        domain="[('partner_type', '=', 'operator')]",
        help='Filtrer par opérateur. Laisser vide pour tous les opérateurs.',
    )

    format_export = fields.Selection(
        selection=[
            ('csv', 'CSV (séparateur point-virgule)'),
        ],
        string='Format',
        default='csv',
        required=True,
    )

    # Output fields
    file_data = fields.Binary(
        string='Fichier export',
        readonly=True,
    )

    file_name = fields.Char(
        string='Nom du fichier',
        readonly=True,
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Paramètres'),
            ('done', 'Téléchargement'),
        ],
        default='draft',
    )

    def action_generate(self):
        """Generate the operator export file."""
        self.ensure_one()

        if self.date_to < self.date_from:
            raise UserError("La date de fin doit être postérieure à la date de début.")

        # Build search domain
        domain = [
            ('date_planifiee', '>=', self.date_from),
            ('date_planifiee', '<=', self.date_to),
        ]
        if self.operateur_id:
            domain.append(('operateur_id', '=', self.operateur_id.id))

        interventions = self.env['telecom.intervention'].search(
            domain, order='date_planifiee asc'
        )

        if not interventions:
            raise UserError(
                "Aucune intervention trouvée pour la période et l'opérateur sélectionnés."
            )

        # State label mapping
        state_labels = dict(
            self.env['telecom.intervention']._fields['state'].selection
        )
        type_labels = dict(
            self.env['telecom.intervention']._fields['intervention_type'].selection
        )

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # Header
        writer.writerow([
            'Code_Site',
            'Nom_Site',
            'Date_Intervention',
            'Type',
            'Duree_Heures',
            'Statut',
            'Technicien',
            'Operateur',
        ])

        for interv in interventions:
            # Get site code
            site_code = ''
            if interv.site_id:
                site_code = interv.site_id.code_operateur or interv.site_id.name or ''

            site_name = interv.site_id.name if interv.site_id else ''

            # Date
            date_str = ''
            if interv.date_planifiee:
                date_str = interv.date_planifiee.strftime('%d/%m/%Y')

            # Type label
            type_label = type_labels.get(interv.intervention_type, interv.intervention_type or '')

            # Duration
            duree = f"{interv.duree_estimee:.2f}" if interv.duree_estimee else '0.00'

            # State label
            state_label = state_labels.get(interv.state, interv.state or '')

            # Technicians (comma-separated)
            technicians = ', '.join(interv.technician_ids.mapped('name'))

            # Operator
            operateur_name = interv.operateur_id.name if interv.operateur_id else ''

            writer.writerow([
                site_code,
                site_name,
                date_str,
                type_label,
                duree,
                state_label,
                technicians,
                operateur_name,
            ])

        csv_content = output.getvalue()
        output.close()

        file_data = base64.b64encode(csv_content.encode('utf-8'))
        op_name = self.operateur_id.name if self.operateur_id else 'Tous'
        file_name = (
            f"Export_Interventions_{op_name}_"
            f"{self.date_from.strftime('%Y%m%d')}_"
            f"{self.date_to.strftime('%Y%m%d')}.csv"
        )

        self.write({
            'file_data': file_data,
            'file_name': file_name,
            'state': 'done',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
