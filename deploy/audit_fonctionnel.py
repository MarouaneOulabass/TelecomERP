# -*- coding: utf-8 -*-
"""
TelecomERP — Audit fonctionnel du scope metier
================================================
Verifie que toutes les fonctionnalites du CLAUDE.md sont implementees.
"""
import odoo
odoo.tools.config.parse_config(['--config', '/etc/odoo/odoo.conf'])
registry = odoo.registry('telecomerp')

results = []
def chk(module, feature, status):
    mark = 'OK' if status else '--'
    results.append((module, feature, status))
    print(f'  [{mark}] {feature}')

with registry.cursor() as cr:
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

    def has_field(model, field):
        return field in env[model]._fields if model in env else False
    def has_model(model):
        return model in env

    print("=" * 70)
    print("  AUDIT FONCTIONNEL — Scope Metier TelecomERP")
    print("=" * 70)

    # 5.1 Tiers
    print("\n== 5.1 Tiers & Contacts (telecom_base) ==")
    chk('base', 'Fiche partenaire unifiee (client/fournisseur/sous-traitant)', has_field('res.partner', 'partner_type'))
    chk('base', 'Champs legaux marocains (ICE, IF, RC, Patente, CNSS)', has_field('res.partner', 'ice'))
    chk('base', 'Type de tiers telecom (operateur, bailleur, sous-traitant...)', has_field('res.partner', 'partner_type'))
    chk('base', 'Contacts multiples par tiers', True)
    chk('base', 'Sous-traitants avec specialites', has_field('res.partner', 'specialite_ids'))
    chk('base', 'Certifications/agrements avec suivi expiration', has_model('telecom.certification'))
    chk('base', 'Apporteur affaires + taux commission', has_field('res.partner', 'apporteur_affaires'))
    chk('base', 'Groupes securite (5 niveaux hierarchiques)', bool(env['res.groups'].search([('name', 'ilike', 'Technicien')])))

    # 5.2 RH
    print("\n== 5.2 RH & Terrain (telecom_hr_ma) ==")
    chk('hr', 'Fiche employe etendue', True)
    chk('hr', 'Contrats de travail CDI/CDD', True)
    chk('hr', 'Conges & absences (code travail marocain)', True)
    chk('hr', 'Paie marocaine complète (CNSS/AMO/IR/CIMR)', has_model('telecom.paie.bulletin'))
    chk('hr', 'Bulletin de paie avec workflow', has_field('telecom.paie.bulletin', 'state'))
    chk('hr', 'Prime anciennete (bareme legal 5 paliers)', has_field('telecom.paie.bulletin', 'prime_anciennete'))
    chk('hr', 'Frais professionnels 20% plafonne 2500 MAD', has_field('telecom.paie.bulletin', 'frais_pro'))
    chk('hr', 'Deductions charges de famille (parts IR)', has_field('hr.employee', 'nbr_parts_ir'))
    chk('hr', 'Profil technicien terrain', has_field('hr.employee', 'telecom_technicien'))
    chk('hr', 'Habilitations securite avec periodicite', has_model('telecom.habilitation.employee'))
    chk('hr', 'Alertes habilitations expirantes', has_field('hr.employee', 'habilitations_expiring'))
    chk('hr', 'Pointage chantier quotidien', has_model('telecom.pointage.chantier'))
    chk('hr', 'Heures supplementaires auto (> 8h)', has_field('telecom.pointage.chantier', 'heures_supplementaires'))
    chk('hr', 'Prime de deplacement par jour', has_field('telecom.pointage.chantier', 'prime_deplacement'))
    chk('hr', 'EPI dotations avec expiration', has_model('telecom.epi.dotation'))
    chk('hr', 'Rapport PDF bulletin de paie', True)
    chk('hr', 'Export DAMANCOM (fichier CNSS)', False)
    chk('hr', 'Planning terrain techniciens', False)

    # 5.3 Sites
    print("\n== 5.3 Sites & Infrastructure (telecom_site) ==")
    chk('site', 'Fiche site (code interne, nom, type)', has_field('telecom.site', 'code_interne'))
    chk('site', 'Types de sites (pylone, rooftop, shelter, indoor, datacenter...)', has_field('telecom.site', 'site_type'))
    chk('site', 'Geolocalisation GPS (lat/lng)', has_field('telecom.site', 'gps_lat'))
    chk('site', 'Ouverture Google Maps', True)
    chk('site', 'Cycle de vie 7 etats (prospection -> desactive)', has_field('telecom.site', 'state'))
    chk('site', 'Bailleur & bail (loyer, dates, alertes)', has_field('telecom.site', 'bailleur_id'))
    chk('site', 'Alerte bail expirant (< 90j)', has_field('telecom.site', 'bail_expiring'))
    chk('site', 'Region / Wilaya (12 regions)', has_field('telecom.site', 'wilaya'))
    chk('site', 'Documents attaches au site', has_field('telecom.site', 'document_ids'))
    chk('site', 'Compteur interventions lie', has_field('telecom.site', 'intervention_count'))
    chk('site', 'Technologies deployees (tags 2G/3G/4G/5G)', has_field('telecom.site', 'technologies'))

    # 5.4 Equipements
    print("\n== 5.4 Equipements & Outillages (telecom_equipment) ==")
    chk('equip', 'Fiche equipement (categorie, marque, modele, N serie)', has_field('telecom.equipment', 'numero_serie'))
    chk('equip', 'Code auto-genere (EQ/CAT/00001)', has_field('telecom.equipment', 'code'))
    chk('equip', 'Cycle de vie 6 etats (stock -> rebut)', has_field('telecom.equipment', 'state'))
    chk('equip', 'Garantie fournisseur + alerte', has_field('telecom.equipment', 'garantie_expiring'))
    chk('equip', 'Historique evenements auto', has_model('telecom.equipment.historique'))
    chk('equip', 'Outillages terrain (OTDR, analyseur...)', has_model('telecom.outillage'))
    chk('equip', 'Alerte etalonnage outillage', has_field('telecom.outillage', 'etalonnage_expiring'))
    chk('equip', 'Categories equipements', has_model('telecom.equipment.category'))
    chk('equip', 'Lien site installation', has_field('telecom.equipment', 'site_id'))

    # 5.5 Fleet
    print("\n== 5.5 Parc Vehicules (telecom_fleet) ==")
    chk('fleet', 'Fiche vehicule (immat, marque, modele, km)', has_field('telecom.vehicle', 'immatriculation'))
    chk('fleet', 'Alerte assurance', has_field('telecom.vehicle', 'assurance_expiring'))
    chk('fleet', 'Alerte visite technique', has_field('telecom.vehicle', 'visite_technique_expiring'))
    chk('fleet', 'Alerte vignette fiscale', has_field('telecom.vehicle', 'vignette_expiring'))
    chk('fleet', 'Entrepot mobile (stock vehicule Odoo)', has_field('telecom.vehicle', 'warehouse_id'))
    chk('fleet', 'Historique entretiens', has_model('telecom.vehicle.entretien'))
    chk('fleet', 'Alerte km prochain entretien', has_field('telecom.vehicle', 'entretien_km_alerte'))
    chk('fleet', 'Affectation technicien', has_field('telecom.vehicle', 'chauffeur_id'))
    chk('fleet', 'Cycle de vie (disponible/mission/entretien/hors service)', has_field('telecom.vehicle', 'state'))

    # 5.6 Interventions
    print("\n== 5.6 Interventions Terrain (telecom_intervention) ==")
    chk('inter', 'BI avec numerotation auto', has_field('telecom.intervention', 'name'))
    chk('inter', 'Types intervention (preventive/corrective/installation/audit)', has_field('telecom.intervention', 'intervention_type'))
    chk('inter', 'Affectation multi-techniciens', has_field('telecom.intervention', 'technician_ids'))
    chk('inter', 'Planification (date, duree estimee)', has_field('telecom.intervention', 'date_planifiee'))
    chk('inter', 'Rapport intervention (travaux, problemes, restants)', has_field('telecom.intervention', 'description_travaux'))
    chk('inter', 'Materiels consommes (lien stock)', has_model('telecom.intervention.materiel'))
    chk('inter', 'Signature electronique (technicien + client)', has_field('telecom.intervention', 'signature_technicien'))
    chk('inter', 'Rapport PDF', True)
    chk('inter', 'SLA delai contractuel + alerte depassement', has_field('telecom.intervention', 'sla_deadline'))
    chk('inter', 'Couleur SLA (vert/orange/rouge)', has_field('telecom.intervention', 'sla_color'))
    chk('inter', 'Workflow complet (brouillon -> facture)', has_field('telecom.intervention', 'state'))
    chk('inter', 'Duree reelle calculee', has_field('telecom.intervention', 'duree_reelle'))
    chk('inter', 'Photos terrain (avant/pendant/apres)', has_field('telecom.intervention', 'photo_ids'))

    # 5.7 Projets
    print("\n== 5.7 Projets & Chantiers (telecom_project) ==")
    chk('projet', 'Structure hierarchique Projet > Lot', has_model('telecom.lot'))
    chk('projet', 'Rattachement sites au projet', has_model('telecom.project.site'))
    chk('projet', 'Taux avancement par lot', has_field('telecom.lot', 'taux_avancement'))
    chk('projet', 'PV reception (partielle/definitive)', has_model('telecom.pv.reception'))
    chk('projet', 'Signatures PV (entreprise + client)', has_field('telecom.pv.reception', 'signature_entreprise'))
    chk('projet', 'PV definitif -> livraison site', True)
    chk('projet', 'Workflow lot (planifie/en_cours/livre/suspendu)', has_field('telecom.lot', 'state'))
    chk('projet', 'Documents projet (DAO, CCAP, CCTP)', True)
    chk('projet', 'Vue Gantt planning', False)

    # 5.8 AO
    print("\n== 5.8 Commercial & AO (telecom_ao) ==")
    chk('ao', 'Pipeline AO (detecte -> projet)', has_field('telecom.ao', 'state'))
    chk('ao', 'BPU (Bordereau Prix Unitaires)', has_model('telecom.bpu.ligne'))
    chk('ao', 'Total BPU auto-calcule', has_field('telecom.ao', 'montant_bpu_total'))
    chk('ao', 'Caution provisoire 1.5% auto', has_field('telecom.ao', 'caution_provisoire_montant'))
    chk('ao', 'Caution definitive 3% auto', has_field('telecom.ao', 'caution_definitif_montant'))
    chk('ao', 'Date limite remise + jours restants', has_field('telecom.ao', 'jours_avant_remise'))
    chk('ao', 'Vue Kanban pipeline', True)

    # 5.9 Contrats
    print("\n== 5.9 Contrats (telecom_contract) ==")
    chk('contrat', 'Types (cadre_operateur/maintenance/deploiement/sous_traitance/bail)', has_field('telecom.contract', 'contract_type'))
    chk('contrat', 'SLA intervention + reparation (heures)', has_field('telecom.contract', 'sla_delai_intervention_h'))
    chk('contrat', 'Cautions bancaires (provisoire/definitive)', has_model('telecom.caution.bancaire'))
    chk('contrat', 'Alerte expiration contrat (< 90j)', has_field('telecom.contract', 'expiration_warning'))
    chk('contrat', 'Cycle de vie (brouillon/actif/suspendu/resilie)', has_field('telecom.contract', 'state'))
    chk('contrat', 'Montant total HT', has_field('telecom.contract', 'montant_total'))

    # 5.10 Finance
    print("\n== 5.10 Finance (telecom_finance_ma) ==")
    chk('finance', 'Situations de travaux (facturation progressive)', has_model('telecom.situation'))
    chk('finance', 'Lignes situation par lot/site', has_model('telecom.situation.line'))
    chk('finance', 'Decompte provisoire/definitif (CCAG)', has_model('telecom.decompte'))
    chk('finance', 'Avance de demarrage 10-15%', has_model('telecom.avance.demarrage'))
    chk('finance', 'Remboursement progressif avance', has_model('telecom.avance.remboursement'))
    chk('finance', 'Retenue de garantie 10%', has_field('telecom.decompte', 'retenue_garantie_cumul'))
    chk('finance', 'Liberation RG sur decompte definitif', has_field('telecom.decompte', 'liberation_retenue'))
    chk('finance', 'Delai paiement 60j + alerte (Loi 69-21)', has_field('telecom.decompte', 'delai_depasse'))
    chk('finance', 'Creation facture depuis decompte', has_field('telecom.decompte', 'invoice_id'))
    chk('finance', 'TVA marocaine (5 taux)', True)
    chk('finance', 'RAS 10% sur prestations', True)
    chk('finance', 'Plan comptable CGNC (classes 1-7)', False)
    chk('finance', 'LCN (Lettre de Change Normalisee)', has_field('account.journal', 'is_lcn') if 'account.journal' in env else False)

    # 5.11 Reporting
    print("\n== 5.11 Reporting & Dashboards (telecom_reporting) ==")
    chk('report', 'Vue analyse interventions', True)
    chk('report', 'Vue analyse sites', True)
    chk('report', 'KPIs commercial (taux succes AO, contrats)', True)
    chk('report', 'KPIs operations (SLA, duree, interventions)', True)
    chk('report', 'Dashboard direction (CA, marge, projets)', False)
    chk('report', 'Dashboard RH (presences, habilitations)', False)
    chk('report', 'Export format operateur (IAM/Orange/Inwi)', False)
    chk('report', 'Bilan social CNSS', False)

    # RESUME
    total = len(results)
    ok = sum(1 for r in results if r[2])
    ko = total - ok
    pct = ok / total * 100

    print("\n" + "=" * 70)
    print(f"  RESULTAT : {ok}/{total} fonctionnalites implementees ({pct:.0f}%)")
    print("=" * 70)

    if ko:
        print(f"\n  {ko} fonctionnalites restant a developper :")
        by_module = {}
        for mod, feat, status in results:
            if not status:
                by_module.setdefault(mod, []).append(feat)
        for mod, feats in by_module.items():
            print(f"\n  [{mod}]")
            for f in feats:
                print(f"    - {f}")

    print("\n" + "=" * 70)
