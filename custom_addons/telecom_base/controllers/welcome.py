# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class TelecomWelcome(http.Controller):

    @http.route('/telecom/welcome', type='http', auth='user', website=False)
    def welcome(self, **kwargs):
        env = request.env

        # Gather stats
        stats = {
            'sites': env['telecom.site'].search_count([]),
            'sites_live': env['telecom.site'].search_count([('state', '=', 'livre')]),
            'interventions': env['telecom.intervention'].search_count([]),
            'interventions_today': env['telecom.intervention'].search_count([
                ('state', 'in', ['en_cours', 'planifie']),
            ]),
            'employees': env['hr.employee'].search_count([('telecom_technicien', '=', True)]),
            'equipments': env['telecom.equipment'].search_count([]),
            'vehicles': env['telecom.vehicle'].search_count([]),
            'contracts': env['telecom.contract'].search_count([('state', '=', 'actif')]),
            'ao_pipeline': env['telecom.ao'].search_count([('state', 'in', ['detecte', 'etude', 'soumis'])]),
            'projects': env['project.project'].search_count([]),
        }

        return request.render('telecom_base.welcome_page', {'stats': stats})
