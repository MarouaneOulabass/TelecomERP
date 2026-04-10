# Guide d'Administration des Tests BDD — TelecomERP

> **Public cible** : Équipe métier, chefs de projet, responsables fonctionnels
> **Prérequis** : Un compte GitHub et un navigateur web

---

## Qu'est-ce qu'un test BDD ?

Un test BDD est une **règle métier écrite en français** dans un fichier `.feature`. Chaque règle décrit un comportement attendu du système sous forme de scénario :

```gherkin
Scénario: Un site livré peut être désactivé
  Soit un site à l'état "livre"
  Quand je passe le site à l'état "desactive"
  Alors l'état du site est "desactive"
```

**Si ce test échoue = le système ne respecte pas la règle métier = bug à corriger.**

---

## Où sont les fichiers de test ?

Chaque module a ses tests dans un dossier `tests/features/` :

```
custom_addons/
├── telecom_site/tests/features/
│   ├── site_creation.feature      ← Création de sites
│   ├── site_bail.feature          ← Alertes bail / bailleur
│   └── site_cycle_vie.feature     ← Transitions d'état
│
├── telecom_intervention/tests/features/
│   ├── intervention_workflow.feature  ← Workflow BI
│   └── intervention_sla.feature       ← Règles SLA
│
├── telecom_hr_ma/tests/features/
│   ├── paie_cnss_amo.feature      ← Calculs CNSS/AMO
│   ├── paie_ir.feature            ← Barème IR 2024
│   ├── paie_anciennete.feature    ← Prime ancienneté
│   ├── habilitation.feature       ← Habilitations sécurité
│   └── epi_pointage.feature       ← EPI et pointage
│
├── telecom_finance_ma/tests/features/
│   ├── decompte_calculs.feature   ← Calculs CCAG
│   ├── decompte_workflow.feature  ← Workflow décomptes
│   └── avance_situation.feature   ← Avances et situations
│
├── telecom_equipment/tests/features/
│   ├── equipement.feature         ← Cycle de vie équipement
│   └── equipement_actions.feature ← Actions métier
│
├── telecom_fleet/tests/features/
│   └── vehicule.feature           ← Véhicules et alertes
│
├── telecom_ao/tests/features/
│   ├── ao_pipeline.feature        ← Pipeline appels d'offres
│   └── ao_cautions_bpu.feature    ← Cautions et BPU
│
├── telecom_contract/tests/features/
│   └── contrat_cycle_vie.feature  ← Contrats et cautions
│
├── telecom_project/tests/features/
│   ├── projet_structure.feature   ← Projets, lots, sites
│   └── pv_reception.feature       ← PV de réception
│
├── telecom_base/tests/features/
│   └── partenaire_marocain.feature ← Partenaires et ICE
│
├── telecom_localization_ma/tests/features/
│   └── tva_ras.feature            ← TVA et RAS
│
└── telecom_reporting/tests/features/
    ├── kpi_commercial.feature     ← KPIs commerciaux
    └── kpi_operations.feature     ← KPIs opérations
```

---

## Comment ajouter un scénario de test ?

### Étape 1 : Ouvrir le fichier `.feature` sur GitHub

1. Aller sur https://github.com/MarouaneOulabass/TelecomERP
2. Naviguer vers le fichier `.feature` du module concerné
3. Cliquer sur l'icône **crayon** (Edit) en haut à droite

### Étape 2 : Écrire le scénario en français

Ajouter un nouveau scénario en respectant cette structure :

```gherkin
  Scénario: [Description courte de la règle métier]
    Soit [état initial / contexte]
    Quand [action déclenchante]
    Alors [résultat attendu]
    Et [résultat complémentaire]
```

### Étape 3 : Sauvegarder via Pull Request

1. En bas de la page, sélectionner **"Create a new branch"**
2. Donner un nom : `ajout-test-nom-du-test`
3. Cliquer sur **"Propose changes"**
4. Créer la **Pull Request**

L'équipe de développement recevra la notification et implémentera le code correspondant.

---

## Mots-clés disponibles

| Mot-clé | Usage | Exemple |
|---------|-------|---------|
| `Soit` | Définir le contexte initial | `Soit un site à l'état "livre"` |
| `Quand` | Décrire l'action | `Quand je passe le site à l'état "desactive"` |
| `Alors` | Vérifier le résultat | `Alors l'état du site est "desactive"` |
| `Et` | Ajouter une condition/résultat | `Et la date est renseignée` |

### Pour les scénarios paramétrés (avec tableau de valeurs) :

```gherkin
  Plan du Scénario: CNSS salarié selon salaire
    Soit un bulletin de paie avec un salaire de base de "<salaire>" MAD
    Alors le CNSS salarié est "<cnss>" MAD

    Exemples:
      | salaire | cnss   |
      | 3000    | 134.40 |
      | 6000    | 268.80 |
      | 10000   | 268.80 |
```

---

## Phrases réutilisables (steps existants)

### Contexte général
| Phrase | Description |
|--------|-------------|
| `Soit la date du jour est "2024-03-01"` | Simule une date |
| `Soit la société courante est initialisée` | Initialise la société |

### Sites
| Phrase | Description |
|--------|-------------|
| `Soit un site "{nom}" avec le code "{code}" existe` | Crée un site |
| `Quand je passe le site à l'état "{état}"` | Change l'état |
| `Alors l'état du site est "{état}"` | Vérifie l'état |

### Interventions
| Phrase | Description |
|--------|-------------|
| `Quand je planifie le BI` | Planifie l'intervention |
| `Quand je démarre le BI` | Démarre l'intervention |
| `Quand je termine le BI` | Termine l'intervention |
| `Quand je valide le BI` | Valide l'intervention |

### Paie
| Phrase | Description |
|--------|-------------|
| `Soit un bulletin de paie avec un salaire de base de "{montant}" MAD` | Crée un bulletin |
| `Alors le CNSS salarié est "{montant}" MAD` | Vérifie le calcul CNSS |
| `Alors l'AMO salarié est "{montant}" MAD` | Vérifie le calcul AMO |
| `Alors le net à payer est "{montant}" MAD` | Vérifie le net |

### Erreurs attendues
| Phrase | Description |
|--------|-------------|
| `Alors une erreur utilisateur est levée indiquant "{texte}"` | Vérifie qu'une erreur est bien bloquante |
| `Alors une erreur de validation est levée indiquant "{texte}"` | Vérifie une contrainte |
| `Alors une erreur d'intégrité est levée` | Vérifie un doublon refusé |

---

## Comment lancer les tests ?

### Depuis le serveur (pour les devs)
```bash
ssh root@65.108.146.17
cd /opt/telecomerp
bash bin/pre-deploy-tests.sh
```

### Un module spécifique
```bash
bash bin/pre-deploy-tests.sh --module site
bash bin/pre-deploy-tests.sh --module paie
```

### Avec rapport HTML
```bash
bash bin/pre-deploy-tests.sh --report
```

---

## Couverture actuelle : 359 scénarios

| Module | Scénarios | Fichiers |
|--------|-----------|----------|
| telecom_site | 36 | 3 fichiers |
| telecom_intervention | 37 | 2 fichiers |
| telecom_hr_ma | 38 | 5 fichiers |
| telecom_finance_ma | 29 | 3 fichiers |
| telecom_equipment | 13 | 2 fichiers |
| telecom_fleet | 8 | 1 fichier |
| telecom_ao | 21 | 2 fichiers |
| telecom_contract | 21 | 1 fichier |
| telecom_project | 22 | 2 fichiers |
| telecom_base | 9 | 1 fichier |
| telecom_localization_ma | 10 | 1 fichier |
| telecom_reporting | 17 | 2 fichiers |
| **Total** | **359** | **25 fichiers** |

---

## Règle d'or

> **Un scénario BDD = une règle métier = un test automatisé.**
> Si la règle n'est pas dans un fichier `.feature`, elle n'existe pas pour le système.

---

## Workflow recommandé

```
1. Le MÉTIER écrit un scénario dans un .feature    (Pull Request)
2. Les DEVS implémentent le step definition         (Code Python)
3. Les TESTS passent                                 (CI/CD)
4. La fonctionnalité est VALIDÉE                     (Merge)
```

Ce workflow garantit que **le métier définit le comportement** et que **le code le respecte**.
