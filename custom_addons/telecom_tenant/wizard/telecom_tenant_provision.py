# -*- coding: utf-8 -*-
"""Quick provisioning wizard — create a tenant from YAML paste."""
import yaml
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TelecomTenantProvisionWizard(models.TransientModel):
    _name = 'telecom.tenant.provision.wizard'
    _description = 'Provisioning rapide tenant'

    yaml_content = fields.Text(
        string='Profil YAML',
        required=True,
        help='Collez le contenu du fichier tenant_profile.yaml ici.',
    )
    admin_password = fields.Char(
        string='Mot de passe admin',
        default='admin',
        required=True,
    )

    def action_provision_from_yaml(self):
        self.ensure_one()
        try:
            data = yaml.safe_load(self.yaml_content)
        except Exception as e:
            raise ValidationError(_('YAML invalide : %s') % str(e))

        if not data or not isinstance(data, dict):
            raise ValidationError(_('Le YAML doit être un dictionnaire.'))

        tenant_data = data.get('tenant', {})
        org_data = data.get('organization', {})
        caps_data = data.get('capabilities', {})

        if not tenant_data.get('name') or not tenant_data.get('subdomain'):
            raise ValidationError(_('Le YAML doit contenir tenant.name et tenant.subdomain.'))

        # Map capabilities to boolean fields
        enabled = caps_data.get('enabled', [])
        cap_map = {
            'telecom_site': 'cap_site',
            'telecom_intervention': 'cap_intervention',
            'telecom_hr_ma': 'cap_hr',
            'telecom_equipment': 'cap_equipment',
            'telecom_fleet': 'cap_fleet',
            'telecom_project': 'cap_project',
            'telecom_ao': 'cap_ao',
            'telecom_contract': 'cap_contract',
            'telecom_finance_ma': 'cap_finance',
            'telecom_cost': 'cap_cost',
            'telecom_reporting': 'cap_reporting',
        }

        vals = {
            'name': tenant_data['name'],
            'subdomain': tenant_data['subdomain'],
            'language': tenant_data.get('language', 'fr_FR'),
            'currency': tenant_data.get('currency', 'MAD'),
            'ice': org_data.get('ice', ''),
            'city': org_data.get('city', ''),
            'forme_juridique': org_data.get('forme_juridique', 'sarl'),
            'contact_name': org_data.get('contact_name', ''),
            'contact_email': org_data.get('contact_email', ''),
            'yaml_profile': self.yaml_content,
            'admin_password': self.admin_password,
        }

        for module, field in cap_map.items():
            vals[field] = module in enabled

        tenant = self.env['telecom.tenant'].create(vals)

        return {
            'type': 'ir.actions.act_window',
            'name': tenant.name,
            'res_model': 'telecom.tenant',
            'res_id': tenant.id,
            'view_mode': 'form',
        }
