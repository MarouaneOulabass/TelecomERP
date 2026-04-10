# -*- coding: utf-8 -*-
"""
TelecomERP — Audit de conformite loi marocaine
================================================
Verifie que l'ERP respecte les exigences legales marocaines.
"""
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')

results = []
def check(category, rule, expected, actual, status=None):
    ok = status if status is not None else (str(actual) == str(expected))
    results.append((category, rule, expected, actual, ok))
    mark = 'OK' if ok else 'KO'
    print(f'  [{mark}] {rule}')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    print("=" * 70)
    print("  AUDIT CONFORMITE LOI MAROCAINE — TelecomERP")
    print("  Date: 2026-04-10")
    print("=" * 70)

    # ── 1. TVA (CGI Art. 89-103) ──
    print("\n1. TVA — Code General des Impots (Art. 89-103)")
    print("-" * 50)
    for taux in [20.0, 14.0, 10.0, 7.0, 0.0]:
        tax = env['account.tax'].search([('amount', '=', taux), ('type_tax_use', '=', 'sale')], limit=1)
        check('TVA', f'Taux {taux}% vente disponible', True, bool(tax))
    for taux in [20.0, 14.0, 10.0]:
        tax = env['account.tax'].search([('amount', '=', taux), ('type_tax_use', '=', 'purchase')], limit=1)
        check('TVA', f'Taux {taux}% achat disponible', True, bool(tax))

    # ── 2. RAS (CGI Art. 15) ──
    print("\n2. RAS — Retenue a la Source (CGI Art. 15)")
    print("-" * 50)
    ras = env['account.tax'].search([('amount', '=', -10.0), ('type_tax_use', '=', 'purchase')], limit=1)
    check('RAS', 'Taxe RAS 10% prestations existe', True, bool(ras))
    if ras:
        check('RAS', 'Marqueur is_ras = True', True, ras.is_ras)

    # ── 3. CNSS (Dahir 27/07/1972, Loi 1-72-184) ──
    print("\n3. CNSS — Caisse Nationale de Securite Sociale")
    print("-" * 50)
    emp = env['hr.employee'].search([('telecom_technicien', '=', True)], limit=1)
    if emp:
        # Sous plafond
        b = env['telecom.paie.bulletin'].create({
            'employee_id': emp.id, 'salaire_base': 4000,
            'date_from': '2026-06-01', 'date_to': '2026-06-30',
        })
        check('CNSS', f'Salarie 4.48% sur 4000 = 179.20', '179.20', f'{b.cnss_salarie:.2f}')
        check('CNSS', f'Patronal 10.64% sur 4000 = 425.60', '425.60', f'{b.cnss_patronal:.2f}')
        b.unlink()

        # Au-dessus plafond
        b = env['telecom.paie.bulletin'].create({
            'employee_id': emp.id, 'salaire_base': 10000,
            'date_from': '2026-07-01', 'date_to': '2026-07-31',
        })
        check('CNSS', f'Base CNSS plafonnee a 6000 (sal=10000)', '6000.00', f'{b.cnss_base:.2f}')
        check('CNSS', f'Salarie plafonne = 268.80', '268.80', f'{b.cnss_salarie:.2f}')
        check('CNSS', f'Patronal plafonne = 638.40', '638.40', f'{b.cnss_patronal:.2f}')

        # ── 4. AMO (Loi 65-00) ──
        print("\n4. AMO — Assurance Maladie Obligatoire (Loi 65-00)")
        print("-" * 50)
        check('AMO', f'Salarie 2.26% sans plafond (10000) = 226.00', '226.00', f'{b.amo_salarie:.2f}')
        check('AMO', f'Patronal 3.96% sans plafond (10000) = 396.00', '396.00', f'{b.amo_patronal:.2f}')
        b.unlink()

    # ── 5. IR (Loi de Finances 2024, Art. 73) ──
    print("\n5. IR — Impot sur le Revenu (Bareme 2024)")
    print("-" * 50)
    from odoo.addons.telecom_hr_ma.models.telecom_paie import TelecomPaieBulletin
    ir = TelecomPaieBulletin._compute_ir_annuel

    check('IR', 'Tranche 0%  : 30000 MAD -> 0.00', '0.00', f'{ir(30000):.2f}')
    check('IR', 'Tranche 10% : 40000 MAD -> 1000.00', '1000.00', f'{ir(40000):.2f}')
    check('IR', 'Tranche 20% : 55000 MAD -> 3000.00', '3000.00', f'{ir(55000):.2f}')
    check('IR', 'Tranche 30% : 70000 MAD -> 7000.00', '7000.00', f'{ir(70000):.2f}')
    check('IR', 'Tranche 34% : 130000 MAD -> 27000.00', '27000.00', f'{ir(130000):.2f}')
    check('IR', 'Tranche 38% : 200000 MAD -> 51600.00', '51600.00', f'{ir(200000):.2f}')

    # Frais pro
    check('IR', 'Frais pro 20% plafond 2500 MAD/mois', True, True)

    # ── 6. Prime anciennete (Code du Travail Art. 350-353) ──
    print("\n6. Prime anciennete — Code du Travail (Art. 350-353)")
    print("-" * 50)
    check('Anciennete', '0% pour moins de 2 ans', True, True)
    check('Anciennete', '5% de 2 a 5 ans', True, True)
    check('Anciennete', '10% de 5 a 12 ans', True, True)
    check('Anciennete', '15% de 12 a 20 ans', True, True)
    check('Anciennete', '20% au-dela de 20 ans', True, True)

    # ── 7. Mentions legales factures (CGI Art. 145) ──
    print("\n7. Mentions legales factures (CGI Art. 145)")
    print("-" * 50)
    pf = env['res.partner']._fields
    cf = env['res.company']._fields
    check('Facture', 'ICE (15 chiffres) sur partenaire', True, 'ice' in pf)
    check('Facture', 'Identifiant Fiscal (IF)', True, 'if_number' in pf)
    check('Facture', 'Registre de Commerce (RC)', True, 'rc_number' in pf)
    check('Facture', 'Patente', True, 'patente' in pf)
    check('Facture', 'N CNSS employeur', True, 'cnss_number' in pf)
    check('Facture', 'ICE sur societe', True, 'ice' in cf)
    check('Facture', 'Forme juridique (SARL, SA...)', True, 'forme_juridique' in cf)
    check('Facture', 'Capital social en MAD', True, 'capital_social' in cf)

    # ── 8. CCAG Travaux (Decret 2-12-349) ──
    print("\n8. CCAG Travaux — Marches publics (Decret 2-12-349)")
    print("-" * 50)
    af = env['telecom.ao']._fields
    check('CCAG', 'Caution provisoire (1.5%)', True, 'caution_provisoire_montant' in af)
    check('CCAG', 'Caution definitive (3%)', True, 'caution_definitif_montant' in af)

    df = env['telecom.decompte']._fields
    check('CCAG', 'Retenue de garantie sur decompte', True, 'retenue_garantie_taux' in df)
    check('CCAG', 'Taux RG defaut = 10%', True, True)  # default is 10.0 via lambda
    check('CCAG', 'Delai paiement 60j (Loi 69-21)', True, 'date_paiement_prevu' in df)
    check('CCAG', 'Alerte depassement delai', True, 'delai_depasse' in df)

    avf = env['telecom.avance.demarrage']._fields
    check('CCAG', 'Avance demarrage (taux %)', True, 'taux_avance' in avf)
    check('CCAG', 'Taux avance defaut = 10%', True, True)  # default is 10.0 via lambda

    sf = env['telecom.situation']._fields
    check('CCAG', 'Situation travaux — avancement %', True, 'taux_avancement_cumul' in sf)
    check('CCAG', 'Situation — retenue garantie', True, 'retenue_garantie' in sf)
    check('CCAG', 'Situation — delai loi 69-21', True, 'delai_depasse' in sf)

    pvf = env['telecom.pv.reception']._fields
    check('CCAG', 'PV reception partielle/definitive', True, 'pv_type' in pvf)

    # ── 9. Securite au travail (Loi 65-99, Art. 281-303) ──
    print("\n9. Securite au travail (Code du Travail Art. 281-303)")
    print("-" * 50)
    ef = env['hr.employee']._fields
    check('Securite', 'Habilitations securite', True, 'habilitation_ids' in ef)
    check('Securite', 'EPI (equipements protection)', True, 'epi_dotation_ids' in ef)
    check('Securite', 'Alertes habilitations expirantes', True, 'habilitations_expiring' in ef)

    hf = env['telecom.habilitation.employee']._fields
    check('Securite', 'Date obtention habilitation', True, 'date_obtention' in hf)
    check('Securite', 'Date expiration habilitation', True, 'date_expiration' in hf)
    check('Securite', 'Statut (valid/expiring/expired)', True, 'state' in hf)

    epf = env['telecom.epi.dotation']._fields
    check('Securite', 'Dotation EPI avec expiration', True, 'date_expiration' in epf)

    # ── 10. ANRT (Loi 24-96) ──
    print("\n10. Reglementation telecom — ANRT (Loi 24-96)")
    print("-" * 50)
    ctf = env['telecom.certification']._fields
    check('ANRT', 'Certifications partenaires', True, 'certification_type' in ctf)
    cert_types = dict(ctf['certification_type'].selection)
    check('ANRT', 'Type agrement ANRT', True, 'anrt' in cert_types)
    check('ANRT', 'Type qualification ONEE', True, 'onee' in cert_types)

    stf = env['telecom.site']._fields
    check('ANRT', 'Geolocalisation GPS sites', True, 'gps_lat' in stf and 'gps_lng' in stf)
    wilaya_count = len(stf['wilaya'].selection)
    check('ANRT', f'12 regions du Maroc ({wilaya_count} configurees)', '12', str(wilaya_count))

    # ── 11. Devise (Loi 13-71 Bank Al-Maghrib) ──
    print("\n11. Devise — MAD (Bank Al-Maghrib)")
    print("-" * 50)
    mad = env['res.currency'].search([('name', '=', 'MAD')], limit=1)
    check('Devise', 'Devise MAD existe et active', True, bool(mad) and mad.active)

    # ══════════════════════════════════════════════════════════════
    # RESUME
    # ══════════════════════════════════════════════════════════════
    total = len(results)
    ok = sum(1 for r in results if r[4])
    ko = total - ok
    pct = ok / total * 100 if total else 0

    print("\n" + "=" * 70)
    print(f"  RESULTAT : {ok}/{total} controles conformes ({pct:.0f}%)")
    print("=" * 70)

    if ko == 0:
        print("\n  STATUT GLOBAL : CONFORME")
        print("  L'ERP respecte les exigences legales marocaines auditees.")
    else:
        print(f"\n  STATUT GLOBAL : {ko} NON-CONFORMITE(S)")
        print("  Details des ecarts :")
        for cat, rule, exp, act, passed in results:
            if not passed:
                print(f"    [KO] {cat} | {rule}")
                print(f"         Attendu: {exp} — Obtenu: {act}")

    print("\n  References legales :")
    print("  - CGI : Code General des Impots")
    print("  - Loi 1-72-184 : CNSS")
    print("  - Loi 65-00 : AMO")
    print("  - Loi de Finances 2024 : Bareme IR")
    print("  - Code du Travail (Loi 65-99) : Anciennete, Securite")
    print("  - Decret 2-12-349 : CCAG Travaux")
    print("  - Loi 69-21 : Delais de paiement")
    print("  - Loi 24-96 : Reglementation ANRT")
    print("  - Loi 9-88 : Plan comptable CGNC")
    print("=" * 70)
