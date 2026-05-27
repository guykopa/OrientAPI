# Cahier des charges technique — Infrastructure OrientAPI

**Référence :** OrientSup-DSI-CDC-2024-001  
**Version :** 1.0  
**Date :** 2024-11-15  
**Émetteur :** Direction des Systèmes d'Information — OrientSup  
**Destinataire :** Prestataire d'infogérance retenu  
**Statut :** Applicable

---

## 1. Contexte et objet du document

### 1.1 Contexte organisationnel

OrientSup est un groupement d'intérêt public (GIP) sous tutelle du ministère de l'Éducation nationale, chargé de l'orientation scolaire et professionnelle. La DSI d'OrientSup pilote l'ensemble des systèmes d'information de l'établissement, dont certains font l'objet de délégations à des prestataires d'infogérance.

Dans le cadre de sa stratégie de modernisation 2024-2026, la DSI souhaite déployer **OrientAPI**, une API REST de recommandation de formations post-bac à destination des équipes internes et des intégrateurs partenaires. Ce service traite des données personnelles de profils élèves et est classifié **sensible** au sens de la politique de sécurité des systèmes d'information (PSSI) de l'établissement.

### 1.2 Objet du présent document

Le présent cahier des charges définit les **exigences techniques, de sécurité, de performance et de conformité** que le prestataire retenu devra respecter pour la conception, le déploiement et l'exploitation de l'infrastructure hébergeant OrientAPI.

Il constitue la référence contractuelle pour la phase de recette et servira de base à la revue d'architecture avant mise en production.

---

## 2. Périmètre fonctionnel

### 2.1 Description du service

OrientAPI expose trois endpoints REST :

| Méthode | Chemin       | Description                                                    |
|---------|--------------|----------------------------------------------------------------|
| GET     | `/health`    | Sonde de disponibilité pour les outils d'orchestration        |
| GET     | `/metrics`   | Métriques Prometheus pour la supervision                       |
| POST    | `/recommend` | Retourne une liste de formations adaptée à un profil élève    |

L'API est sans état applicatif (*stateless*) ; la persistance est assurée par une base PostgreSQL hébergeant le référentiel des formations OrientSup (~10 000 entrées).

### 2.2 Volumétrie de référence

| Indicateur                         | Valeur cible              |
|------------------------------------|---------------------------|
| Charge nominale                    | 50 à 200 requêtes/seconde |
| Pic Parcoursup (mi-juin)           | 1 000 requêtes/seconde    |
| Temps de réponse nominal (P95)     | < 300 ms                  |
| Temps de réponse pic (P95)         | < 500 ms                  |
| Disponibilité contractuelle        | 99,5 % (hors maintenance) |

---

## 3. Exigences d'infrastructure

### 3.1 Cloud et localisation

**EXI-INFRA-01** — L'ensemble des ressources doit être hébergé sur AWS, région **`eu-west-3` (Paris)**, afin de garantir la résidence des données sur le territoire français conformément à la réglementation RGPD applicable aux établissements publics.

**EXI-INFRA-02** — Aucune ressource traitant des données OrientAPI ne peut être localisée hors de l'Union européenne, y compris pour des services managés (sauvegardes, logs, monitoring).

### 3.2 Compute et orchestration

**EXI-INFRA-03** — Le service doit être déployé sur un cluster Kubernetes. Pour le périmètre de la présente commande (environnement de démonstration et pré-production), un cluster k3s single-node sur EC2 est accepté. La montée en charge vers un cluster multi-nœuds en production est explicitement documentée dans les limites de l'architecture livrée.

**EXI-INFRA-04** — Le dimensionnement minimal accepté est **2 vCPU / 2 Gio RAM** (EC2 t3.small). Tout changement de dimensionnement doit faire l'objet d'une justification chiffrée en section « compromis d'architecture ».

**EXI-INFRA-05** — L'infrastructure doit être intégralement décrite en **Infrastructure as Code (Terraform ≥ 1.6)**. Aucune ressource créée manuellement dans la console AWS ne sera acceptée en recette.

### 3.3 GitOps et CI/CD

**EXI-INFRA-06** — Le déploiement des applications sur le cluster doit être piloté par **Argo CD** en mode synchronisation automatique. L'état désiré est versionné dans le dépôt Git fourni par la DSI.

**EXI-INFRA-07** — Un pipeline de CI/CD (GitHub Actions) doit être livré, couvrant : exécution des tests unitaires, construction de l'image Docker, analyse de vulnérabilités (Trivy), publication sur le registre d'images (GHCR) et mise à jour automatique du tag d'image dans les manifests Kubernetes.

**EXI-INFRA-08** — Toute image déployée en production doit avoir passé une analyse Trivy sans vulnérabilité de sévérité CRITICAL.

---

## 4. Exigences de sécurité

**EXI-SEC-01** — Les secrets applicatifs (identifiants PostgreSQL, clés API) ne doivent jamais être stockés en clair dans le dépôt Git ni dans les images Docker. Pour l'environnement de démonstration, l'injection par le mécanisme de provisionnement d'infrastructure (cloud-init, variables sensibles hors Git) est acceptée. En production, l'usage d'un gestionnaire de secrets dédié (Bitnami Sealed Secrets, HashiCorp Vault ou AWS Secrets Manager) est exigé.

**EXI-SEC-02** — Des **Network Policies Kubernetes** doivent être définies selon le principe du moindre privilège : refus de tout trafic par défaut, autorisation explicite et documentée des flux nécessaires. Le CNI déployé doit appliquer ces politiques (Cilium recommandé).

**EXI-SEC-03** — L'accès SSH à l'instance EC2 doit être restreint à la plage IP de l'opérateur désigné. Aucune règle de sécurité `0.0.0.0/0` ne sera acceptée sur le port 22.

**EXI-SEC-04** — Le volume EBS doit être chiffré. Pour la version initiale, le chiffrement avec la clé par défaut AWS est toléré ; le passage à une clé KMS dédiée est requis pour la mise en production réelle.

**EXI-SEC-05** — Le trafic HTTP entrant doit être redirigé vers HTTPS. Un certificat TLS valide doit être provisionné via cert-manager et Let's Encrypt.

**EXI-SEC-06** — Les pods applicatifs doivent s'exécuter avec un utilisateur non-root (UID ≥ 1000) et sans capacités Linux supplémentaires.

---

## 5. Exigences d'observabilité

**EXI-OBS-01** — La stack de supervision doit comprendre au minimum : **Prometheus** (collecte des métriques) et **Grafana** (visualisation, dashboards versionnés). Pour l'environnement de démonstration, l'observabilité est limitée aux métriques. L'agrégation des logs (**Loki + Promtail**) est exigée pour la mise en production et constitue un livrable de la phase V2.

**EXI-OBS-02** — Au minimum deux dashboards Grafana doivent être livrés et versionnés dans le dépôt Git (format JSON Grafana) :
- **Tableau de bord API** : taux de requêtes, latence P50/P95, taux d'erreurs 5xx, nombre de pods actifs.
- **Tableau de bord cluster** : consommation CPU et mémoire par pod, redémarrages, pression mémoire du nœud.

**EXI-OBS-03** — Les métriques Prometheus doivent être exposées par l'application via l'endpoint `/metrics`. L'instrumentation automatique FastAPI (`prometheus-fastapi-instrumentator`) est la référence.

**EXI-OBS-04** — La rétention des métriques est fixée à **7 jours** minimum. La rétention des logs est fixée à **7 jours** minimum.

---

## 6. Exigences de performance et de résilience

**EXI-PERF-01** — Un test de charge simulant un pic Parcoursup (montée progressive jusqu'à 1 000 req/s, maintien 5 minutes) doit être exécuté et le rapport livré avec la recette. L'outil retenu est **k6**.

**EXI-PERF-02** — Le déploiement de l'API doit utiliser au minimum **2 réplicas** pour permettre les mises à jour sans interruption de service (*rolling update*).

**EXI-PERF-03** — Des sondes de disponibilité (`livenessProbe`) et de disponibilité applicative (`readinessProbe`) doivent être configurées sur tous les déploiements.

**EXI-PERF-04** — Des limites et demandes de ressources (`resources.requests` et `resources.limits`) doivent être définies sur tous les conteneurs.

---

## 7. Conformité RGPD

**EXI-RGPD-01** — Les données de profil élève transitant par `/recommend` sont des données à caractère personnel au sens du RGPD. Elles ne doivent pas être persistées par l'API au-delà de la durée de la requête.

**EXI-RGPD-02** — Les logs applicatifs ne doivent pas contenir de données personnelles identifiantes (nom, prénom, adresse IP utilisateur). Les champs logués sont limités aux métriques techniques (handler, durée, code HTTP).

**EXI-RGPD-03** — Le prestataire doit fournir une analyse d'impact relative à la protection des données (AIPD/DPIA) simplifiée pour cet hébergement.

---

## 8. Livrables attendus

| # | Livrable                                              | Format          | Délai |
|---|-------------------------------------------------------|-----------------|-------|
| L1 | Code Terraform (VPC, EC2, sécurité)                  | `.tf` dans Git  | J+2   |
| L2 | Manifests Kubernetes (API, Network Policies) + Docker Compose (Postgres sur nœud app, Prometheus + Grafana sur nœud monitoring) | YAML/Compose dans Git | J+3 |
| L3 | Pipeline CI/CD GitHub Actions                        | `.yml` dans Git | J+3   |
| L4 | Dashboards Grafana                                   | JSON dans Git   | J+4   |
| L5 | Rapport de test de charge k6                         | JSON + texte    | J+4   |
| L6 | Document d'architecture                              | Markdown + PNG  | J+4   |
| L7 | DPIA simplifiée                                      | Markdown        | J+5   |

---

## 9. Critères de recette

La recette sera prononcée favorable si l'ensemble des conditions suivantes sont remplies :

1. **`terraform apply`** s'exécute sans erreur depuis un environnement vierge et produit une instance EC2 accessible en SSH.
2. **Un commit sur la branche `main`** déclenche le pipeline CI, qui se termine avec succès (tests verts, scan Trivy sans CRITICAL, image publiée sur GHCR).
3. **Argo CD synchronise** automatiquement le cluster après la mise à jour du tag d'image.
4. **Les endpoints** `/health`, `/metrics` et `/recommend` répondent correctement sur l'IP publique de l'instance.
5. **Les dashboards Grafana** affichent des données en temps réel lors du test de charge.
6. **Le test de charge k6** s'exécute sans dépasser le seuil d'erreur de 1 % et avec un P95 < 500 ms en charge nominale.
7. **Aucun secret en clair** n'est présent dans le dépôt Git (vérification `git log --all -p | grep -i password`).
8. **Les Network Policies** sont présentes dans le dépôt et documentées.

---

*Document rédigé par la DSI OrientSup — toute modification doit faire l'objet d'un avenant signé par les deux parties.*
