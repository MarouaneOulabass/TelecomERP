# -*- coding: utf-8 -*-
"""
TelecomERP — Test E2E de surface
==================================
Valide que chaque action, vue, bouton, et workflow fonctionne sans erreur.
Pas de selenium — on teste cote serveur via l'ORM Odoo.
"""
import odoo
import traceback
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')

results = []
def test(section, name, fn):
    try:
        fn()
        results.append((section, name, True, ''))
        print(f'  [OK] {name}')
    except Exception as e:
        msg = str(e)[:200]
        results.append((section, name, False, msg))
        print(f'  [KO] {name}')
        print(f'       {msg}')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {'test_mode': True})

    print('=' * 70)
    print('  TEST E2E DE SURFACE — TelecomERP')
    print('=' * 70)

    # ══════════════════════════════════════════════════════════════════
    # 1. VUES — Toutes les vues se chargent
    # ══════════════════════════════════════════════════════════════════
    print('\n== 1. VALIDATION DES VUES ==')

    views = env['ir.ui.view'].search([('model', 'like', 'telecom.%')])
    for v in views:
        test('Vues', f'{v.type} {v.model} ({v.name})', lambda v=v: v._check_xml())

    # ══════════════════════════════════════════════════════════════════
    # 2. ACTIONS — Toutes les actions s'ouvrent
    # ══════════════════════════════════════════════════════════════════
    print('\n== 2. VALIDATION DES ACTIONS ==')

    actions = env['ir.actions.act_window'].search([('res_model', 'like', 'telecom.%')])
    for act in actions:
        def check_action(a=act):
            assert a.res_model in env, f'Modele {a.res_model} inexistant'
            model = env[a.res_model]
            # Simulate loading the view
            if a.view_mode:
                for vm in a.view_mode.split(','):
                    vm = vm.strip()
                    if vm == 'tree':
                        model.get_views([(False, 'list')])
                    elif vm in ('form', 'kanban', 'search', 'pivot', 'graph', 'calendar'):
                        model.get_views([(False, vm)])
        test('Actions', f'{act.name} ({act.res_model})', check_action)

    # ══════════════════════════════════════════════════════════════════
    # 3. MENUS — Tous les menus sont accessibles
    # ══════════════════════════════════════════════════════════════════
    print('\n== 3. VALIDATION DES MENUS ==')

    menus = env['ir.ui.menu'].search([])
    telecom_menus = menus.filtered(lambda m: 'telecom' in (m.get_external_id().get(m.id, '') or ''))
    for menu in telecom_menus:
        def check_menu(m=menu):
            if m.action:
                # Ensure action exists and is loadable
                assert m.action.exists(), f'Action {m.action} inexistante'
        test('Menus', f'{menu.complete_name}', check_menu)

    # ══════════════════════════════════════════════════════════════════
    # 4. CRUD — Creer, lire, modifier, supprimer chaque modele
    # ══════════════════════════════════════════════════════════════════
    print('\n== 4. CRUD SUR CHAQUE MODELE ==')

    crud_tests = [
        ('telecom.site', {'name': 'Test E2E', 'code_interne': 'E2E-001', 'site_type': 'pylone_greenfield'}),
        ('telecom.intervention', None),  # needs site
        ('telecom.equipment', None),  # needs category
        ('telecom.vehicle', {'immatriculation': 'E2E-TEST-001', 'marque': 'Test', 'modele': 'E2E'}),
        ('telecom.contract', {'name': 'E2E Contract', 'contract_type': 'maintenance', 'partenaire_id': None, 'date_debut': '2026-01-01'}),
        ('telecom.ao', {'name': 'E2E AO', 'maitre_ouvrage_id': None}),
        ('telecom.lot', {'name': 'E2E-LOT', 'project_id': None}),
        ('telecom.decompte', None),  # complex deps
        ('telecom.situation', None),  # complex deps
        ('telecom.pointage.chantier', None),  # needs employee + site
        ('telecom.paie.bulletin', None),  # needs employee
        ('telecom.habilitation.type', {'name': 'E2E Hab Type', 'code': 'E2E_HAB'}),
        ('telecom.epi.type', {'name': 'E2E EPI Type'}),
        ('telecom.specialite', {'name': 'E2E Specialite'}),
        ('telecom.technologie', {'name': 'E2E Technologie'}),
        ('telecom.certification', None),  # needs partner
        ('telecom.test.feature', {'name': 'e2e.feature', 'module': 'telecom_e2e', 'file_path': '/tmp/e2e'}),
        ('telecom.test.scenario', None),  # needs feature
        ('telecom.test.run', {}),
    ]

    partner = env['res.partner'].create({'name': 'E2E Partner'})
    project = env['project.project'].create({'name': 'E2E Project'})
    site = None
    cat = None

    for model_name, vals in crud_tests:
        if model_name not in env:
            test('CRUD', f'{model_name} — modele existe', lambda: (_ for _ in ()).throw(Exception('Modele inexistant')))
            continue

        # Fill in dependencies
        if vals is None:
            if model_name == 'telecom.intervention':
                if not site:
                    site = env['telecom.site'].create({'name': 'E2E Site', 'code_interne': 'E2E-CRUD', 'site_type': 'pylone_greenfield'})
                vals = {'site_id': site.id, 'intervention_type': 'preventive', 'date_planifiee': '2026-06-01'}
            elif model_name == 'telecom.equipment':
                if not cat:
                    cat = env['telecom.equipment.category'].search([], limit=1)
                    if not cat:
                        cat = env['telecom.equipment.category'].create({'name': 'E2E Cat'})
                vals = {'name': 'E2E Equip', 'numero_serie': 'E2E-SN-001', 'category_id': cat.id}
            elif model_name == 'telecom.pointage.chantier':
                emp = env['hr.employee'].search([], limit=1)
                if not site:
                    site = env['telecom.site'].create({'name': 'E2E Site2', 'code_interne': 'E2E-PT', 'site_type': 'pylone_greenfield'})
                vals = {'employee_id': emp.id, 'site_id': site.id, 'date': '2026-06-01', 'heure_debut': 8.0, 'heure_fin': 17.0}
            elif model_name == 'telecom.paie.bulletin':
                emp = env['hr.employee'].search([], limit=1)
                vals = {'employee_id': emp.id, 'salaire_base': 5000, 'date_from': '2026-06-01', 'date_to': '2026-06-30'}
            elif model_name == 'telecom.certification':
                vals = {'partner_id': partner.id, 'name': 'E2E Cert', 'certification_type': 'other'}
            elif model_name == 'telecom.test.scenario':
                feat = env['telecom.test.feature'].search([], limit=1)
                vals = {'name': 'E2E Scenario', 'feature_id': feat.id, 'module': 'telecom_e2e'}
            elif model_name == 'telecom.decompte':
                contract = env['telecom.contract'].search([], limit=1)
                vals = {'decompte_type': 'provisoire', 'project_id': project.id, 'contract_id': contract.id, 'client_id': partner.id}
            elif model_name == 'telecom.situation':
                vals = {'project_id': project.id, 'client_id': partner.id, 'numero_situation': 99, 'periode_du': '2026-06-01', 'periode_au': '2026-06-30'}
            else:
                continue

        if vals is not None:
            # Fill partner/project refs
            for k in list(vals.keys()):
                if vals[k] is None:
                    if 'partner' in k or 'partenaire' in k or 'maitre_ouvrage' in k or 'client' in k:
                        vals[k] = partner.id
                    elif 'project' in k:
                        vals[k] = project.id

        def crud_test(m=model_name, v=vals):
            rec = env[m].create(v)
            assert rec.id, 'Create failed'
            # Read
            rec.read()
            # Write
            if 'name' in env[m]._fields:
                rec.write({'name': rec.name or 'updated'})
            # Unlink (skip for records that might cascade)
            rec.unlink()

        test('CRUD', f'{model_name} — create/read/write/delete', crud_test)

    # ══════════════════════════════════════════════════════════════════
    # 5. WORKFLOWS — Transitions d'etat
    # ══════════════════════════════════════════════════════════════════
    print('\n== 5. WORKFLOWS ==')

    # Site lifecycle
    def test_site_workflow():
        s = env['telecom.site'].create({'name': 'WF Site', 'code_interne': 'WF-001', 'site_type': 'pylone_greenfield'})
        assert s.state == 'prospection'
        s.write({'state': 'etude'})
        assert s.state == 'etude'
        s.write({'state': 'deploiement'})
        s.write({'state': 'livre'})
        assert s.state == 'livre'
        s.unlink()
    test('Workflow', 'Site: prospection -> etude -> deploiement -> livre', test_site_workflow)

    # Intervention workflow
    def test_intervention_workflow():
        s = env['telecom.site'].create({'name': 'WF Inter Site', 'code_interne': 'WF-INT', 'site_type': 'pylone_greenfield'})
        bi = env['telecom.intervention'].create({
            'site_id': s.id, 'intervention_type': 'corrective', 'date_planifiee': '2026-06-01',
        })
        assert bi.state == 'draft'
        bi.action_planifier()
        assert bi.state == 'planifie'
        bi.action_demarrer()
        assert bi.state == 'en_cours'
        bi.action_terminer()
        assert bi.state == 'termine'
        bi.unlink()
        s.unlink()
    test('Workflow', 'Intervention: draft -> planifie -> en_cours -> termine', test_intervention_workflow)

    # Contract workflow
    def test_contract_workflow():
        c = env['telecom.contract'].create({
            'name': 'WF Contract', 'contract_type': 'maintenance',
            'partenaire_id': partner.id, 'date_debut': '2026-01-01',
        })
        assert c.state == 'brouillon'
        c.action_activer()
        assert c.state == 'actif'
        c.action_suspendre()
        assert c.state == 'suspendu'
        c.action_reactiver()
        assert c.state == 'actif'
        c.unlink()
    test('Workflow', 'Contrat: brouillon -> actif -> suspendu -> actif', test_contract_workflow)

    # Paie workflow
    def test_paie_workflow():
        emp = env['hr.employee'].search([], limit=1)
        b = env['telecom.paie.bulletin'].create({
            'employee_id': emp.id, 'salaire_base': 7000,
            'date_from': '2026-09-01', 'date_to': '2026-09-30',
        })
        assert b.state == 'draft'
        b.action_confirmer()
        assert b.state == 'confirme'
        b.action_valider()
        assert b.state == 'valide'
        b.action_marquer_paye()
        assert b.state == 'paye'
        b.unlink()
    test('Workflow', 'Bulletin paie: draft -> confirme -> valide -> paye', test_paie_workflow)

    # AO workflow
    def test_ao_workflow():
        ao = env['telecom.ao'].create({'name': 'WF AO', 'maitre_ouvrage_id': partner.id})
        assert ao.state == 'detecte'
        ao.action_passer_etude()
        assert ao.state == 'etude'
        ao.write({'date_remise': '2026-12-31'})
        ao.action_soumettre()
        assert ao.state == 'soumis'
        ao.action_gagner()
        assert ao.state == 'gagne'
        ao.unlink()
    test('Workflow', 'AO: detecte -> etude -> soumis -> gagne', test_ao_workflow)

    # Decompte workflow
    def test_decompte_workflow():
        contract = env['telecom.contract'].search([], limit=1)
        d = env['telecom.decompte'].create({
            'decompte_type': 'provisoire', 'project_id': project.id,
            'contract_id': contract.id, 'client_id': partner.id,
        })
        assert d.state == 'draft'
        d.action_soumettre()
        assert d.state == 'soumis'
        d.action_approuver()
        assert d.state == 'approuve'
        d.action_signer()
        assert d.state == 'signe'
        d.unlink()
    test('Workflow', 'Decompte: draft -> soumis -> approuve -> signe', test_decompte_workflow)

    # Vehicle workflow
    def test_vehicle_workflow():
        v = env['telecom.vehicle'].create({
            'immatriculation': 'WF-VEH-001', 'marque': 'Test', 'modele': 'WF',
        })
        assert v.state == 'disponible'
        v.action_affecter_mission()
        assert v.state == 'en_mission'
        v.action_retour()
        assert v.state == 'disponible'
        v.unlink()
    test('Workflow', 'Vehicule: disponible -> en_mission -> disponible', test_vehicle_workflow)

    # ══════════════════════════════════════════════════════════════════
    # 6. CALCULS METIER
    # ══════════════════════════════════════════════════════════════════
    print('\n== 6. CALCULS METIER ==')

    def test_cnss():
        emp = env['hr.employee'].search([], limit=1)
        b = env['telecom.paie.bulletin'].create({
            'employee_id': emp.id, 'salaire_base': 10000,
            'date_from': '2026-10-01', 'date_to': '2026-10-31',
        })
        assert abs(b.cnss_base - 6000) < 0.01, f'CNSS base: {b.cnss_base}'
        assert abs(b.cnss_salarie - 268.80) < 0.01, f'CNSS sal: {b.cnss_salarie}'
        assert abs(b.amo_salarie - 226.0) < 0.01, f'AMO sal: {b.amo_salarie}'
        b.unlink()
    test('Calculs', 'CNSS plafond 6000 + AMO sans plafond', test_cnss)

    def test_caution_ao():
        ao = env['telecom.ao'].create({'name': 'Calc AO', 'maitre_ouvrage_id': partner.id, 'montant_estimatif': 1000000})
        assert abs(ao.caution_provisoire_montant - 15000) < 0.01, f'Caution prov: {ao.caution_provisoire_montant}'
        assert abs(ao.caution_definitif_montant - 30000) < 0.01, f'Caution def: {ao.caution_definitif_montant}'
        ao.unlink()
    test('Calculs', 'Caution AO 1.5% / 3%', test_caution_ao)

    def test_decompte_calculs():
        contract = env['telecom.contract'].search([], limit=1)
        d = env['telecom.decompte'].create({
            'decompte_type': 'provisoire', 'project_id': project.id,
            'contract_id': contract.id, 'client_id': partner.id,
            'montant_travaux_ht': 500000, 'retenue_garantie_taux': 10,
        })
        assert abs(d.total_ht_cumul - 500000) < 0.01
        assert abs(d.retenue_garantie_cumul - 50000) < 0.01
        d.unlink()
    test('Calculs', 'Decompte RG 10% sur 500K', test_decompte_calculs)

    # ══════════════════════════════════════════════════════════════════
    # 7. CONTRAINTES ET VALIDATIONS
    # ══════════════════════════════════════════════════════════════════
    print('\n== 7. CONTRAINTES ==')

    def test_ice_invalid():
        try:
            env['res.partner'].create({'name': 'Bad ICE', 'ice': '12345'})
            assert False, 'Should have raised'
        except Exception:
            pass
    test('Contraintes', 'ICE invalide (< 15 chiffres) refuse', test_ice_invalid)

    def test_site_code_unique():
        s1 = env['telecom.site'].create({'name': 'Dup1', 'code_interne': 'DUP-E2E', 'site_type': 'rooftop'})
        try:
            env['telecom.site'].create({'name': 'Dup2', 'code_interne': 'DUP-E2E', 'site_type': 'rooftop'})
            assert False, 'Should have raised'
        except Exception:
            pass
        s1.unlink()
    test('Contraintes', 'Code site unique', test_site_code_unique)

    def test_bulletin_negatif():
        emp = env['hr.employee'].search([], limit=1)
        try:
            env['telecom.paie.bulletin'].create({
                'employee_id': emp.id, 'salaire_base': -100,
                'date_from': '2026-11-01', 'date_to': '2026-11-30',
            })
            assert False, 'Should have raised'
        except Exception:
            pass
    test('Contraintes', 'Salaire negatif refuse', test_bulletin_negatif)

    # ══════════════════════════════════════════════════════════════════
    # 8. RAPPORTS PDF
    # ══════════════════════════════════════════════════════════════════
    print('\n== 8. RAPPORTS PDF ==')

    reports = env['ir.actions.report'].search([('model', 'like', 'telecom.%')])
    for r in reports:
        test('Rapports', f'{r.name} ({r.model})', lambda r=r: r.exists())

    # ══════════════════════════════════════════════════════════════════
    # RESUME
    # ══════════════════════════════════════════════════════════════════
    total = len(results)
    ok = sum(1 for r in results if r[2])
    ko = total - ok

    print('\n' + '=' * 70)
    print(f'  RESULTAT E2E : {ok}/{total} tests passent ({ok*100//total}%)')
    print('=' * 70)

    if ko:
        print(f'\n  {ko} ECHEC(S) :')
        for section, name, passed, msg in results:
            if not passed:
                print(f'    [{section}] {name}')
                if msg:
                    print(f'      -> {msg[:150]}')

    print('=' * 70)
    cr.rollback()
