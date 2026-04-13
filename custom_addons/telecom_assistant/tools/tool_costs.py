# -*- coding: utf-8 -*-
"""Tools: Cost tracking and fuel consumption."""
from odoo.addons.telecom_assistant.models.assistant_tool_registry import register_tool


def get_fuel_consumption(env, project_name=None, vehicle_plate=None, month=None, limit=30):
    """Get fuel consumption records."""
    FuelRecord = env.get('telecom.plein.carburant')
    if FuelRecord is None:
        return {'count': 0, 'total_mad': 0, 'records': [], 'info': 'Module carburant non installé'}
    domain = []
    if project_name:
        Project = env.get('project.project')
        if Project:
            projects = Project.search([('name', 'ilike', project_name)], limit=1)
            if projects:
                domain.append(('project_id', '=', projects.id))
    if vehicle_plate:
        Vehicle = env.get('telecom.vehicle')
        if Vehicle:
            vehicles = Vehicle.search([('immatriculation', 'ilike', vehicle_plate)])
            domain.append(('vehicle_id', 'in', vehicles.ids))
    if month:
        domain.append(('date', '>=', month + '-01'))
        domain.append(('date', '<=', month + '-31'))

    records = FuelRecord.search(domain, order='date desc', limit=limit)
    result = []
    total = 0
    for r in records:
        amt = r.amount or 0
        total += amt
        result.append({
            'date': str(r.date),
            'vehicle': r.vehicle_id.immatriculation if r.vehicle_id else None,
            'litres': r.litres,
            'price_per_litre': r.prix_litre,
            'amount_mad': round(amt, 2),
            'km': r.kilometrage,
            'project': r.project_id.name if r.project_id else None,
        })
    return {'count': len(result), 'total_mad': round(total, 2), 'records': result}


register_tool(
    'get_fuel_consumption',
    get_fuel_consumption,
    "Obtenir la consommation de carburant par projet, véhicule ou mois.",
    {
        'type': 'object',
        'properties': {
            'project_name': {'type': 'string', 'description': 'Nom du projet'},
            'vehicle_plate': {'type': 'string', 'description': "Immatriculation du véhicule"},
            'month': {'type': 'string', 'description': 'Mois (YYYY-MM)'},
            'limit': {'type': 'integer', 'default': 30},
        },
    }
)
