# -*- coding: utf-8 -*-
"""Tools: Interventions terrain."""
from odoo.addons.telecom_assistant.models.assistant_tool_registry import register_tool


def get_interventions(env, site_name=None, technician_name=None, status=None, date_from=None, date_to=None, limit=20):
    """Get field interventions filtered by various criteria."""
    domain = [('active', '=', True)]
    if site_name:
        sites = env['telecom.site'].search([('name', 'ilike', site_name)])
        domain.append(('site_id', 'in', sites.ids))
    if technician_name:
        techs = env['hr.employee'].search([('name', 'ilike', technician_name)])
        domain.append(('technician_ids', 'in', techs.ids))
    if status:
        domain.append(('state', '=', status))
    if date_from:
        domain.append(('date_planifiee', '>=', date_from))
    if date_to:
        domain.append(('date_planifiee', '<=', date_to))

    interventions = env['telecom.intervention'].search(domain, order='date_planifiee desc', limit=limit)
    result = []
    for bi in interventions:
        result.append({
            'id': bi.id,
            'reference': bi.name,
            'type': bi.intervention_type,
            'site': bi.site_id.name if bi.site_id else None,
            'site_code': bi.site_id.code_interne if bi.site_id else None,
            'status': bi.state,
            'planned_date': str(bi.date_planifiee) if bi.date_planifiee else None,
            'duration_hours': bi.duree_reelle or 0,
            'technicians': [t.name for t in bi.technician_ids],
            'sla_exceeded': bi.sla_depasse,
            'description': (bi.description_travaux or '')[:200],
        })
    return {'count': len(result), 'interventions': result}


register_tool(
    'get_interventions',
    get_interventions,
    "Rechercher des bons d'intervention par site, technicien, statut ou date.",
    {
        'type': 'object',
        'properties': {
            'site_name': {'type': 'string', 'description': 'Nom ou code du site'},
            'technician_name': {'type': 'string', 'description': 'Nom du technicien'},
            'status': {'type': 'string', 'enum': ['draft', 'planifie', 'en_cours', 'termine', 'valide', 'facture', 'annule']},
            'date_from': {'type': 'string', 'description': 'Date début (YYYY-MM-DD)'},
            'date_to': {'type': 'string', 'description': 'Date fin (YYYY-MM-DD)'},
            'limit': {'type': 'integer', 'description': 'Nombre max de résultats', 'default': 20},
        },
    }
)
