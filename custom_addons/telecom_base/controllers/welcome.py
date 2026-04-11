# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class TelecomWelcome(http.Controller):

    @http.route('/telecom/welcome', type='http', auth='user', website=False)
    def welcome(self, **kwargs):
        env = request.env

        stats = {
            'sites': env['telecom.site'].search_count([]),
            'sites_live': env['telecom.site'].search_count([('state', '=', 'livre')]),
            'interventions': env['telecom.intervention'].search_count([]),
            'interventions_active': env['telecom.intervention'].search_count([
                ('state', 'in', ['en_cours', 'planifie']),
            ]),
            'employees': env['hr.employee'].search_count([('telecom_technicien', '=', True)]),
            'equipments': env['telecom.equipment'].search_count([]),
            'vehicles': env['telecom.vehicle'].search_count([]),
            'contracts': env['telecom.contract'].search_count([('state', '=', 'actif')]),
            'ao_pipeline': env['telecom.ao'].search_count([('state', 'in', ['detecte', 'etude', 'soumis'])]),
            'projects': env['project.project'].search_count([]),
        }

        s = stats
        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>TelecomERP</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);min-height:100vh;color:#fff}}
.container{{max-width:1100px;margin:0 auto;padding:30px 20px}}
h1{{font-size:2.5rem;text-align:center;margin-bottom:8px}}
h1 .red{{color:#e94560}}
.subtitle{{text-align:center;color:#a8a8b3;font-size:1.1rem;margin-bottom:40px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;margin-bottom:40px}}
.stat{{background:rgba(255,255,255,0.08);border-radius:16px;padding:24px;text-align:center}}
.stat .icon{{font-size:2rem;margin-bottom:8px}}
.stat .number{{font-size:2rem;font-weight:700}}
.stat .label{{color:#a8a8b3;font-size:0.9rem}}
.stat .sub{{color:#4ecca3;font-size:0.8rem;margin-top:4px}}
.modules{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-bottom:40px}}
.mod{{background:rgba(255,255,255,0.06);border-radius:12px;padding:16px;text-decoration:none;color:#fff;transition:transform 0.2s}}
.mod:hover{{transform:translateY(-3px)}}
.mod h3{{margin-bottom:6px}}
.mod p{{color:#a8a8b3;font-size:0.85rem;margin:0}}
.footer{{text-align:center;padding:30px 0;color:#555}}
.footer a{{color:#e94560;text-decoration:none;padding:10px 30px;border:1px solid #e94560;border-radius:6px;display:inline-block;margin-top:10px}}
.footer a:hover{{background:#e94560;color:#fff}}
</style></head><body>
<div class="container">
<h1><span class="red">Telecom</span>ERP</h1>
<p class="subtitle">Deploiement &amp; Maintenance Infrastructure Telecom — Maroc</p>

<div class="stats">
<div class="stat"><div class="icon" style="color:#e94560">&#9881;</div><div class="number">{s['sites']}</div><div class="label">Sites telecom</div><div class="sub">{s['sites_live']} operationnels</div></div>
<div class="stat"><div class="icon" style="color:#4ecca3">&#9874;</div><div class="number">{s['interventions']}</div><div class="label">Interventions</div><div class="sub">{s['interventions_active']} en cours</div></div>
<div class="stat"><div class="icon" style="color:#3282b8">&#9775;</div><div class="number">{s['employees']}</div><div class="label">Techniciens</div><div class="sub">{s['vehicles']} vehicules</div></div>
<div class="stat"><div class="icon" style="color:#ffc107">&#9733;</div><div class="number">{s['contracts']}</div><div class="label">Contrats actifs</div><div class="sub">{s['ao_pipeline']} AO en pipeline</div></div>
</div>

<div class="modules">
<a class="mod" href="/odoo"><h3>&#128205; Sites &amp; Infrastructure</h3><p>25 sites, GPS, bailleur, cycle de vie</p></a>
<a class="mod" href="/odoo"><h3>&#128295; Interventions Terrain</h3><p>BI, SLA, photos, signatures</p></a>
<a class="mod" href="/odoo"><h3>&#128100; RH &amp; Paie</h3><p>CNSS, AMO, IR, habilitations, EPI</p></a>
<a class="mod" href="/odoo"><h3>&#128187; Equipements</h3><p>N serie, garantie, outillages</p></a>
<a class="mod" href="/odoo"><h3>&#128666; Projets &amp; Chantiers</h3><p>Lots, PV reception, avancement</p></a>
<a class="mod" href="/odoo"><h3>&#128200; Finance CCAG</h3><p>Situations, decomptes, RG 10%</p></a>
</div>

<div class="footer">
<p>TelecomERP v17.0 — Odoo 17 Community</p>
<p style="font-size:0.85rem;margin-top:5px">TVA, CNSS, AMO, IR, CGNC, CCAG Travaux</p>
<a href="/odoo">Acceder a l'ERP &rarr;</a>
</div>
</div></body></html>"""

        return request.make_response(html, headers=[('Content-Type', 'text/html')])
