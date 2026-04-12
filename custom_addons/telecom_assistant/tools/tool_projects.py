# -*- coding: utf-8 -*-
"""Tools: Projects, margins, costs breakdown."""
from odoo.addons.telecom_assistant.models.assistant_tool_registry import register_tool


def list_projects(env, active_only=True):
    """List all projects with basic info."""
    domain = []
    if active_only:
        domain = [('active', '=', True)]
    projects = env['project.project'].search(domain, limit=50, order='name')
    result = []
    for p in projects:
        lots = env['telecom.lot'].search_count([('project_id', '=', p.id)])
        result.append({
            'id': p.id,
            'name': p.name,
            'partner': p.partner_id.name if p.partner_id else None,
            'lots': lots,
        })
    return {'count': len(result), 'projects': result}


def get_project_status(env, project_name=None, project_id=None):
    """Get project status with margin, costs, and progress."""
    domain = []
    if project_id:
        domain = [('id', '=', project_id)]
    elif project_name:
        domain = [('name', 'ilike', project_name)]
    else:
        domain = [('active', '=', True)]

    projects = env['project.project'].search(domain, limit=10)
    result = []
    for p in projects:
        lots = env['telecom.lot'].search([('project_id', '=', p.id)])
        # Get costs — use try/except for field name compatibility
        costs = env['telecom.cost.entry'].search([('project_id', '=', p.id)])
        total_cost = 0
        for c in costs:
            try:
                total_cost += c.amount
            except Exception:
                try:
                    total_cost += c.montant
                except Exception:
                    pass

        # Get margin — may fail if SQL view has issues
        margin_pct = 0
        health = 'unknown'
        try:
            margins = env['telecom.project.margin'].search([('project_id', '=', p.id)], limit=1)
            if margins:
                margin_pct = margins.marge_pct or 0
                health = margins.health or 'unknown'
        except Exception:
            pass

        result.append({
            'id': p.id,
            'name': p.name,
            'partner': p.partner_id.name if p.partner_id else None,
            'lots': len(lots),
            'total_costs_mad': round(total_cost, 2),
            'margin_pct': margin_pct,
            'health': health,
        })
    return {'count': len(result), 'projects': result}


def get_cost_breakdown(env, project_name=None, project_id=None, month=None, cost_type=None):
    """Get cost breakdown for a project."""
    domain = []
    if project_id:
        domain.append(('project_id', '=', project_id))
    elif project_name:
        projects = env['project.project'].search([('name', 'ilike', project_name)], limit=1)
        if projects:
            domain.append(('project_id', '=', projects.id))
    if month:
        domain.append(('date', '>=', month + '-01'))
        domain.append(('date', '<=', month + '-31'))
    if cost_type:
        types = env['telecom.cost.type'].search([('name', 'ilike', cost_type)])
        domain.append(('cost_type_id', 'in', types.ids))

    costs = env['telecom.cost.entry'].search(domain, order='date desc', limit=50)
    result = []
    for c in costs:
        result.append({
            'date': str(c.date),
            'type': c.cost_type_id.name,
            'category': c.category,
            'description': c.description,
            'amount_mad': round(c.amount, 2),
            'project': c.project_id.name,
            'lot': c.lot_id.name if c.lot_id else None,
        })
    return {
        'count': len(result),
        'total_mad': round(sum(r['amount_mad'] for r in result), 2),
        'entries': result,
    }


register_tool(
    'list_projects',
    list_projects,
    "Lister tous les projets actifs avec leur nom, client et nombre de lots.",
    {
        'type': 'object',
        'properties': {
            'active_only': {'type': 'boolean', 'description': 'Filtrer les projets actifs uniquement', 'default': True},
        },
    }
)

register_tool(
    'get_project_status',
    get_project_status,
    "Obtenir le statut d'un projet : marge, coûts, avancement, santé. Peut chercher par nom ou ID.",
    {
        'type': 'object',
        'properties': {
            'project_name': {'type': 'string', 'description': 'Nom ou partie du nom du projet'},
            'project_id': {'type': 'integer', 'description': 'ID du projet'},
        },
    }
)

register_tool(
    'get_cost_breakdown',
    get_cost_breakdown,
    "Obtenir le détail des coûts d'un projet, filtrable par mois et type de coût.",
    {
        'type': 'object',
        'properties': {
            'project_name': {'type': 'string', 'description': 'Nom du projet'},
            'project_id': {'type': 'integer', 'description': 'ID du projet'},
            'month': {'type': 'string', 'description': 'Mois au format YYYY-MM'},
            'cost_type': {'type': 'string', 'description': 'Type de coût (carburant, main oeuvre, etc.)'},
        },
    }
)
