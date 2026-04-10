# -*- coding: utf-8 -*-
"""
damancom_export.py
==================
Wizard that generates a CSV file compatible with the CNSS DAMANCOM platform.

Queries all telecom.paie.bulletin records for a given month/year and produces
a CSV with columns:
  N_CNSS, Nom, Prenom, Salaire_Brut, Jours_Travailles, CNSS_Salarie, CNSS_Patronal
"""

import base64
import csv
import io
from datetime import date
import calendar

from odoo import api, fields, models
from odoo.exceptions import UserError


MONTH_SELECTION = [
    ('1', 'Janvier'), ('2', 'Février'), ('3', 'Mars'),
    ('4', 'Avril'), ('5', 'Mai'), ('6', 'Juin'),
    ('7', 'Juillet'), ('8', 'Août'), ('9', 'Septembre'),
    ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre'),
]


class DamancomExportWizard(models.TransientModel):
    """Wizard to export CNSS DAMANCOM CSV file."""

    _name = 'telecom.damancom.export.wizard'
    _description = 'Export DAMANCOM CNSS'

    mois = fields.Selection(
        selection=MONTH_SELECTION,
        string='Mois',
        required=True,
        default=lambda self: str(date.today().month),
    )

    annee = fields.Integer(
        string='Année',
        required=True,
        default=lambda self: date.today().year,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Société',
        default=lambda self: self.env.company,
        required=True,
    )

    # Output fields
    file_data = fields.Binary(
        string='Fichier DAMANCOM',
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
        """Generate DAMANCOM CSV from payslips of the selected period."""
        self.ensure_one()

        month = int(self.mois)
        year = self.annee

        # Compute period boundaries
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        # Search validated/paid payslips in the period
        bulletins = self.env['telecom.paie.bulletin'].search([
            ('date_from', '>=', first_day),
            ('date_from', '<=', last_day),
            ('state', 'in', ['confirme', 'valide', 'paye']),
            ('company_id', '=', self.company_id.id),
        ], order='employee_id')

        if not bulletins:
            raise UserError(
                f"Aucun bulletin de paie trouvé pour la période "
                f"{dict(MONTH_SELECTION).get(self.mois)} {year}."
            )

        # Generate CSV content
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # Header row
        writer.writerow([
            'N_CNSS',
            'Nom',
            'Prenom',
            'Salaire_Brut',
            'Jours_Travailles',
            'CNSS_Salarie',
            'CNSS_Patronal',
        ])

        for bulletin in bulletins:
            emp = bulletin.employee_id
            # Split employee name into nom/prenom (best effort)
            name_parts = (emp.name or '').strip().split(' ', 1)
            nom = name_parts[0] if name_parts else ''
            prenom = name_parts[1] if len(name_parts) > 1 else ''

            writer.writerow([
                emp.cnss_number or '',
                nom,
                prenom,
                f"{bulletin.salaire_base:.2f}",
                f"{bulletin.nbr_jours_travailles:.0f}",
                f"{bulletin.cnss_salarie:.2f}",
                f"{bulletin.cnss_patronal:.2f}",
            ])

        csv_content = output.getvalue()
        output.close()

        # Encode to base64 for Binary field
        file_data = base64.b64encode(csv_content.encode('utf-8'))
        month_label = dict(MONTH_SELECTION).get(self.mois, self.mois)
        file_name = f"DAMANCOM_{year}_{month:02d}.csv"

        self.write({
            'file_data': file_data,
            'file_name': file_name,
            'state': 'done',
        })

        # Return the same wizard so the user sees the download button
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
