# -*- coding: utf-8 -*-
"""Tools: HR, pointage, habilitations."""
from odoo.addons.telecom_assistant.models.assistant_tool_registry import register_tool


def get_pointages(env, site_name=None, employee_name=None, date=None, week=None):
    """Get field attendance records."""
    Pointage = env.get('telecom.pointage.chantier')
    if Pointage is None:
        return {'count': 0, 'pointages': [], 'info': 'Module pointage non installé'}
    domain = []
    if site_name:
        Site = env.get('telecom.site')
        if Site:
            sites = Site.search([('name', 'ilike', site_name)])
            domain.append(('site_id', 'in', sites.ids))
    if employee_name:
        Employee = env.get('hr.employee')
        if Employee:
            emps = Employee.search([('name', 'ilike', employee_name)])
            domain.append(('employee_id', 'in', emps.ids))
    if date:
        domain.append(('date', '=', date))
    if week:
        from datetime import datetime, timedelta
        d = datetime.strptime(week, '%Y-%W-%w') if '-' in week else datetime.now()
        start = d - timedelta(days=d.weekday())
        end = start + timedelta(days=6)
        domain.append(('date', '>=', start.strftime('%Y-%m-%d')))
        domain.append(('date', '<=', end.strftime('%Y-%m-%d')))

    records = Pointage.search(domain, order='date desc', limit=50)
    result = []
    for p in records:
        result.append({
            'date': str(p.date),
            'employee': p.employee_id.name,
            'site': p.site_id.name if p.site_id else None,
            'hours': p.duree_heures,
            'overtime': p.heures_supplementaires,
            'state': p.state,
        })
    return {'count': len(result), 'pointages': result}


def get_expiring_habilitations(env, days=60):
    """Get habilitations expiring soon or already expired."""
    Hab = env.get('telecom.habilitation.employee')
    if Hab is None:
        return {'count': 0, 'habilitations': [], 'info': 'Module habilitations non installé'}
    habs = Hab.search([
        ('state', 'in', ['expiring_soon', 'expired']),
    ])
    result = []
    for h in habs:
        result.append({
            'employee': h.employee_id.name,
            'type': h.habilitation_type_id.name,
            'expiration': str(h.date_expiration) if h.date_expiration else None,
            'state': h.state,
        })
    return {'count': len(result), 'habilitations': result}


register_tool(
    'get_pointages',
    get_pointages,
    "Obtenir les pointages chantier par site, employé ou date. Utile pour savoir qui était sur quel site.",
    {
        'type': 'object',
        'properties': {
            'site_name': {'type': 'string', 'description': 'Nom du site'},
            'employee_name': {'type': 'string', 'description': "Nom de l'employé"},
            'date': {'type': 'string', 'description': 'Date (YYYY-MM-DD)'},
            'week': {'type': 'string', 'description': 'Semaine (YYYY-WW)'},
        },
    }
)

register_tool(
    'get_expiring_habilitations',
    get_expiring_habilitations,
    "Lister les habilitations sécurité qui expirent bientôt ou sont déjà expirées.",
    {
        'type': 'object',
        'properties': {
            'days': {'type': 'integer', 'description': 'Nombre de jours avant expiration', 'default': 60},
        },
    }
)
