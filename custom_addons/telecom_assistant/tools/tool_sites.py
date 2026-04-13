# -*- coding: utf-8 -*-
"""Tools: Sites telecom."""
from odoo.addons.telecom_assistant.models.assistant_tool_registry import register_tool


def get_sites(env, name=None, code=None, wilaya=None, state=None, limit=20):
    """Search telecom sites."""
    Site = env.get('telecom.site')
    if Site is None:
        return {'count': 0, 'sites': [], 'info': 'Module site non installé'}
    domain = []
    if name:
        domain.append(('name', 'ilike', name))
    if code:
        domain.append(('code_interne', 'ilike', code))
    if wilaya:
        domain.append(('wilaya', 'ilike', wilaya))
    if state:
        domain.append(('state', '=', state))

    sites = Site.search(domain, limit=limit)
    result = []
    for s in sites:
        result.append({
            'id': s.id,
            'code': s.code_interne,
            'name': s.name,
            'type': s.site_type,
            'state': s.state,
            'wilaya': s.wilaya,
            'gps': {'lat': s.gps_lat, 'lng': s.gps_lng} if s.gps_lat else None,
            'bailleur': s.bailleur_id.name if s.bailleur_id else None,
            'intervention_count': s.intervention_count,
        })
    return {'count': len(result), 'sites': result}


register_tool(
    'get_sites',
    get_sites,
    "Rechercher des sites télécom par nom, code, région ou état.",
    {
        'type': 'object',
        'properties': {
            'name': {'type': 'string', 'description': 'Nom ou partie du nom du site'},
            'code': {'type': 'string', 'description': 'Code interne du site'},
            'wilaya': {'type': 'string', 'description': 'Région / wilaya'},
            'state': {'type': 'string', 'enum': ['prospection', 'etude', 'autorisation', 'deploiement', 'livre', 'maintenance', 'desactive']},
            'limit': {'type': 'integer', 'default': 20},
        },
    }
)
