# TelecomERP — Guide Testeurs

> **Bienvenue dans l'equipe de test TelecomERP !**
> Ce document vous donne tout ce qu'il faut pour acceder a l'ERP, comprendre les modules, et contribuer aux tests.

---

## Acces

| | |
|---|---|
| **URL** | **https://erp.kleanse.fr** |
| **Login** | `admin` |
| **Password** | `admin` *(a changer apres 1ere connexion)* |
| **Langues** | Francais (defaut), English, العربية |
| **Code source** | https://github.com/MarouaneOulabass/TelecomERP |

Pour changer de langue : cliquez sur votre nom en haut a droite → Mon profil → Langue.

---

## Les 12 modules — A quoi sert chacun ?

### Fondations

| Module | Menu dans Odoo | Ca fait quoi |
|--------|---------------|-------------|
| **Sites** | Sites & Infrastructure | La carte de tous nos sites telecom (pylones, rooftops, shelters). Chaque site a ses coordonnees GPS, son bailleur, ses documents, et son cycle de vie de la prospection a la desactivation. |
| **Interventions** | Interventions | Les bons d'intervention terrain. On planifie, on envoie le technicien, il fait son rapport avec photos, le chef valide, on facture. Avec suivi SLA (delai contractuel). |
| **RH & Paie** | RH & Terrain | Tout le volet RH marocain : bulletins de paie (CNSS, AMO, IR bareme 2024), habilitations securite des techniciens, dotations EPI (casque, harnais...), pointage chantier quotidien. |

### Operations

| Module | Menu dans Odoo | Ca fait quoi |
|--------|---------------|-------------|
| **Equipements** | Equipements | L'inventaire de tout le materiel deploye : antennes, eNodeB, OLT, batteries. Chaque equipement a son N° de serie, son historique, et des alertes de garantie. Aussi les outillages terrain (OTDR, soudeuses). |
| **Vehicules** | Flotte Terrain | Le parc de vehicules : immatriculation, affectation technicien, alertes assurance/visite technique/vignette, historique entretiens, et meme un stock embarque par vehicule. |
| **Projets** | Projets | La structure des chantiers : Projet → Lots → Sites. Avec taux d'avancement automatique, PV de reception (signatures electroniques), et suivi par lot. |

### Commercial & Finance

| Module | Menu dans Odoo | Ca fait quoi |
|--------|---------------|-------------|
| **Appels d'Offres** | Commercial | Le pipeline commercial : on detecte un AO, on etudie, on soumissionne, on gagne (ou pas). Avec BPU (Bordereau Prix Unitaires) et calcul auto des cautions (1.5% provisoire, 3% definitive). |
| **Contrats** | Contrats | Les contrats avec les operateurs : type (cadre, maintenance, deploiement), SLA, cautions bancaires, alertes d'expiration. |
| **Finance** | Finance | La facturation progressive des marches publics : situations de travaux, decomptes CCAG (retenue de garantie 10%, delai 60 jours loi 69-21), avances de demarrage. |

### Transversal

| Module | Menu dans Odoo | Ca fait quoi |
|--------|---------------|-------------|
| **Localisation Maroc** | *(integre partout)* | TVA marocaine (20/14/10/7/0%), RAS 10%, plan comptable CGNC, mentions legales factures (ICE, IF, RC). |
| **Reporting** | Reporting | Dashboards direction (CA, sites, interventions), dashboards RH (presences, habilitations), export format operateur (IAM/Orange/Inwi), bilan social CNSS. |
| **Tests BDD** | Tests BDD | L'interface pour voir et gerer les 359 tests automatises. C'est la que vous intervenez ! |

---

## Comment tester ?

### 1. Explorez librement

Connectez-vous et cliquez partout. Creez des sites, des interventions, des bulletins de paie. Essayez les workflows (planifier → demarrer → terminer → valider). Cassez des trucs — c'est fait pour ca.

### 2. Verifiez les regles metier

Quelques exemples a tester :

| Test | Comment | Resultat attendu |
|------|---------|-------------------|
| ICE invalide | Creez un partenaire avec ICE "12345" (< 15 chiffres) | Erreur de validation |
| CNSS plafond | Creez un bulletin avec salaire 10 000 MAD | Base CNSS = 6 000 (plafonnee) |
| SLA depasse | Creez un BI planifie il y a 3 jours avec SLA 48h | Indicateur rouge |
| Caution AO | Creez un AO a 1 000 000 MAD | Caution provisoire = 15 000 (1.5%) |
| Doublon site | Creez 2 sites avec le meme code interne | Erreur d'integrite |

### 3. Signalez les bugs

Si quelque chose ne marche pas comme prevu :
1. Notez l'ecran/menu ou ca se passe
2. Decrivez ce que vous avez fait
3. Decrivez ce qui s'est passe vs ce qui etait attendu
4. Creez une **Issue** sur https://github.com/MarouaneOulabass/TelecomERP/issues

---

## Comment modifier les tests ?

Les tests sont ecrits en **francais** dans des fichiers `.feature`. Pas besoin de coder.

### Ou sont les tests ?

Sur GitHub : https://github.com/MarouaneOulabass/TelecomERP

Chemin : `custom_addons/telecom_XXX/tests/features/`

Exemple : `custom_addons/telecom_site/tests/features/site_creation.feature`

### A quoi ressemble un test ?

```gherkin
Scenario: Creation d'un site avec les champs obligatoires
  Soit la societe courante est initialisee
  Quand je cree un site avec le code "TLM-001" et le nom "Site Casablanca"
  Alors le site est cree avec succes
  Et l'etat du site est "prospection"
```

**C'est du francais.** Chaque scenario = une regle metier.

### Comment ajouter un test ?

1. Allez sur GitHub → naviguez vers le fichier `.feature` du module concerne
2. Cliquez sur le **crayon** (Edit) en haut a droite
3. Ajoutez votre scenario a la fin du fichier :

```gherkin
  Scenario: [Votre regle metier ici]
    Soit [contexte initial]
    Quand [action]
    Alors [resultat attendu]
```

4. En bas, selectionnez **"Create a new branch"**
5. Donnez un nom : `test-ma-nouvelle-regle`
6. Cliquez **"Propose changes"** puis **"Create Pull Request"**

L'equipe dev recevra une notification et implementera le code.

### Les mots-cles

| Mot | Usage | Exemple |
|-----|-------|---------|
| `Soit` | Contexte initial | `Soit un site a l'etat "livre"` |
| `Quand` | Action | `Quand je passe le site a l'etat "desactive"` |
| `Alors` | Verification | `Alors l'etat du site est "desactive"` |
| `Et` | Condition supplementaire | `Et la date est renseignee` |

### Fichiers de test par module

| Module | Fichier(s) | Nb tests |
|--------|-----------|----------|
| Sites | `site_creation.feature`, `site_bail.feature`, `site_cycle_vie.feature` | 36 |
| Interventions | `intervention_workflow.feature`, `intervention_sla.feature` | 37 |
| RH / Paie | `paie_cnss_amo.feature`, `paie_ir.feature`, `paie_anciennete.feature`, `habilitation.feature`, `epi_pointage.feature` | 38 |
| Finance | `decompte_calculs.feature`, `decompte_workflow.feature`, `avance_situation.feature` | 29 |
| Equipements | `equipement.feature`, `equipement_actions.feature` | 13 |
| Vehicules | `vehicule.feature` | 8 |
| AO | `ao_pipeline.feature`, `ao_cautions_bpu.feature` | 21 |
| Contrats | `contrat_cycle_vie.feature` | 21 |
| Projets | `projet_structure.feature`, `pv_reception.feature` | 22 |
| Partenaires | `partenaire_marocain.feature` | 9 |
| Localisation | `tva_ras.feature` | 10 |
| Reporting | `kpi_commercial.feature`, `kpi_operations.feature` | 17 |
| **Total** | **25 fichiers** | **359** |

---

## Donnees de demo chargees

L'ERP contient deja des donnees realistes pour tester :

- **4 operateurs** : Maroc Telecom, Orange, Inwi, ONEE
- **5 sous-traitants** avec specialites et certifications
- **25 sites telecom** repartis sur les 12 regions du Maroc (GPS reel)
- **20 techniciens** avec habilitations et EPI
- **20 equipements** installes (antennes, eNodeB, OLT...)
- **8 vehicules** avec historique entretiens
- **4 projets** avec lots et sites rattaches
- **6 appels d'offres** dans le pipeline
- **5 contrats** operateurs actifs
- **15 interventions** a differents stades
- **~130 pointages** sur les 20 derniers jours
- **10 bulletins de paie** (mars 2026)

---

## Contacts

| Qui | Pour quoi |
|-----|-----------|
| **Marouane** | Questions fonctionnelles, acces, priorites |
| **GitHub Issues** | Bugs et demandes d'amelioration |
| **Pull Requests** | Propositions de nouveaux tests |

---

*Bons tests !*
