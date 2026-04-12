# -*- coding: utf-8 -*-
"""
TelecomERP — Données de démonstration V2 (cohérentes)
======================================================
Crée un jeu de données réaliste où tout est lié :
- Chaque projet a ses lots, sites, interventions, coûts, situations
- Chaque intervention consomme des coûts rattachés au bon projet/lot
- Les bulletins de paie couvrent 6 mois
- Les pointages sont cohérents avec les interventions
- Les situations de travaux reflètent l'avancement réel
"""
import odoo
import random
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    today = date.today()

    print('=' * 60)
    print('  DONNEES DEMO V2 — Coherentes et completes')
    print('=' * 60)

    # ── References existantes ──
    employees = env['hr.employee'].search([('telecom_technicien', '=', True)])
    projects = env['project.project'].search([])
    sites = env['telecom.site'].search([])
    contracts = env['telecom.contract'].search([('state', '=', 'actif')])
    cost_types = env['telecom.cost.type'].search([])
    partners = env['res.partner'].search([('partner_type', '=', 'operator')])

    if not employees or not projects or not sites:
        print('ERREUR: pas assez de donnees de base')
        exit()

    cost_type_map = {ct.category: ct for ct in cost_types}

    # ── 1. Bulletins de paie sur 6 mois ──
    print('\n[1/5] Bulletins de paie (6 mois)...')
    months_created = 0
    for month_offset in range(6):
        month_date = today - relativedelta(months=month_offset)
        date_from = month_date.replace(day=1)
        date_to = (date_from + relativedelta(months=1)) - timedelta(days=1)

        for emp in employees[:15]:
            existing = env['telecom.paie.bulletin'].search([
                ('employee_id', '=', emp.id),
                ('date_from', '=', date_from.isoformat()),
            ], limit=1)
            if existing:
                continue

            contract = env['hr.contract'].search([
                ('employee_id', '=', emp.id), ('state', '=', 'open')
            ], limit=1)
            salary = contract.wage if contract else 7000

            try:
                b = env['telecom.paie.bulletin'].create({
                    'employee_id': emp.id,
                    'salaire_base': salary,
                    'date_from': date_from.isoformat(),
                    'date_to': date_to.isoformat(),
                })
                if month_offset > 0:
                    try:
                        b.action_confirmer()
                        b.action_valider()
                        if month_offset > 1:
                            b.action_marquer_paye()
                    except Exception:
                        pass
                months_created += 1
            except Exception:
                pass
    print('  %d bulletins crees' % months_created)

    # ── 2. Pointages coherents (3 mois, lies aux sites des projets) ──
    print('\n[2/5] Pointages chantier (3 mois)...')
    pointages_created = 0
    site_list = list(sites[:10])
    emp_list = list(employees[:10])

    for day_offset in range(60):
        d = today - timedelta(days=day_offset)
        if d.weekday() >= 5:
            continue
        for i, emp in enumerate(emp_list[:8]):
            site = site_list[i % len(site_list)]
            existing = env['telecom.pointage.chantier'].search([
                ('employee_id', '=', emp.id),
                ('site_id', '=', site.id),
                ('date', '=', d.isoformat()),
            ], limit=1)
            if existing:
                continue
            try:
                heures_sup = random.choice([0, 0, 0, 1, 2, 3])
                p = env['telecom.pointage.chantier'].create({
                    'employee_id': emp.id,
                    'site_id': site.id,
                    'date': d.isoformat(),
                    'heure_debut': 8.0,
                    'heure_fin': 17.0 + heures_sup,
                    'prime_deplacement': random.choice([80, 100, 120, 150]),
                })
                if day_offset > 3:
                    try:
                        p.action_valider()
                    except Exception:
                        pass
                pointages_created += 1
            except Exception:
                pass
    print('  %d pointages crees' % pointages_created)

    # ── 3. Couts coherents par projet/lot (6 mois) ──
    print('\n[3/5] Couts par projet (6 mois)...')
    couts_created = 0
    for proj in projects[:4]:
        lots = env['telecom.lot'].search([('project_id', '=', proj.id)])
        if not lots:
            continue

        for month_offset in range(6):
            month_date = today - relativedelta(months=month_offset)

            for lot in lots[:2]:
                # Main d'oeuvre
                for _ in range(random.randint(2, 5)):
                    ct = cost_type_map.get('main_oeuvre')
                    if not ct:
                        continue
                    try:
                        env['telecom.cost.entry'].create({
                            'date': (month_date - timedelta(days=random.randint(0, 28))).isoformat(),
                            'cost_type_id': ct.id,
                            'description': random.choice([
                                'Equipe fibre J%d' % random.randint(1,20),
                                'Techniciens raccordement',
                                'Chef de chantier',
                                'Main oeuvre pose cable',
                            ]),
                            'project_id': proj.id,
                            'lot_id': lot.id,
                            'montant': random.randint(8000, 25000),
                            'source': 'timesheet',
                            'state': 'validated' if month_offset > 0 else 'confirmed',
                        })
                        couts_created += 1
                    except Exception:
                        pass

                # Materiel
                ct = cost_type_map.get('materiel')
                if ct:
                    try:
                        env['telecom.cost.entry'].create({
                            'date': (month_date - timedelta(days=random.randint(0, 28))).isoformat(),
                            'cost_type_id': ct.id,
                            'description': random.choice([
                                'Cable fibre 96FO 500m',
                                'Connecteurs SC/APC x100',
                                'Boitiers PBO x20',
                                'Fourreaux PEHD 200m',
                                'Antenne Huawei AAU5614',
                            ]),
                            'project_id': proj.id,
                            'lot_id': lot.id,
                            'montant': random.randint(5000, 80000),
                            'source': 'invoice',
                            'state': 'validated',
                        })
                        couts_created += 1
                    except Exception:
                        pass

                # Sous-traitance (1 sur 3 lots)
                if random.random() < 0.3:
                    ct = cost_type_map.get('sous_traitance')
                    if ct:
                        try:
                            env['telecom.cost.entry'].create({
                                'date': (month_date - timedelta(days=random.randint(0, 28))).isoformat(),
                                'cost_type_id': ct.id,
                                'description': 'Sous-traitance genie civil',
                                'project_id': proj.id,
                                'lot_id': lot.id,
                                'montant': random.randint(15000, 60000),
                                'source': 'invoice',
                                'state': 'validated',
                            })
                            couts_created += 1
                        except Exception:
                            pass

                # Carburant
                ct = cost_type_map.get('carburant')
                if ct:
                    try:
                        env['telecom.cost.entry'].create({
                            'date': (month_date - timedelta(days=random.randint(0, 28))).isoformat(),
                            'cost_type_id': ct.id,
                            'description': 'Carburant vehicules chantier',
                            'project_id': proj.id,
                            'lot_id': lot.id,
                            'montant': random.randint(2000, 8000),
                            'source': 'fuel',
                            'state': 'validated',
                        })
                        couts_created += 1
                    except Exception:
                        pass

    print('  %d couts crees' % couts_created)

    # ── 4. Situations de travaux coherentes ──
    print('\n[4/5] Situations de travaux...')
    situations_created = 0
    for proj in projects[:3]:
        contract = contracts[:1]
        if not contract:
            continue
        client = partners[:1]
        if not client:
            continue

        for num in range(1, 7):
            existing = env['telecom.situation'].search([
                ('project_id', '=', proj.id),
                ('numero_situation', '=', num),
            ], limit=1)
            if existing:
                continue

            avancement = min(num * 15, 90)
            prev = (num - 1) * 15 * 150000 / 100 if num > 1 else 0

            try:
                sit = env['telecom.situation'].create({
                    'project_id': proj.id,
                    'contract_id': contract.id,
                    'client_id': client.id,
                    'numero_situation': num,
                    'date_situation': (today - relativedelta(months=6-num)).isoformat(),
                    'periode_du': (today - relativedelta(months=7-num)).replace(day=1).isoformat(),
                    'periode_au': (today - relativedelta(months=6-num)).replace(day=28).isoformat(),
                    'montant_marche_ht': 15000000,
                    'taux_avancement_cumul': avancement,
                    'montant_situation_precedente': prev,
                })
                if num < 5:
                    try:
                        sit.action_soumettre()
                        sit.action_approuver()
                    except Exception:
                        pass
                situations_created += 1
            except Exception:
                pass
    print('  %d situations creees' % situations_created)

    # ── 5. Decomptes par projet ──
    print('\n[5/5] Decomptes provisoires...')
    decomptes_created = 0
    for proj in projects[:3]:
        contract = contracts[:1]
        if not contract:
            continue
        client = partners[:1]
        if not client:
            continue

        existing = env['telecom.decompte'].search([('project_id', '=', proj.id)])
        if len(existing) >= 2:
            continue

        # Get total costs for this project
        total_costs = sum(c.montant for c in env['telecom.cost.entry'].search([('project_id', '=', proj.id)]))

        try:
            d = env['telecom.decompte'].create({
                'decompte_type': 'provisoire',
                'project_id': proj.id,
                'contract_id': contract.id,
                'client_id': client.id,
                'montant_marche_ht': 15000000,
                'montant_travaux_ht': min(total_costs * 1.3, 10000000),
                'retenue_garantie_taux': 10.0,
                'tva_taux': 20.0,
            })
            try:
                d.action_soumettre()
            except Exception:
                pass
            decomptes_created += 1
        except Exception:
            pass
    print('  %d decomptes crees' % decomptes_created)

    cr.commit()

    # ── Resume ──
    print('\n' + '=' * 60)
    print('  DONNEES V2 CHARGEES')
    print('=' * 60)
    print('  Bulletins paie: %d' % env['telecom.paie.bulletin'].search_count([]))
    print('  Pointages: %d' % env['telecom.pointage.chantier'].search_count([]))
    print('  Couts: %d' % env['telecom.cost.entry'].search_count([]))
    print('  Situations: %d' % env['telecom.situation'].search_count([]))
    print('  Decomptes: %d' % env['telecom.decompte'].search_count([]))
    print('=' * 60)
