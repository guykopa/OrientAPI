---
layout: default
title: Revue d'architecture
nav_order: 4
---

# Revue d'architecture — Livraison CloudOps Services SAS

**Référence :** OrientSup-REV-2026-001  
**Version :** 1.0  
**Date :** 2026-03-20  
**Réviseur :** Guy Florian KOPA, Ingénieur DevOps — OrientSup  
**Prestataire évalué :** CloudOps Services SAS  
**Périmètre :** Infrastructure OrientAPI — environnement de démonstration

---

## 1. Contexte et objectif de la revue

La présente revue fait suite à la livraison par CloudOps Services SAS de l'infrastructure OrientAPI, telle que spécifiée dans le cahier des charges OrientSup-CDC-2026-001. Elle vise à évaluer la conformité de la livraison aux exigences contractuelles, à identifier les écarts et risques résiduels, et à formuler les recommandations pour la mise en production.

La revue a été conduite à partir du dépôt Git livré, de la documentation d'architecture fournie, et des rapports de test de charge k6.

---

## 2. Architecture livrée — description synthétique

| Composant | Choix livré | Exigence CDC |
|---|---|---|
| Cloud / région | AWS eu-west-3 (Paris) | ✅ Conforme |
| Compute | EC2 t3.small (app) + EC2 t3.micro (monitoring) | ✅ Conforme |
| Orchestration | k3s single-node | ✅ Conforme (périmètre démo) |
| IaC | Terraform ≥ 1.6 | ✅ Conforme |
| GitOps | Argo CD, sync automatique | ✅ Conforme |
| CI/CD | GitHub Actions — test, scan, push, bump | ✅ Conforme |
| Registre d'images | GHCR (public) | ✅ Conforme |
| Base de données | PostgreSQL 16 en Docker sur nœud app | ✅ Conforme (périmètre démo) |
| Observabilité | Prometheus + Grafana sur nœud dédié — 2 dashboards | ✅ Conforme (Loki reporté en V2 — EXI-OBS-01) |
| Secrets | Injection cloud-init (hors Git) | ✅ Conforme (démo) — gestionnaire dédié requis en prod |
| TLS | cert-manager + Let's Encrypt (staging) | ⚠️ Partiel |
| Network Policies | Définies dans Git, Cilium non déployé | ⚠️ Partiel |
| Chiffrement EBS | Clé par défaut AWS | ⚠️ Non-conforme (CDC EXI-SEC-04) |
| DPIA | Non livrée | ❌ Manquant |

---

## 3. Points conformes — ce qui a été bien livré

### 3.1 Infrastructure as Code rigoureuse

Le code Terraform est structuré selon les bonnes pratiques : un fichier par concern (`network.tf`, `compute.tf`, `security.tf`), toutes les variables typées et documentées, tags standardisés sur toutes les ressources. Le `terraform plan` est reproductible et aucune ressource manuelle n'a été identifiée.

**Appréciation positive :** la modularité du code facilitera l'évolution vers une infrastructure multi-nœuds ou multi-environnements.

### 3.2 Pipeline CI/CD complet et sécurisé

Le pipeline GitHub Actions couvre l'ensemble du cycle : tests unitaires (pytest, SQLite in-memory), construction de l'image (multi-stage, non-root), analyse de vulnérabilités Trivy avant push, publication GHCR et mise à jour automatique du tag dans les manifests. La logique de bump de tag est correctement isolée dans un job dédié avec permissions minimales.

**Appréciation positive :** l'ordre build → scan → push garantit qu'aucune image vulnérable n'est publiée.

### 3.3 Observabilité opérationnelle

Les deux dashboards Grafana sont versionnés en JSON et provisionnés automatiquement au démarrage du nœud monitoring. Les requêtes Prometheus sont pertinentes (P95 latence, taux d'erreur 5xx, CPU/RAM de l'hôte). Le post-mortem a démontré l'efficacité de la stack : détection en moins de 2 minutes par alerte Grafana, diagnostic par les métriques Prometheus. L'absence de Loki (reporté en V2) est documentée comme limite connue et acceptée pour le périmètre démo.

### 3.4 Architecture applicative claire

Le découpage en couches (routes → services → modèles) est respecté. Les routes FastAPI sont effectivement minces. Les tests unitaires couvrent les cas limites du service de recommandation (filière inconnue, moyenne nulle, tri par sélectivité).

---

## 4. Écarts et risques identifiés

### 4.1 Absence de haute disponibilité — risque ÉLEVÉ

**Constat :** L'architecture livrée repose sur un cluster k3s **single-node** dans une **seule zone de disponibilité** (`eu-west-3a`). La défaillance de l'instance EC2 entraîne une indisponibilité totale du service.

**Risque :** RTO (Recovery Time Objective) réel estimé à 10-15 minutes (redémarrage EC2 + cloud-init k3s). Incompatible avec une disponibilité contractuelle de 99,5 % en production.

**Recommandation :** Pour la production, migrer vers un cluster k3s multi-nœuds (minimum 3 nœuds dans 2 AZ différentes) ou vers EKS si le budget le permet. Documenter explicitement le RTO/RPO dans le contrat de service.

### 4.2 Pas de sauvegarde managée de la base PostgreSQL — risque ÉLEVÉ

**Constat :** PostgreSQL est déployé en conteneur Docker sur le nœud app, avec un volume Docker sur le stockage local de l'instance. Il n'existe aucun mécanisme de sauvegarde automatique vers S3 ou tout autre stockage externe. La destruction de l'instance EC2 ou la corruption du volume EBS entraîne une perte totale des données.

**Risque :** RPO (Recovery Point Objective) infini en cas de sinistre majeur.

**Recommandation :** Mettre en place un job CronJob Kubernetes exécutant `pg_dump` vers S3 (chiffrement côté serveur, rétention 7 jours minimum), ou migrer vers Amazon RDS PostgreSQL 16 avec snapshots automatiques. Cette dernière option représente un surcoût d'environ 25 €/mois mais garantit un RPO < 5 minutes.

### 4.3 Chiffrement EBS avec clé par défaut — non-conforme EXI-SEC-04

**Constat :** Le volume EBS est chiffré, ce qui est positif. Cependant, la clé utilisée est la clé par défaut AWS du compte (`alias/aws/ebs`), partagée entre toutes les ressources du compte. Cette configuration ne permet pas d'audit fin des accès cryptographiques ni de rotation indépendante.

**Recommandation :** Créer une clé KMS dédiée au projet OrientOps (`alias/orientops`) avec une politique restrictive limitant son usage aux seuls rôles IAM autorisés. Référencer cette clé dans le Terraform (`kms_key_id`). Délai de mise en conformité : avant mise en production.

### 4.4 TLS Let's Encrypt en mode staging

**Constat :** cert-manager est configuré avec l'issuer `letsencrypt-staging`, qui génère des certificats non reconnus par les navigateurs et les clients HTTP standards.

**Recommandation :** Basculer vers `letsencrypt-production` dès que le nom de domaine est stabilisé. Cette modification d'une seule ligne dans le manifest de l'issuer Argo CD est sans risque.

### 4.5 Network Policies définies mais non appliquées

**Constat :** Les Network Policies sont correctement rédigées et versionnées dans Git. Cependant, k3s est installé avec le CNI Flannel par défaut, qui **n'applique pas** les Network Policies Kubernetes. Les politiques de sécurité réseau sont donc présentes en déclaratif mais sans effet à l'exécution.

**Recommandation :** Installer k3s avec `--flannel-backend=none` et déployer Cilium (~150 MiB RAM supplémentaires). La charge mémoire totale passerait à ~1 670 MiB, dans les limites du budget t3.small. Cette action est **prioritaire** avant toute mise en production.

### 4.6 DPIA non livrée

**Constat :** Le livrable L7 (DPIA simplifiée) est absent de la livraison.

**Recommandation :** Le prestataire doit livrer la DPIA sous 5 jours ouvrés. Sans ce document, la mise en production est bloquée au regard des obligations RGPD de l'OrientSup en tant que responsable de traitement.

---

## 5. Tableau de synthèse des risques

| Risque | Probabilité | Impact | Criticité | Traitement recommandé |
|--------|-------------|--------|-----------|----------------------|
| Panne nœud unique (no HA) | Moyenne | Très élevé | **CRITIQUE** | Multi-nœuds en prod (V2) |
| Perte base sans backup | Faible | Très élevé | **CRITIQUE** | CronJob pg_dump → S3 (J+7) |
| Network Policies sans effet | Certaine | Élevé | **ÉLEVÉ** | Déployer Cilium (J+3) |
| Chiffrement KMS non dédié | Faible | Moyen | **MOYEN** | Clé KMS dédiée avant prod |
| TLS staging | Certaine | Faible | **FAIBLE** | Issuer production (J+1) |
| DPIA manquante | Certaine | Élevé | **ÉLEVÉ** | Livraison sous 5 jours |

---

## 6. Conclusion et décision

**La livraison est acceptée pour l'environnement de démonstration**, avec les réserves suivantes :

- ✅ **Sans réserve** : IaC, pipeline CI/CD, observabilité (métriques), architecture applicative, gestion des secrets.
- ⚠️ **Avec réserves levables avant production** : DPIA (bloquant), Cilium pour Network Policies, clé KMS dédiée, issuer TLS production.
- 🚫 **Non-conforme pour mise en production** : absence de HA et absence de sauvegarde managée. Ces points doivent faire l'objet d'un avenant contractuel et d'un nouveau cahier des charges pour la phase de production.

OrientSup reconnaît que ces limites ont été **explicitement documentées par le prestataire** dans le document d'architecture, ce qui témoigne d'une posture de transparence appréciable. La mise en production nécessitera un dimensionnement et un cahier des charges distincts.

---

*Revue réalisée par OrientSup. Ce document est communicable à l'équipe projet et au DPO (pour la partie RGPD).*
