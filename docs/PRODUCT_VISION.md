# PRODUCT_VISION.md

> Document fondateur du produit. Toutes les décisions techniques, commerciales et organisationnelles qui suivent doivent être traçables jusqu'à ce document. À relire au début de chaque session de développement, qu'elle soit menée par un humain ou par un agent autonome.
>
> **Statut** : v1 — à valider avec l'associé métier avant figement.
> **Dernière mise à jour** : avril 2026

---

## 1. Vision en une phrase

**TelecomERP est le cockpit de pilotage et de rentabilité des projets télécom au Maroc, conçu pour s'adapter à l'organisation réelle de chaque entreprise sans jamais quitter le mode standard.**

Le produit réconcilie deux mondes que personne ne réconcilie aujourd'hui sur le marché marocain : la richesse fonctionnelle d'un produit standard maintenable, et la précision d'un outil sur-mesure qui parle exactement le langage de l'entreprise qui l'utilise.

---

## 2. Le client idéal (ICP)

**Profil principal** : PME marocaine intervenant sur le déploiement et la maintenance d'infrastructures télécom, qui gagne régulièrement des appels d'offres (publics ou en sous-traitance d'opérateurs comme Inwi, Orange Maroc, IAM) et qui exécute des projets de tailles très variables — d'un chantier de 800k MAD sur 3 mois à un déploiement 5G à 30M MAD sur 18 mois — souvent en parallèle.

**Caractéristiques typiques** :
- Effectif : 10 à 200 personnes, dont une part significative en équipes terrain
- Activité : déploiement fibre, mise en place de réseaux 5G, maintenance de tours, ingénierie radio, sous-traitance d'opérateurs
- Multi-sites : équipes réparties sur plusieurs villes ou régions du Maroc
- Maturité numérique : utilise aujourd'hui un mélange d'Excel, Sage 100 ou équivalent, WhatsApp pour la coordination terrain, et beaucoup de papier
- Profil du décideur : dirigeant-fondateur, opérationnel, pragmatique, qui connaît son métier mais qui n'a pas le temps ni l'envie de mener un projet d'intégration ERP de 6 mois

**Insider de référence** : le co-fondateur métier du projet est lui-même dirigeant d'une société de ce profil, gagne des AO 5G régulièrement, et a vécu pendant des années la frustration de ne trouver aucun outil satisfaisant. C'est sa douleur opérationnelle qui guide la roadmap.

---

## 3. Le problème central

**Aujourd'hui, un dirigeant de PME télécom marocaine ne peut pas répondre à la question la plus importante de son métier : "Ce projet que je suis en train d'exécuter, est-ce que je vais réellement gagner de l'argent dessus, et si oui combien ?"**

Il le saura — peut-être — six mois après la livraison, quand son comptable aura fini de réconcilier les factures et que les écarts seront déjà figés. D'ici là, il navigue à l'aveugle. Les conséquences sont systémiques :

- Il ne peut pas arbitrer en cours de route entre deux projets concurrents
- Il ne peut pas détecter une dérive avant qu'elle devienne irrattrapable
- Il ne peut pas négocier en position de force avec ses fournisseurs ou ses sous-traitants
- Il ne peut pas valider scientifiquement le prix de ses prochaines offres
- Il ne peut pas savoir lesquels de ses chefs de chantier sont rentables et lesquels ne le sont pas

La cause racine est connue : aucun système ne **rattache automatiquement les coûts opérationnels (carburant, main-d'œuvre, matériel, sous-traitance, frais financiers) au bon projet, en temps réel, avec le bon degré de précision**. Tout repose sur des tableurs entretenus à la main, en retard, partiellement faux.

---

## 4. Les douleurs secondaires (les capteurs qui alimentent le cockpit)

Le cockpit de rentabilité n'existe que parce que des données opérationnelles propres l'alimentent. Chacune de ces douleurs justifie une capability du produit, et chacune peut être résolue indépendamment :

- **Consommation carburant non rattachée aux projets** : impossible de savoir si une équipe consomme anormalement, ou si un véhicule sert à un projet tout en étant facturé à un autre
- **Coût réel de financement ignoré** : taux d'intérêt et frais financiers selon le type de financement (crédit, leasing, avances client, cautions bancaires) ne sont jamais réintégrés dans la marge projet
- **Pointage et présence terrain non fiables** : impossible de prouver qu'une équipe était bien sur site à un moment donné, ce qui pose des problèmes de fraude interne et de litiges de facturation avec les opérateurs
- **Gestion des cautions bancaires manuelle** : risque permanent de péremption, de mainlevée oubliée, d'immobilisation de trésorerie
- **Conformité CNSS, AMO, IR, EPI, habilitations** : obligations légales mal suivies, exposition à des redressements et à des accidents
- **Suivi des situations de travaux et décomptes CCAG** : tâches répétitives, sources d'erreurs, qui retardent les paiements opérateurs

Le produit ne résout pas chacune de ces douleurs comme un outil isolé : il les résout **dans le contexte du cockpit de rentabilité**, ce qui fait que chaque donnée saisie sert deux fois — une fois pour l'opérationnel, une fois pour la marge.

---

## 5. La proposition de valeur

### Promesse principale

**Avoir, à tout moment, une vision en temps réel de la rentabilité réelle de chaque projet, sans avoir à attendre la clôture comptable.**

### Promesses secondaires

- **S'adapter à l'organisation existante** plutôt que d'imposer la sienne : que la société soit organisée en BU, en départements, en agences, qu'elle sépare ou fusionne ses fonctions, l'outil épouse cette structure
- **Conformité légale marocaine native** : TVA, CGNC, retenue à la source, CNSS, AMO, IR, mentions LCN, CCAG travaux — tout est intégré et maintenu, pas à reconstruire
- **Suivi terrain réel** : pointage géolocalisé, photos horodatées, signatures de bons d'intervention, traçabilité bout-en-bout
- **Démarrage rapide** : configuration assistée par un agent IA conversationnel, pas de mission d'intégration de plusieurs semaines

### Le positionnement en une formule

**Joindre le spécifique au général** — un produit standard qui, par sa configuration, ressemble à du sur-mesure pour chaque client, sans en avoir le coût ni la dette technique.

TelecomERP s'adapte à chaque entreprise à deux niveaux. Le profil d'installation définit la **structure** : quelles capabilities sont activées, quelle est l'organisation, quels sont les workflows. Les **feature flags** permettent ensuite à l'administrateur du tenant d'activer ou désactiver finement les comportements à tout moment, sans redéploiement ni intervention technique. Cette double adaptabilité est ce qui permet au produit de joindre le spécifique au général.

---

## 6. Les alternatives actuelles et le positionnement contre elles

> **Hypothèse à valider avec l'associé** : la cartographie ci-dessous est une hypothèse de travail. Elle doit être confirmée par une discussion explicite avec l'associé métier et 2-3 autres dirigeants du secteur avant d'être figée.

| Alternative actuelle | Ce qu'elle fait bien | Ce qu'elle ne fait pas | Pourquoi on gagne |
|---|---|---|---|
| **Excel + WhatsApp + papier** | Flexible, gratuit, tout le monde sait l'utiliser | Aucune consolidation, aucune rentabilité projet, aucune traçabilité, aucune conformité légale | Le client garde la souplesse perçue d'Excel mais gagne le pilotage |
| **Sage 100 ou équivalent généraliste** | Comptabilité solide, conformité fiscale | Aucune notion de projet télécom, pas d'opérationnel terrain, pas de rentabilité par chantier | On parle le langage du métier, pas celui du comptable |
| **Odoo standard intégré par un cabinet local** | Plateforme puissante, théoriquement adaptable | Mission d'intégration de 3-9 mois à 200-400 €/jour, configuration figée, dette technique, dépendance permanente à l'intégrateur | Démarrage en jours, pas en mois ; pas de dépendance ; produit qui évolue |
| **Solutions internes développées en interne** | Sur-mesure parfait au moment de la livraison | Devient obsolète rapidement, dépendance au développeur initial, aucune mutualisation des évolutions | Roadmap commune financée par tous les clients |

**Notre concurrent réel n'est pas un autre produit. C'est l'inertie : l'habitude d'un dirigeant à se débrouiller comme il peut parce qu'il n'a jamais vu d'alternative crédible.**

---

## 7. Le modèle économique

### Hypothèse de pricing

Modèle SaaS volume, ciblant **500 à 1500 MAD par mois et par tenant**, avec une cible de **50+ clients actifs à 18 mois**.

### Conséquences structurantes de ce choix

Ce niveau de prix interdit certains modes opératoires et en impose d'autres. Ces conséquences sont **non-négociables** parce qu'elles découlent directement de l'arithmétique économique :

- **Onboarding manuel impossible**. Un onboarding qui prendrait 5 jours-homme à un consultant coûterait à lui seul plus que la première année d'abonnement. → L'agent IA d'onboarding n'est pas une fonctionnalité confort, c'est une condition de viabilité.
- **Migration manuelle des données impossible à grande échelle**. Pour les premiers clients (1 à 5), une migration semi-manuelle assistée est acceptable comme apprentissage. Au-delà, il faut un outil de migration assisté par IA, ou refuser le client.
- **Support premium impossible**. Le support doit être asynchrone, documenté, communautaire pour la majorité des cas. Les escalades humaines doivent être l'exception.
- **Customisations client-spécifiques impossibles**. Tout ce qu'un client demande doit, soit déjà exister dans le catalogue de capabilities, soit y entrer comme évolution générale qui bénéficie à tous, soit être refusé.
- **Architecture multi-tenant obligatoire**. Pas une option, pas un objectif futur — la condition mathématique pour que la marge unitaire soit positive.

### Hypothèse de marché

Le marché cible (PME télécom MA correspondant à l'ICP) est estimé à plusieurs centaines d'entreprises. Atteindre 50 clients actifs représente une pénétration réaliste à 18 mois, à condition que l'effet de bouche-à-oreille s'enclenche via le réseau de l'associé métier. **Hypothèse à valider** : taille exacte du marché adressable, taux de conversion attendu d'une démo, cycle de vente moyen.

---

## 8. Qui on refuse de servir

Aussi important que de définir qui on vise : définir qui on refuse, même quand ils paient.

- **Les sociétés qui ne sont pas prêtes à "jouer le jeu" de l'outil**. Un client qui exige que l'outil épouse exactement ses processus historiques sans changer une virgule, qui refuse d'utiliser le pointage terrain "parce que les équipes n'aiment pas", ou qui veut des écrans entièrement personnalisés, n'est pas un client compatible. Le détecter tôt et le refuser est plus rentable que de signer et de regretter.
- **Les sociétés hors du périmètre télécom MA** au moins pendant les 18 premiers mois. Chaque dérive sectorielle ou géographique dilue la focalisation et fait reculer la roadmap. Cette frontière sera revue après les 50 premiers clients.
- **Les très grandes structures** dont les exigences en matière d'intégration SI, de SSO entreprise, d'audit, et de support contractuel dépassent ce qu'un produit volume peut offrir. Ces clients sont précieux mais incompatibles avec le modèle économique actuel.
- **Les sociétés en détresse opérationnelle** qui cherchent un outil pour résoudre un problème humain ou organisationnel. Un ERP n'a jamais sauvé une entreprise mal gérée ; il a souvent accéléré sa chute.

---

## 9. Principes non-négociables candidats

> Cette section sera figée à la fin de la rédaction des 6 documents fondateurs. Pour l'instant, elle liste les candidats issus des décisions prises ci-dessus. L'objectif est d'en retenir **3 à 5** maximum, ceux qui sont vraiment irrévocables.

1. **Aucun fork client-spécifique, jamais.** Toute demande client doit, soit être satisfaite par configuration, soit devenir une évolution générale du produit, soit être refusée.
2. **Configuration sans code, par l'agent IA.** L'onboarding d'un client ne nécessite jamais l'intervention d'un développeur ni d'un consultant intégrateur.
3. **Conformité légale marocaine native dès le jour 1.** Aucune exception, aucun "on verra plus tard", pour TVA, CNSS, retenue à la source, mentions légales, CCAG.
4. **Le même produit du chantier de 800k au déploiement 5G à 30M.** Pas deux produits, pas deux modes, pas d'édition entreprise distincte.
5. **Multi-tenant SaaS, jamais d'on-premise.** La complexité et le coût d'un on-premise détruisent la marge unitaire.
6. **Le terrain est mobile-first.** Toute fonctionnalité utilisée par un technicien sur le terrain doit être pensée pour un téléphone, dans des conditions difficiles, avant d'être pensée pour un bureau.
7. **Toute donnée opérationnelle doit être rattachable à un projet.** C'est ce qui alimente le cockpit de rentabilité ; sans ce principe, le produit perd sa promesse principale.

---

## 10. Hypothèses à valider sur le terrain

Le présent document repose sur plusieurs hypothèses qui ne sont pas encore validées par des données marché. Elles sont listées ici explicitement pour qu'elles soient testées en priorité plutôt que tenues pour acquises.

- **H1** — La cartographie des outils actuellement utilisés par le marché cible (Excel, Sage, autres) est conforme à la réalité.
- **H2** — Le marché adressable au Maroc compte effectivement plusieurs centaines d'entreprises répondant à l'ICP.
- **H3** — Un dirigeant de PME télécom est prêt à payer 500-1500 MAD/mois pour le cockpit de rentabilité, sans subvention par d'autres modules.
- **H4** — L'agent IA d'onboarding peut atteindre un taux de configuration réussie sans intervention humaine supérieur à 80% sur le profil cible.
- **H5** — La migration des données depuis l'existant (Excel et Sage) est faisable de façon semi-automatique pour 70% des cas.
- **H6** — Le bouche-à-oreille via le réseau de l'associé métier suffit à générer un flux de prospects stable, sans investissement marketing significatif.

Chacune de ces hypothèses doit faire l'objet d'un test explicite avant d'être considérée comme validée. Les premières conversations avec les prospects et le design partner sont le moyen privilégié de les tester.

---

## 11. Ce que ce document n'est pas

Pour éviter les confusions :

- Ce n'est pas un cahier des charges fonctionnel. Le catalogue précis des capabilities est dans `CAPABILITY_CATALOG.md`.
- Ce n'est pas un document d'architecture technique. Les principes techniques sont dans `ARCHITECTURE_PRINCIPLES.md`.
- Ce n'est pas un business plan financier. Les hypothèses économiques sont esquissées ici, pas modélisées.
- Ce n'est pas figé. Il évoluera, mais chaque évolution doit être consciente et tracée, pas accidentelle.

---

*Fin du document.*
