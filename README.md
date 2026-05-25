# OrientOps

[![CI](https://github.com/guykopa/orientops/actions/workflows/ci.yml/badge.svg)](https://github.com/guykopa/orientops/actions/workflows/ci.yml)

Projet de portfolio DevOps démontrant la construction et l'opération d'une infrastructure GitOps complète sur AWS, ainsi que les livrables de gouvernance attendus d'un ingénieur DevOps junior en contexte public (référence : ONISEP).

> **Pitch :** *« J'ai construit OrientOps pour prouver que je sais à la fois opérer techniquement une infrastructure GitOps sur AWS et produire les livrables de pilotage qu'un DevOps DSI produit au quotidien — cahier des charges, post-mortem, revue d'architecture prestataire. »*

---

## Ce que ce projet démontre

| # | Compétence | Preuve concrète |
|---|---|---|
| 1 | Infrastructure as Code | Terraform appliqué — VPC, EC2, k3s, eu-west-3 |
| 2 | Orchestration Kubernetes | k3s + manifests (Deployment, StatefulSet, Ingress, Network Policies) |
| 3 | CI/CD automatisée | GitHub Actions : test → build → scan Trivy → push GHCR → bump tag |
| 4 | GitOps | Argo CD synchronise le cluster depuis `main` à chaque commit |
| 5 | Observabilité | Prometheus + Grafana + Loki — 2 dashboards versionnés |
| 6 | Sécurité | Sealed Secrets, Network Policies, scan image, non-root pods |
| 7 | Tests de charge | k6 — simulation pic Parcoursup 1 000 req/s |
| 8 | **Cahier des charges** | Spec formelle ONISEP → prestataire, 9 exigences, critères de recette |
| 9 | **Post-mortem** | Incident DB provoqué, diagnostiqué en < 2 min, causes documentées |
| 10 | **Revue prestataire** | 6 écarts identifiés, tableau de risques, décision motivée |

---

## Architecture

```
  git push
     │
     ▼
GitHub Actions ──► Trivy scan ──► GHCR (image)
     │                                │
     │ bump tag                        │ pull
     ▼                                ▼
 Git repo ◄──── Argo CD ────► k3s (EC2 t3.small, eu-west-3)
                                  ├─ orientapi (2 pods × 60 MiB)
                                  ├─ postgres:16 (StatefulSet, PVC 5 Gi)
                                  ├─ Prometheus + Grafana + Loki
                                  └─ Argo CD + Traefik (inclus k3s)
```

**Choix structurants documentés :** k3s plutôt qu'EKS (−70 €/mois), PostgreSQL en pod plutôt que RDS (free tier insuffisant), single-node documenté comme limite connue.

---

## Démarrage rapide — dev local

```bash
cd app
docker compose up
```

Appeler l'API :

```bash
# Recommandations pour un élève en informatique, 14/20, vise un BAC+3
curl -s -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"filiere_souhaitee": "informatique", "moyenne": 14.0, "niveau_vise": "BAC+3"}' \
  | python3 -m json.tool
```

Santé et métriques :

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

---

## Tests

```bash
cd app
source ../.venv/bin/activate
pytest -v
# → 6/6 passed
```

---

## Déployer l'infrastructure

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Renseigner operator_ip (votre IP publique) et public_key_path
terraform init
terraform plan   # vérifier le coût avant d'appliquer
terraform apply
```

**Coût estimé :** < 0,05 €/heure (EC2 t3.small + EBS gp3 20 Gi). Détruire après usage : `terraform destroy`.

### Récupérer le kubeconfig

```bash
# Disponible ~5 min après le démarrage (cloud-init installe k3s + Argo CD)
$(terraform output -raw kubeconfig_command)
export KUBECONFIG=~/.kube/orientops.yaml
kubectl get nodes
```

### Appliquer les applications Argo CD

```bash
kubectl apply -f infra/kubernetes/argo-apps/
# Argo CD synchronise automatiquement toute la stack
```

---

## Test de charge

```bash
# Prérequis : k6 installé (https://k6.io/docs/getting-started/installation/)
BASE_URL=https://api.orientops.demo k6 run tests/k6/parcoursup-spike.js
```

Le script simule 5 phases : montée progressive → 200 req/s nominal → spike 1 000 req/s → retour à zéro.

---

## Incident provoqué (Jour 3)

Lors du test de charge, un `max_connections = 10` volontairement trop bas a saturé le pool PostgreSQL, provoquant 47 % d'erreurs 5xx pendant 8 minutes. Détection par Grafana en < 2 min, diagnostic par Loki, résolution par mise à jour de la ConfigMap et redémarrage contrôlé du pod.

→ Voir [`docs/02-post-mortem-incident.md`](docs/02-post-mortem-incident.md)

---

## Livrables de gouvernance

Ces trois documents constituent le **différenciateur principal** du projet par rapport à un portfolio purement technique.

| Document | Description |
|---|---|
| [`docs/01-cahier-des-charges.md`](docs/01-cahier-des-charges.md) | Spécification formelle ONISEP → prestataire : 9 exigences (infra, sécurité, performance, RGPD), critères de recette |
| [`docs/02-post-mortem-incident.md`](docs/02-post-mortem-incident.md) | Analyse de l'incident de saturation PostgreSQL : chronologie, cause racine, impact, 6 actions préventives |
| [`docs/03-revue-architecture-presta.md`](docs/03-revue-architecture-presta.md) | Revue critique de la livraison : 4 points conformes, 6 écarts identifiés, tableau de risques, décision motivée |

---

## Limites assumées de la v1

Ces limites sont **volontairement documentées** — elles font partie de la valeur du projet.

| Limite | Risque | Plan v2 |
|---|---|---|
| Single-node, single-AZ | Pas de HA, RTO ~15 min | k3s multi-nœuds ou EKS |
| Pas de backup PostgreSQL | RPO infini | CronJob pg_dump → S3 |
| Flannel sans Network Policies actives | Isolation réseau déclarative seulement | Migrer vers Cilium |
| Chiffrement EBS clé par défaut | Audit cryptographique limité | Clé KMS dédiée |
| PostgreSQL en pod (pas RDS) | Pas de snapshots managés | RDS en production |

---

## Structure du dépôt

```
app/                         Application OrientAPI (FastAPI + PostgreSQL)
├── src/                     Code source (routes → services → modèles)
├── tests/                   Tests unitaires SQLite in-memory
├── Dockerfile               Multi-stage, non-root uid 1001
└── docker-compose.yml       Dev local

infra/terraform/             Infrastructure AWS (VPC, EC2, k3s, cloud-init)
infra/kubernetes/
├── base/orientapi/          Deployment, Service, Ingress, ConfigMap
├── base/postgres/           StatefulSet, Service, Sealed Secret
├── base/observability/      Helm values + dashboards Grafana JSON
├── base/network-policies/   Deny-all + allow-list
└── argo-apps/               Définitions Application Argo CD

.github/workflows/ci.yml     Pipeline CI/CD
tests/k6/                    Script de charge Parcoursup
docs/                        Livrables de gouvernance + screenshots
```

---

Auteur : **Guy Florian KOPA** · [GitHub @guykopa](https://github.com/guykopa) · [LinkedIn](https://linkedin.com/in/kopaguy) · kopaguy@yahoo.com
