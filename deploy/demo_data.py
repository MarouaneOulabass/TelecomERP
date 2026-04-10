# -*- coding: utf-8 -*-
"""
TelecomERP — Script de données de démonstration réalistes
=========================================================
Peuple la base avec des données marocaines réalistes couvrant les 12 modules.

Usage (dans le container Odoo):
    python3 /opt/telecomerp/deploy/demo_data.py
"""
import odoo
import sys
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# ── Bootstrap Odoo ───────────────────────────────────────────────────────────
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
DB = 'telecomerp'
registry = odoo.registry(DB)

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    company = env.company
    today = date.today()

    print("══════════════════════════════════════════════════════")
    print("  TelecomERP — Chargement des données de démonstration")
    print("══════════════════════════════════════════════════════")

    # ═══════════════════════════════════════════════════════════════════════
    # 1. SPÉCIALITÉS TECHNIQUES
    # ═══════════════════════════════════════════════════════════════════════
    print("\n[1/15] Spécialités techniques...")
    specs = {}
    for name, code in [
        ('Fibre optique FTTH/FTTB', 'FIBRE'), ('Radio fréquence 2G/3G/4G/5G', 'RF'),
        ('Courant fort', 'CF'), ('Courant faible', 'CFB'), ('Génie civil télécom', 'GC'),
        ('Climatisation & énergie', 'CLIM'), ('Pylônes & structures', 'PYL'),
        ('Transmission micro-ondes', 'MW'),
    ]:
        s = env['telecom.specialite'].search([('name', '=', name)], limit=1)
        if not s:
            s = env['telecom.specialite'].create({'name': name, 'code': code})
        specs[code] = s

    # ═══════════════════════════════════════════════════════════════════════
    # 2. PARTENAIRES — Opérateurs, sous-traitants, bailleurs
    # ═══════════════════════════════════════════════════════════════════════
    print("[2/15] Partenaires...")

    operators = {}
    for name, ice, ptype in [
        ('Maroc Telecom (IAM)', '001580000093001', 'operator'),
        ('Orange Maroc (Médi Telecom)', '001773289000043', 'operator'),
        ('Inwi (Wana Corporate)', '001518282000025', 'operator'),
        ('ONEE - Branche Électricité', '000123456789012', 'public_org'),
    ]:
        p = env['res.partner'].search([('name', '=', name)], limit=1)
        if not p:
            p = env['res.partner'].create({
                'name': name, 'partner_type': ptype, 'ice': ice,
                'is_company': True, 'country_id': env.ref('base.ma').id,
            })
        operators[name] = p

    subcontractors = {}
    for name, ice, spec_codes in [
        ('TechnoFibre Maroc SARL', '002345678901234', ['FIBRE', 'GC']),
        ('Atlas RF Engineering SA', '003456789012345', ['RF', 'MW']),
        ('Electro Courant Fort SARL', '004567890123456', ['CF', 'CFB']),
        ('Sahara Pylônes & Structures SA', '005678901234567', ['PYL', 'CLIM']),
        ('Digital Infrastructure Maroc', '006789012345678', ['FIBRE', 'RF', 'GC']),
    ]:
        p = env['res.partner'].search([('name', '=', name)], limit=1)
        if not p:
            p = env['res.partner'].create({
                'name': name, 'partner_type': 'subcontractor', 'ice': ice,
                'is_company': True, 'country_id': env.ref('base.ma').id,
                'forme_juridique': 'sarl' if 'SARL' in name else 'sa',
                'specialite_ids': [(6, 0, [specs[c].id for c in spec_codes])],
            })
        subcontractors[name] = p

    bailleurs = {}
    for name, ice in [
        ('Immobilière Al Omrane', '007890123456789'),
        ('Propriétaire Foncier Casablanca SA', '008901234567890'),
        ('Résidences Tanger SARL', '009012345678901'),
        ('Holding Immobilier Rabat', '010123456789012'),
    ]:
        p = env['res.partner'].search([('name', '=', name)], limit=1)
        if not p:
            p = env['res.partner'].create({
                'name': name, 'partner_type': 'lessor', 'ice': ice,
                'is_company': True, 'country_id': env.ref('base.ma').id,
            })
        bailleurs[name] = p

    fournisseurs = {}
    for name, ice in [
        ('Huawei Technologies Maroc', '011234567890123'),
        ('Nokia Networks Maroc', '012345678901234'),
        ('Ericsson Maroc', '013456789012345'),
        ('Corning Optical Maroc', '014567890123456'),
        ('CommScope Maroc', '015678901234567'),
    ]:
        p = env['res.partner'].search([('name', '=', name)], limit=1)
        if not p:
            p = env['res.partner'].create({
                'name': name, 'partner_type': 'supplier', 'ice': ice,
                'is_company': True, 'country_id': env.ref('base.ma').id,
                'supplier_rank': 1,
            })
        fournisseurs[name] = p

    # ── Certifications partenaires ──
    for partner, certs in [
        (subcontractors['TechnoFibre Maroc SARL'], [
            ('Agrément ANRT - Fibre optique', 'anrt', '2027-06-30'),
            ('ISO 9001:2015', 'iso_9001', '2026-12-31'),
        ]),
        (subcontractors['Atlas RF Engineering SA'], [
            ('Agrément ANRT - Radio fréquence', 'anrt', '2027-03-15'),
        ]),
        (subcontractors['Digital Infrastructure Maroc'], [
            ('Agrément ONEE', 'onee', '2026-09-30'),
            ('ISO 14001:2015', 'iso_14001', '2027-01-31'),
            ('ISO 45001:2018', 'iso_45001', '2026-11-30'),
        ]),
    ]:
        for cert_name, cert_type, exp in certs:
            if not env['telecom.certification'].search([('partner_id', '=', partner.id), ('name', '=', cert_name)], limit=1):
                env['telecom.certification'].create({
                    'partner_id': partner.id, 'name': cert_name,
                    'certification_type': cert_type, 'date_expiration': exp,
                })

    # ═══════════════════════════════════════════════════════════════════════
    # 3. SITES TÉLÉCOM — 25 sites réalistes au Maroc
    # ═══════════════════════════════════════════════════════════════════════
    print("[3/15] Sites télécom...")

    sites_data = [
        ('CASA-CTR-001', 'Casablanca Centre - Tour Twin', 'rooftop', 'livre', 33.5731, -7.5898, 'casablanca_settat'),
        ('CASA-AIN-002', 'Casablanca Aïn Diab', 'pylone_greenfield', 'livre', 33.5950, -7.6700, 'casablanca_settat'),
        ('CASA-MOH-003', 'Casablanca Mohammedia Entrée', 'shelter', 'livre', 33.6866, -7.3827, 'casablanca_settat'),
        ('CASA-HAY-004', 'Casablanca Hay Hassani', 'pylone_greenfield', 'deploiement', 33.5600, -7.6500, 'casablanca_settat'),
        ('CASA-BER-005', 'Casablanca Bernoussi ZI', 'indoor_das', 'deploiement', 33.6100, -7.5200, 'casablanca_settat'),
        ('RBT-AGD-001', 'Rabat Agdal', 'rooftop', 'livre', 33.9911, -6.8498, 'rabat_sale_kenitra'),
        ('RBT-HAY-002', 'Rabat Hay Riad', 'pylone_greenfield', 'livre', 34.0100, -6.8800, 'rabat_sale_kenitra'),
        ('RBT-SAL-003', 'Salé Tabriquet', 'rooftop', 'deploiement', 34.0531, -6.8136, 'rabat_sale_kenitra'),
        ('RBT-KEN-004', 'Kénitra Zone Industrielle', 'shelter', 'livre', 34.2610, -6.5802, 'rabat_sale_kenitra'),
        ('TNG-CTR-001', 'Tanger Centre Ville', 'rooftop', 'livre', 35.7595, -5.8340, 'tanger_tetouan_alhoceima'),
        ('TNG-IBN-002', 'Tanger Ibn Batouta Aéroport', 'pylone_greenfield', 'livre', 35.7268, -5.9169, 'tanger_tetouan_alhoceima'),
        ('TNG-TET-003', 'Tétouan Martil', 'pylone_greenfield', 'deploiement', 35.6167, -5.2833, 'tanger_tetouan_alhoceima'),
        ('FES-CTR-001', 'Fès Ville Nouvelle', 'rooftop', 'livre', 34.0331, -5.0003, 'fes_meknes'),
        ('FES-MEK-002', 'Meknès Hamria', 'pylone_greenfield', 'livre', 33.8935, -5.5473, 'fes_meknes'),
        ('MRK-GUE-001', 'Marrakech Guéliz', 'rooftop', 'livre', 31.6340, -8.0100, 'marrakech_safi'),
        ('MRK-MEN-002', 'Marrakech Ménara Aéroport', 'shelter', 'deploiement', 31.6069, -8.0363, 'marrakech_safi'),
        ('AGD-CTR-001', 'Agadir Centre', 'rooftop', 'livre', 30.4278, -9.5981, 'souss_massa'),
        ('AGD-INZ-002', 'Inezgane Zone Industrielle', 'pylone_greenfield', 'autorisation', 30.3556, -9.5339, 'souss_massa'),
        ('OUJ-CTR-001', 'Oujda Centre Ville', 'rooftop', 'livre', 34.6814, -1.9086, 'oriental'),
        ('OUJ-NAD-002', 'Nador Al Aroui', 'pylone_greenfield', 'etude', 35.1740, -2.9287, 'oriental'),
        ('LAY-CTR-001', 'Laâyoune Centre', 'pylone_greenfield', 'livre', 27.1536, -13.2034, 'laayoune_sakia_el_hamra'),
        ('DAK-CTR-001', 'Dakhla Centre', 'pylone_greenfield', 'prospection', 23.7148, -15.9370, 'dakhla_oued_ed_dahab'),
        ('BNM-CTR-001', 'Béni Mellal Centre', 'rooftop', 'livre', 32.3373, -6.3498, 'beni_mellal_khenifra'),
        ('SET-CTR-001', 'Settat Route de Marrakech', 'shelter', 'autorisation', 33.0011, -7.6164, 'casablanca_settat'),
        ('ERR-CTR-001', 'Errachidia Centre', 'pylone_greenfield', 'etude', 31.9314, -4.4288, 'draa_tafilalet'),
    ]

    sites = {}
    for code, name, stype, state, lat, lng, wilaya in sites_data:
        s = env['telecom.site'].search([('code_interne', '=', code)], limit=1)
        if not s:
            vals = {
                'code_interne': code, 'name': name, 'site_type': stype,
                'gps_lat': lat, 'gps_lng': lng, 'wilaya': wilaya,
            }
            bailleur = list(bailleurs.values())[hash(code) % len(bailleurs)]
            vals['bailleur_id'] = bailleur.id
            s = env['telecom.site'].create(vals)
            if state != 'prospection':
                try:
                    s.write({'state': state})
                except Exception:
                    pass
        sites[code] = s

    # ═══════════════════════════════════════════════════════════════════════
    # 4. TYPES D'HABILITATION & TYPES EPI
    # ═══════════════════════════════════════════════════════════════════════
    print("[4/15] Habilitations & EPI types...")

    hab_types = {}
    for name, code, months in [
        ('Travail en hauteur', 'TRAV_HAUTEUR', 36),
        ('Habilitation électrique B1', 'ELEC_B1', 24),
        ('Habilitation électrique B2', 'ELEC_B2', 12),
        ('Habilitation électrique BR', 'ELEC_BR', 24),
        ('CACES Nacelle', 'CACES_NAC', 60),
        ('Sauveteur Secouriste du Travail', 'SST', 24),
        ('Risques chimiques N1', 'CHIMIQ_N1', 36),
        ('Conduite engins de chantier', 'COND_ENGIN', 60),
    ]:
        ht = env['telecom.habilitation.type'].search(['|', ('code', '=', code), ('name', '=', name)], limit=1)
        if not ht:
            ht = env['telecom.habilitation.type'].create({
                'name': name, 'code': code, 'periodicite_renouvellement': months,
            })
        elif not ht.code:
            ht.write({'code': code})
        hab_types[code] = ht

    epi_types = {}
    for name, months in [
        ('Casque de chantier', 36), ('Harnais antichute', 12),
        ('Chaussures de sécurité', 12), ('Gants isolants', 12),
        ('Lunettes de protection', 24), ('Gilet haute visibilité', 24),
        ('Protection auditive', 36), ('Masque respiratoire', 12),
    ]:
        et = env['telecom.epi.type'].search([('name', '=', name)], limit=1)
        if not et:
            et = env['telecom.epi.type'].create({
                'name': name, 'periodicite_renouvellement_mois': months,
            })
        epi_types[name] = et

    # ═══════════════════════════════════════════════════════════════════════
    # 5. EMPLOYÉS — 20 techniciens terrain
    # ═══════════════════════════════════════════════════════════════════════
    print("[5/15] Employés & techniciens...")

    employees_data = [
        ('Mohammed Alami', 8000, 3.0, 3.5, '2018-03-15', ['TRAV_HAUTEUR', 'ELEC_B2']),
        ('Ahmed Bennani', 7500, 3.0, 3.5, '2019-06-01', ['TRAV_HAUTEUR', 'ELEC_B1']),
        ('Youssef El Fassi', 9000, 4.0, 4.5, '2016-01-10', ['TRAV_HAUTEUR', 'ELEC_BR', 'SST']),
        ('Karim Idrissi', 7000, 3.0, 3.5, '2020-09-01', ['TRAV_HAUTEUR']),
        ('Omar Tazi', 8500, 3.0, 3.5, '2017-05-20', ['TRAV_HAUTEUR', 'ELEC_B2', 'CACES_NAC']),
        ('Rachid Mansouri', 10000, 5.0, 5.5, '2014-02-01', ['TRAV_HAUTEUR', 'ELEC_BR', 'SST', 'CACES_NAC']),
        ('Hassan Chraibi', 7500, 3.0, 3.5, '2021-01-15', ['TRAV_HAUTEUR', 'ELEC_B1']),
        ('Abdellah Ouazzani', 8000, 3.0, 3.5, '2019-11-01', ['TRAV_HAUTEUR', 'ELEC_B2']),
        ('Hamza El Amrani', 6500, 0.0, 0.0, '2023-03-01', ['TRAV_HAUTEUR']),
        ('Mustapha Berrada', 9500, 4.0, 4.5, '2015-07-10', ['TRAV_HAUTEUR', 'ELEC_BR', 'CACES_NAC']),
        ('Samir Lahlou', 7000, 3.0, 3.5, '2022-01-10', ['TRAV_HAUTEUR', 'ELEC_B1']),
        ('Nabil Sqalli', 7500, 3.0, 3.5, '2020-04-15', ['TRAV_HAUTEUR', 'ELEC_B2', 'SST']),
        ('Driss Benkirane', 11000, 5.0, 6.0, '2012-09-01', ['TRAV_HAUTEUR', 'ELEC_BR', 'SST', 'COND_ENGIN']),
        ('Khalid Naciri', 8000, 3.0, 3.5, '2018-12-01', ['TRAV_HAUTEUR', 'ELEC_B1']),
        ('Amine Zouiten', 6500, 0.0, 0.0, '2024-01-15', []),
        ('Brahim Hajji', 7000, 3.0, 3.5, '2021-06-01', ['TRAV_HAUTEUR']),
        ('Ismail Kabbaj', 8500, 3.0, 3.5, '2017-03-20', ['TRAV_HAUTEUR', 'ELEC_B2', 'CHIMIQ_N1']),
        ('Mehdi Fassi Fihri', 12000, 5.0, 6.0, '2010-01-05', ['TRAV_HAUTEUR', 'ELEC_BR', 'SST', 'CACES_NAC', 'COND_ENGIN']),
        ('Adil Benjelloun', 9000, 4.0, 4.5, '2016-08-15', ['TRAV_HAUTEUR', 'ELEC_B2', 'SST']),
        ('Zakaria Tahiri', 7500, 3.0, 3.5, '2019-02-01', ['TRAV_HAUTEUR', 'ELEC_B1']),
    ]

    employees = {}
    for name, salary, cimr_s, cimr_p, hire_date, hab_codes in employees_data:
        emp = env['hr.employee'].search([('name', '=', name)], limit=1)
        if not emp:
            emp = env['hr.employee'].create({
                'name': name,
                'telecom_technicien': True,
                'cimr_taux': cimr_s,
                'cimr_taux_patronal': cimr_p,
            })
            # Create contract for hire date
            env['hr.contract'].create({
                'name': f'CDI {name}',
                'employee_id': emp.id,
                'wage': salary,
                'date_start': hire_date,
                'state': 'open',
            })
            # Habilitations
            for hc in hab_codes:
                if hc in hab_types:
                    env['telecom.habilitation.employee'].create({
                        'employee_id': emp.id,
                        'habilitation_type_id': hab_types[hc].id,
                        'date_obtention': (today - relativedelta(months=6)).isoformat(),
                    })
            # EPI dotation — casque + chaussures pour tous
            for epi_name in ['Casque de chantier', 'Chaussures de sécurité', 'Gilet haute visibilité']:
                if epi_name in epi_types:
                    env['telecom.epi.dotation'].create({
                        'employee_id': emp.id,
                        'epi_type_id': epi_types[epi_name].id,
                        'date_dotation': (today - relativedelta(months=3)).isoformat(),
                    })
            if hab_codes and 'TRAV_HAUTEUR' in hab_codes:
                env['telecom.epi.dotation'].create({
                    'employee_id': emp.id,
                    'epi_type_id': epi_types['Harnais antichute'].id,
                    'date_dotation': (today - relativedelta(months=2)).isoformat(),
                })
        employees[name] = emp

    # ═══════════════════════════════════════════════════════════════════════
    # 6. CATÉGORIES & ÉQUIPEMENTS — 40 équipements
    # ═══════════════════════════════════════════════════════════════════════
    print("[6/15] Équipements télécom...")

    categories = {}
    for name in ['Antenne 4G/5G', 'eNodeB/gNodeB', 'OLT', 'ONT', 'Shelter', 'Groupe électrogène',
                  'Batterie', 'Climatisation', 'Câble fibre optique', 'Baie de brassage']:
        c = env['telecom.equipment.category'].search([('name', '=', name)], limit=1)
        if not c:
            c = env['telecom.equipment.category'].create({'name': name})
        categories[name] = c

    equip_data = [
        ('Antenne Huawei AAU5614', 'Antenne 4G/5G', 'SN-ANT-001', 'Huawei', 'AAU5614', 'CASA-CTR-001'),
        ('Antenne Huawei AAU5614', 'Antenne 4G/5G', 'SN-ANT-002', 'Huawei', 'AAU5614', 'CASA-AIN-002'),
        ('Antenne Nokia AEHC', 'Antenne 4G/5G', 'SN-ANT-003', 'Nokia', 'AEHC', 'RBT-AGD-001'),
        ('Antenne Ericsson AIR 6449', 'Antenne 4G/5G', 'SN-ANT-004', 'Ericsson', 'AIR 6449', 'TNG-CTR-001'),
        ('Antenne Nokia AWHQA', 'Antenne 4G/5G', 'SN-ANT-005', 'Nokia', 'AWHQA', 'FES-CTR-001'),
        ('Antenne Huawei AAU5639', 'Antenne 4G/5G', 'SN-ANT-006', 'Huawei', 'AAU5639', 'MRK-GUE-001'),
        ('eNodeB Huawei BBU5900', 'eNodeB/gNodeB', 'SN-ENB-001', 'Huawei', 'BBU5900', 'CASA-CTR-001'),
        ('eNodeB Huawei BBU5900', 'eNodeB/gNodeB', 'SN-ENB-002', 'Huawei', 'BBU5900', 'CASA-AIN-002'),
        ('gNodeB Nokia AMIA', 'eNodeB/gNodeB', 'SN-GNB-001', 'Nokia', 'AMIA', 'RBT-AGD-001'),
        ('eNodeB Ericsson BB6630', 'eNodeB/gNodeB', 'SN-ENB-003', 'Ericsson', 'BB6630', 'TNG-CTR-001'),
        ('OLT Huawei MA5800-X7', 'OLT', 'SN-OLT-001', 'Huawei', 'MA5800-X7', 'CASA-CTR-001'),
        ('OLT Huawei MA5800-X15', 'OLT', 'SN-OLT-002', 'Huawei', 'MA5800-X15', 'RBT-AGD-001'),
        ('OLT Nokia ISAM 7360', 'OLT', 'SN-OLT-003', 'Nokia', 'ISAM 7360', 'FES-CTR-001'),
        ('Shelter Eltek Outdoor 1x1', 'Shelter', 'SN-SHL-001', 'Eltek', 'Outdoor 1x1', 'CASA-MOH-003'),
        ('Shelter Eltek Outdoor 2x2', 'Shelter', 'SN-SHL-002', 'Eltek', 'Outdoor 2x2', 'RBT-KEN-004'),
        ('GE SDMO J130K', 'Groupe électrogène', 'SN-GEN-001', 'SDMO', 'J130K', 'CASA-CTR-001'),
        ('GE Caterpillar C4.4', 'Groupe électrogène', 'SN-GEN-002', 'Caterpillar', 'C4.4', 'TNG-CTR-001'),
        ('Batterie Narada 48V 200Ah', 'Batterie', 'SN-BAT-001', 'Narada', '48V-200Ah', 'CASA-CTR-001'),
        ('Batterie Narada 48V 200Ah', 'Batterie', 'SN-BAT-002', 'Narada', '48V-200Ah', 'RBT-AGD-001'),
        ('Clim Emerson NetSure', 'Climatisation', 'SN-CLM-001', 'Emerson', 'NetSure 5000', 'CASA-CTR-001'),
    ]

    equipments = {}
    for name, cat_name, serial, marque, modele, site_code in equip_data:
        eq = env['telecom.equipment'].search([('numero_serie', '=', serial)], limit=1)
        if not eq:
            eq = env['telecom.equipment'].create({
                'name': name, 'category_id': categories[cat_name].id,
                'numero_serie': serial, 'marque': marque, 'modele': modele,
                'site_id': sites[site_code].id,
                'date_achat': (today - relativedelta(months=12)).isoformat(),
                'date_fin_garantie': (today + relativedelta(months=12)).isoformat(),
                'state': 'installe',
            })
        equipments[serial] = eq

    # ── Outillages terrain ──
    print("[7/15] Outillages terrain...")
    outillages_data = [
        ('OTDR Yokogawa AQ7280', 'otdr', 'OT-OTDR-001'),
        ('OTDR EXFO MaxTester 730C', 'otdr', 'OT-OTDR-002'),
        ('Analyseur spectre Anritsu MS2720T', 'analyseur_spectre', 'OT-AS-001'),
        ('Soudeuse fibre Fujikura 90S+', 'autre', 'OT-SOUD-001'),
        ('Soudeuse fibre Sumitomo T-602S', 'autre', 'OT-SOUD-002'),
        ('Power meter Joinwit JW3208A', 'testeur_fibre', 'OT-PM-001'),
        ('Testeur cuivre Fluke DTX-1800', 'testeur_cable', 'OT-TEST-001'),
    ]
    for name, otype, serial in outillages_data:
        if not env['telecom.outillage'].search([('numero_serie', '=', serial)], limit=1):
            env['telecom.outillage'].create({
                'name': name, 'outillage_type': otype, 'numero_serie': serial,
                'date_dernier_etalonnage': (today - relativedelta(months=4)).isoformat(),
                'periodicite_etalonnage_mois': 12,
            })

    # ═══════════════════════════════════════════════════════════════════════
    # 7. VÉHICULES — 8 véhicules terrain
    # ═══════════════════════════════════════════════════════════════════════
    print("[8/15] Véhicules terrain...")

    vehicles_data = [
        ('12345-A-78', 'Toyota', 'Hilux DC 2.4 D-4D', 2022, 'diesel', 45000, 'Mohammed Alami'),
        ('23456-B-12', 'Toyota', 'Hilux SC 2.4', 2021, 'diesel', 62000, 'Ahmed Bennani'),
        ('34567-C-45', 'Renault', 'Kangoo Van', 2023, 'diesel', 28000, 'Youssef El Fassi'),
        ('45678-D-33', 'Ford', 'Transit Custom', 2022, 'diesel', 51000, 'Omar Tazi'),
        ('56789-E-67', 'Mitsubishi', 'L200 Sportero', 2021, 'diesel', 71000, 'Rachid Mansouri'),
        ('67890-F-89', 'Dacia', 'Dokker Van', 2023, 'diesel', 19000, 'Karim Idrissi'),
        ('78901-G-23', 'Toyota', 'Land Cruiser 300', 2024, 'diesel', 8000, 'Driss Benkirane'),
        ('89012-H-56', 'Renault', 'Master Fourgon', 2022, 'diesel', 43000, 'Mustapha Berrada'),
    ]

    vehicles = {}
    for immat, marque, modele, annee, carb, km, driver_name in vehicles_data:
        v = env['telecom.vehicle'].search([('immatriculation', '=', immat)], limit=1)
        if not v:
            v = env['telecom.vehicle'].create({
                'immatriculation': immat, 'marque': marque, 'modele': modele,
                'annee': annee, 'carburant': carb, 'kilometrage': km,
                'chauffeur_id': employees.get(driver_name, list(employees.values())[0]).id,
                'carte_grise_expiration': (today + relativedelta(months=8)).isoformat(),
                'assurance_expiration': (today + relativedelta(months=5)).isoformat(),
                'km_dernier_entretien': km - 5000,
                'intervalle_entretien_km': 10000,
            })
            # Entretien historique
            env['telecom.vehicle.entretien'].create({
                'vehicle_id': v.id, 'name': f'Vidange + filtres {km-5000} km',
                'entretien_type': 'vidange',
                'date': (today - relativedelta(months=2)).isoformat(),
                'kilometrage': km - 5000, 'cout': 1500,
            })
        vehicles[immat] = v

    # ═══════════════════════════════════════════════════════════════════════
    # 8. PROJETS & LOTS — 4 projets majeurs
    # ═══════════════════════════════════════════════════════════════════════
    print("[9/15] Projets & lots...")

    projects = {}
    proj_data = [
        ('Déploiement FTTH Grand Casablanca - Phase 2', operators['Maroc Telecom (IAM)'],
         [('LOT-CASA-EST', 'Lot Casablanca Est'), ('LOT-CASA-OUEST', 'Lot Casablanca Ouest')],
         ['CASA-CTR-001', 'CASA-AIN-002', 'CASA-MOH-003', 'CASA-HAY-004', 'CASA-BER-005']),
        ('Rollout 4G/5G Axe Rabat-Kénitra', operators['Orange Maroc (Médi Telecom)'],
         [('LOT-RBT', 'Lot Rabat'), ('LOT-KEN', 'Lot Kénitra')],
         ['RBT-AGD-001', 'RBT-HAY-002', 'RBT-SAL-003', 'RBT-KEN-004']),
        ('Maintenance préventive réseau Nord', operators['Inwi (Wana Corporate)'],
         [('LOT-TNG', 'Lot Tanger'), ('LOT-FES', 'Lot Fès')],
         ['TNG-CTR-001', 'TNG-IBN-002', 'FES-CTR-001', 'FES-MEK-002']),
        ('Extension couverture 4G Sud Maroc', operators['Maroc Telecom (IAM)'],
         [('LOT-AGD', 'Lot Agadir'), ('LOT-LAA', 'Lot Laâyoune-Dakhla')],
         ['AGD-CTR-001', 'AGD-INZ-002', 'LAY-CTR-001', 'DAK-CTR-001']),
    ]

    for proj_name, client, lots_data, site_codes in proj_data:
        proj = env['project.project'].search([('name', '=', proj_name)], limit=1)
        if not proj:
            proj = env['project.project'].create({'name': proj_name, 'partner_id': client.id})
        projects[proj_name] = proj

        for lot_code, lot_name in lots_data:
            lot = env['telecom.lot'].search([('name', '=', lot_code), ('project_id', '=', proj.id)], limit=1)
            if not lot:
                env['telecom.lot'].create({
                    'name': lot_code, 'project_id': proj.id,
                    'description': lot_name,
                })

        for sc in site_codes:
            if sc in sites:
                ps = env['telecom.project.site'].search([
                    ('project_id', '=', proj.id), ('site_id', '=', sites[sc].id)
                ], limit=1)
                if not ps:
                    env['telecom.project.site'].create({
                        'project_id': proj.id, 'site_id': sites[sc].id,
                    })

    # ═══════════════════════════════════════════════════════════════════════
    # 9. APPELS D'OFFRES — 6 AO
    # ═══════════════════════════════════════════════════════════════════════
    print("[10/15] Appels d'offres...")

    ao_data = [
        ('Déploiement FTTH Marrakech-Safi', operators['Maroc Telecom (IAM)'], 15000000, 'gagne', '2025-12-15'),
        ('Maintenance réseau cuivre Oriental', operators['Maroc Telecom (IAM)'], 5000000, 'soumis', '2026-05-30'),
        ('Rollout 5G Casablanca Phase 1', operators['Orange Maroc (Médi Telecom)'], 25000000, 'etude', '2026-07-15'),
        ('Extension fibre Béni Mellal', operators['Inwi (Wana Corporate)'], 8000000, 'detecte', None),
        ('Densification 4G zones rurales Souss', operators['Maroc Telecom (IAM)'], 12000000, 'soumis', '2026-06-01'),
        ('Maintenance préventive sites Tanger-Tétouan', operators['Inwi (Wana Corporate)'], 3500000, 'gagne', '2025-11-01'),
    ]

    aos = {}
    for ao_name, mo, montant, state, date_remise in ao_data:
        ao = env['telecom.ao'].search([('name', '=', ao_name)], limit=1)
        if not ao:
            vals = {
                'name': ao_name, 'maitre_ouvrage_id': mo.id,
                'montant_estimatif': montant,
            }
            if date_remise:
                vals['date_remise'] = date_remise
            ao = env['telecom.ao'].create(vals)
            if state != 'detecte':
                try:
                    ao.write({'state': state})
                except Exception:
                    pass
        aos[ao_name] = ao

        # BPU lignes pour les AO gagnés
        if state == 'gagne' and ao:
            bpu_lines = [
                ('Installation pylône greenfield', 'U', 5, 250000),
                ('Déploiement antenne secteur', 'U', 15, 85000),
                ('Raccordement fibre optique', 'ml', 5000, 150),
                ('Installation shelter outdoor', 'U', 3, 180000),
                ('Mise en service eNodeB', 'U', 10, 45000),
            ]
            for designation, unite, qty, pu in bpu_lines:
                if not env['telecom.bpu.ligne'].search([('ao_id', '=', ao.id), ('designation', '=', designation)], limit=1):
                    env['telecom.bpu.ligne'].create({
                        'ao_id': ao.id, 'designation': designation,
                        'unite': unite, 'quantite': qty, 'prix_unitaire': pu,
                    })

    # ═══════════════════════════════════════════════════════════════════════
    # 10. CONTRATS — 5 contrats
    # ═══════════════════════════════════════════════════════════════════════
    print("[11/15] Contrats...")

    contracts = {}
    contract_data = [
        ('CONT-IAM-2024-001', 'Contrat-cadre déploiement FTTH', 'cadre_operateur',
         operators['Maroc Telecom (IAM)'], '2024-01-01', '2026-12-31', 15000000),
        ('CONT-ORG-2024-001', 'Contrat maintenance réseau Orange', 'maintenance',
         operators['Orange Maroc (Médi Telecom)'], '2024-03-01', '2025-12-31', 5000000),
        ('CONT-INW-2024-001', 'Contrat déploiement 4G Inwi', 'deploiement',
         operators['Inwi (Wana Corporate)'], '2024-06-01', '2026-06-30', 8000000),
        ('CONT-IAM-2025-001', 'Contrat maintenance préventive IAM', 'maintenance',
         operators['Maroc Telecom (IAM)'], '2025-01-01', '2026-12-31', 3500000),
        ('CONT-ST-2024-001', 'Contrat sous-traitance TechnoFibre', 'sous_traitance',
         subcontractors['TechnoFibre Maroc SARL'], '2024-01-01', '2025-12-31', 2000000),
    ]

    for ref, name, ctype, partner, d_start, d_end, montant in contract_data:
        ct = env['telecom.contract'].search([('name', '=', ref)], limit=1)
        if not ct:
            ct = env['telecom.contract'].create({
                'name': ref, 'contract_type': ctype,
                'partenaire_id': partner.id,
                'date_debut': d_start, 'date_fin': d_end,
                'montant_total': montant,
                'sla_delai_intervention_h': 48,
                'sla_delai_reparation_h': 72,
            })
            try:
                ct.write({'state': 'actif'})
            except Exception:
                pass
        contracts[ref] = ct

        # Cautions bancaires pour contrats déploiement
        if ctype in ('cadre_operateur', 'deploiement'):
            for caution_type, taux in [('provisoire', 1.5), ('definitive', 3.0)]:
                if not env['telecom.caution.bancaire'].search([
                    ('contract_id', '=', ct.id), ('caution_type', '=', caution_type)
                ], limit=1):
                    env['telecom.caution.bancaire'].create({
                        'contract_id': ct.id, 'caution_type': caution_type,
                        'banque': 'Attijariwafa Bank',
                        'reference_bancaire': f'CB-{ref}-{caution_type[:4].upper()}',
                        'montant': montant * taux / 100,
                        'date_emission': d_start,
                        'date_expiration': d_end,
                    })

    # ═══════════════════════════════════════════════════════════════════════
    # 11. INTERVENTIONS — 15 bons d'intervention
    # ═══════════════════════════════════════════════════════════════════════
    print("[12/15] Interventions terrain...")

    emp_list = list(employees.values())
    interventions_data = [
        ('preventive', 'CASA-CTR-001', 0, 'planifie', 'Maintenance préventive antennes secteur Nord'),
        ('preventive', 'CASA-AIN-002', 1, 'planifie', 'Vérification groupe électrogène'),
        ('corrective', 'RBT-AGD-001', 2, 'en_cours', 'Panne alimentation eNodeB — remplacement redresseur'),
        ('corrective', 'TNG-CTR-001', 3, 'en_cours', 'Alarme température shelter — vérification clim'),
        ('installation', 'CASA-HAY-004', 4, 'termine', 'Installation antenne Huawei AAU5614 secteur 1'),
        ('installation', 'CASA-BER-005', 5, 'termine', 'Installation shelter + baie de brassage'),
        ('installation', 'RBT-SAL-003', 6, 'valide', 'Déploiement complet site — 3 secteurs 4G'),
        ('audit', 'FES-CTR-001', 7, 'valide', 'Audit technique annuel — rapport ANRT'),
        ('preventive', 'MRK-GUE-001', 8, 'facture', 'Maintenance préventive batteries + clim'),
        ('corrective', 'AGD-CTR-001', 9, 'facture', 'Réparation câble fibre coupé — raccordement'),
        ('installation', 'TNG-IBN-002', 10, 'planifie', 'Installation antenne 5G Nokia — aéroport'),
        ('corrective', 'CASA-MOH-003', 11, 'brouillon', 'Fuite eau shelter — étanchéité toiture'),
        ('preventive', 'RBT-KEN-004', 0, 'brouillon', 'Révision complète site — checklist annuelle'),
        ('installation', 'MRK-MEN-002', 1, 'planifie', 'Déploiement DAS indoor terminal aéroport'),
        ('corrective', 'FES-MEK-002', 2, 'en_cours', 'Remplacement batterie 48V défectueuse'),
    ]

    for itype, site_code, emp_idx, state, description in interventions_data:
        site = sites[site_code]
        bi = env['telecom.intervention'].search([
            ('site_id', '=', site.id), ('description_travaux', '=', description)
        ], limit=1)
        if not bi:
            vals = {
                'intervention_type': itype,
                'site_id': site.id,
                'technician_ids': [(6, 0, [emp_list[emp_idx % len(emp_list)].id])],
                'date_planifiee': (today + timedelta(days=emp_idx - 5)).isoformat(),
                'description_travaux': description,
                'duree_estimee': 4.0 if itype == 'preventive' else 6.0,
            }
            bi = env['telecom.intervention'].create(vals)
            try:
                if state == 'planifie':
                    bi.action_planifier()
                elif state == 'en_cours':
                    bi.action_planifier()
                    bi.action_demarrer()
                elif state == 'termine':
                    bi.action_planifier()
                    bi.action_demarrer()
                    bi.action_terminer()
                elif state == 'valide':
                    bi.action_planifier()
                    bi.action_demarrer()
                    bi.action_terminer()
                    bi.action_valider()
                elif state == 'facture':
                    bi.action_planifier()
                    bi.action_demarrer()
                    bi.action_terminer()
                    bi.action_valider()
                    try:
                        bi.action_facturer()
                    except Exception:
                        pass
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════════════
    # 12. POINTAGES CHANTIER — 30 derniers jours
    # ═══════════════════════════════════════════════════════════════════════
    print("[13/15] Pointages chantier...")

    site_list = [sites[c] for c in ['CASA-CTR-001', 'RBT-AGD-001', 'TNG-CTR-001', 'FES-CTR-001', 'MRK-GUE-001']]
    for day_offset in range(20):
        d = today - timedelta(days=day_offset)
        if d.weekday() >= 5:  # skip weekends
            continue
        for i, emp in enumerate(emp_list[:8]):
            site = site_list[i % len(site_list)]
            if not env['telecom.pointage.chantier'].search([
                ('employee_id', '=', emp.id), ('site_id', '=', site.id), ('date', '=', d.isoformat())
            ], limit=1):
                try:
                    p = env['telecom.pointage.chantier'].create({
                        'employee_id': emp.id, 'site_id': site.id,
                        'date': d.isoformat(),
                        'heure_debut': 8.0, 'heure_fin': 17.0 + (i % 3),
                        'prime_deplacement': 100 + (i * 20),
                    })
                    if day_offset > 2:
                        p.action_valider()
                except Exception:
                    pass

    # ═══════════════════════════════════════════════════════════════════════
    # 13. BULLETINS DE PAIE — Mars 2026
    # ═══════════════════════════════════════════════════════════════════════
    print("[14/15] Bulletins de paie...")

    for emp_name, emp in list(employees.items())[:10]:
        contract = env['hr.contract'].search([('employee_id', '=', emp.id), ('state', '=', 'open')], limit=1)
        salary = contract.wage if contract else 7000
        if not env['telecom.paie.bulletin'].search([
            ('employee_id', '=', emp.id), ('date_from', '=', '2026-03-01')
        ], limit=1):
            try:
                env['telecom.paie.bulletin'].create({
                    'employee_id': emp.id,
                    'salaire_base': salary,
                    'date_from': '2026-03-01',
                    'date_to': '2026-03-31',
                })
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════════════
    # 14. SITUATIONS DE TRAVAUX & DÉCOMPTES
    # ═══════════════════════════════════════════════════════════════════════
    print("[15/15] Situations & décomptes...")

    proj1 = projects.get('Déploiement FTTH Grand Casablanca - Phase 2')
    cont1 = contracts.get('CONT-IAM-2024-001')
    client1 = operators['Maroc Telecom (IAM)']

    if proj1 and cont1:
        for num, avancement, prev in [(1, 20, 0), (2, 45, 3000000), (3, 65, 6750000)]:
            if not env['telecom.situation'].search([
                ('project_id', '=', proj1.id), ('numero_situation', '=', num)
            ], limit=1):
                try:
                    env['telecom.situation'].create({
                        'project_id': proj1.id, 'contract_id': cont1.id,
                        'client_id': client1.id,
                        'numero_situation': num,
                        'date_situation': (today - relativedelta(months=4-num)).isoformat(),
                        'periode_du': f'2025-{num*3-2:02d}-01',
                        'periode_au': f'2025-{num*3:02d}-{28 if num*3==2 else 30}',
                        'montant_marche_ht': 15000000,
                        'taux_avancement_cumul': avancement,
                        'montant_situation_precedente': prev,
                    })
                except Exception:
                    pass

        # Décompte provisoire
        if not env['telecom.decompte'].search([('project_id', '=', proj1.id)], limit=1):
            try:
                env['telecom.decompte'].create({
                    'decompte_type': 'provisoire',
                    'project_id': proj1.id, 'contract_id': cont1.id,
                    'client_id': client1.id,
                    'montant_marche_ht': 15000000,
                    'montant_travaux_ht': 9750000,
                    'retenue_garantie_taux': 10.0,
                    'tva_taux': 20.0,
                })
            except Exception:
                pass

    # ═══════════════════════════════════════════════════════════════════════
    # COMMIT
    # ═══════════════════════════════════════════════════════════════════════
    cr.commit()
    print("\n══════════════════════════════════════════════════════")
    print("  DONNÉES DE DÉMONSTRATION CHARGÉES AVEC SUCCÈS")
    print("══════════════════════════════════════════════════════")
    print(f"  Partenaires  : {env['res.partner'].search_count([('partner_type', '!=', False)])}")
    print(f"  Sites        : {env['telecom.site'].search_count([])}")
    print(f"  Employés     : {env['hr.employee'].search_count([('telecom_technicien', '=', True)])}")
    print(f"  Équipements  : {env['telecom.equipment'].search_count([])}")
    print(f"  Véhicules    : {env['telecom.vehicle'].search_count([])}")
    print(f"  Interventions: {env['telecom.intervention'].search_count([])}")
    print(f"  Projets      : {env['project.project'].search_count([])}")
    print(f"  Contrats     : {env['telecom.contract'].search_count([])}")
    print(f"  AO           : {env['telecom.ao'].search_count([])}")
    print("══════════════════════════════════════════════════════")
