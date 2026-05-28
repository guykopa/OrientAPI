# OrientOps

[![CI](https://github.com/guykopa/OrientAPI/actions/workflows/ci.yml/badge.svg)](https://github.com/guykopa/OrientAPI/actions/workflows/ci.yml)
[![Pages](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://guykopa.github.io/OrientAPI/)

**Documentation et présentation du projet : [guykopa.github.io/OrientAPI](https://guykopa.github.io/OrientAPI/)**

Infrastructure GitOps complète sur AWS pour le déploiement et l'opération d'une API de recommandation. Inclut la documentation opérationnelle complète : spécification technique, post-mortem d'incident et revue d'architecture.

---

## Périmètre technique

| # | Composant | Détail |
|---|---|---|
| 1 | Infrastructure as Code | Terraform — VPC, 2 EC2, security groups, cloud-init, eu-west-3 |
| 2 | Orchestration Kubernetes | k3s single-node + manifests (Deployment, Ingress, Network Policies) |
| 3 | CI/CD | GitHub Actions : test → build → scan Trivy → push GHCR → bump tag |
| 4 | GitOps | Argo CD synchronise le cluster depuis `main` à chaque commit |
| 5 | Observabilité | Prometheus + Grafana sur nœud dédié — 2 dashboards provisionnés |
| 6 | Sécurité | Network Policies, JWT auth (HS256), secrets injectés par cloud-init, scan image Trivy, non-root pods |
| 7 | Tests de charge | k6 — simulation pic Parcoursup 1 000 req/s |
| 8 | Cahier des charges | Spécification technique d'infrastructure : 9 exigences, critères de recette |
| 9 | Post-mortem | Incident saturation DB, diagnostiqué en < 2 min, causes documentées |
| 10 | Revue d'architecture | 6 écarts identifiés, tableau de risques, décision motivée |

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
 Git repo ◄──── Argo CD ────► k3s  ┐
                               │   │  EC2 app — t3.small
                               ▼   │  ├─ k3s : Argo CD + OrientAPI (2 pods)
                         Traefik   │  └─ Docker : PostgreSQL + node-exporter
                               │   └──────────────────────────────────────
                               ▼
                          utilisateur        EC2 monitoring — t3.micro
                                             └─ Docker Compose :
                                                Prometheus ← scrape /metrics + node-exporter
                                                Grafana    → dashboards
```

**Choix structurants documentés :** k3s plutôt qu'EKS (−70 €/mois), observabilité sur nœud dédié plutôt qu'in-cluster (RAM limitée à 2 GiB), PostgreSQL en Docker sur l'hôte plutôt que RDS (hors budget). Limites assumées explicitement documentées.

---

## Démarrage rapide — dev local

```bash
cd app
docker compose up
```

Appeler l'API :

```bash
# 1. Obtenir un token
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d "username=demo&password=orientops2026" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Appeler l'API
curl -s -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"filiere_souhaitee": "informatique", "moyenne": 14.0, "niveau_vise": "BAC+3"}' \
  | python3 -m json.tool
```

Santé et métriques :

```bash
curl http://localhost:8000/health        # public
curl http://localhost:8000/metrics       # public (Prometheus)
# Endpoints protégés : /recommend, /formations, /filieres → Bearer token requis
```

---

## Tests

```bash
cd app
source ../.venv/bin/activate
pytest -v
# → 12/12 passed
```

---

## Déployer l'infrastructure

```bash
cp app/.env.example app/.env
# Renseigner les mots de passe dans app/.env

cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Renseigner : operator_ip, public_key_path, postgres_password
terraform init
terraform plan   # vérifier avant d'appliquer
terraform apply
```

**Coût estimé :** < 0,04 €/heure (t3.small + t3.micro + 2 volumes EBS gp3). Détruire après usage : `terraform destroy`.

### Récupérer le kubeconfig (nœud app)

```bash
# Disponible ~10 min après le démarrage (cloud-init installe k3s + Argo CD + PostgreSQL)
$(terraform output -raw app_kubeconfig_command)
export KUBECONFIG=~/.kube/orientops.yaml
kubectl get nodes
```

### Accéder à Argo CD

```bash
# UI : https://<app_public_ip>:30443  (accepter le certificat auto-signé)
terraform output app_public_ip

# Mot de passe admin initial
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

### Déployer les applications Argo CD

```bash
kubectl apply -f infra/kubernetes/argo-apps/
# Argo CD synchronise automatiquement OrientAPI

# Appliquer le Secret JWT (credentials API)
kubectl apply -f infra/kubernetes/base/orientapi/secret-jwt.yaml
```

### Accéder à Grafana

```bash
# UI : http://<monitoring_public_ip>:3000  (admin / orientops)
terraform output grafana_url
```

---

## Test de charge

```bash
# Prérequis : k6 installé (https://k6.io/docs/getting-started/installation/)
BASE_URL=https://api.orientops.demo k6 run tests/k6/parcoursup-spike.js
```

Le script simule 5 phases : montée progressive → 200 req/s nominal → spike 1 000 req/s → retour à zéro.

---

## Incident — Saturation du pool PostgreSQL

Lors du test de charge, un `max_connections` sous-dimensionné a saturé PostgreSQL, provoquant 47 % d'erreurs 5xx pendant 8 minutes. Détection par alerte Grafana en < 2 min, résolution par reconfiguration et redémarrage du conteneur Docker.

→ Voir [`docs/02-post-mortem-incident.md`](docs/02-post-mortem-incident.md)

---

## Documentation

| Document | Description |
|---|---|
| [`docs/01-cahier-des-charges.md`](docs/01-cahier-des-charges.md) | Spécification technique d'infrastructure : 9 exigences (infra, sécurité, performance, RGPD), critères de recette |
| [`docs/02-post-mortem-incident.md`](docs/02-post-mortem-incident.md) | Analyse de l'incident de saturation PostgreSQL : chronologie, cause racine, impact, 6 actions préventives |
| [`docs/03-revue-architecture-presta.md`](docs/03-revue-architecture-presta.md) | Revue critique de l'architecture livrée : 4 points conformes, 6 écarts identifiés, tableau de risques, décision motivée |

---

## Limites assumées de la v1

Ces limites sont documentées et font l'objet d'un plan d'évolution.

| Limite | Risque | Plan v2 |
|---|---|---|
| Single-node, single-AZ | Pas de HA, RTO ~15 min | k3s multi-nœuds ou EKS |
| PostgreSQL et observabilité hors k8s | Hors GitOps, pas d'auto-réparation Kubernetes | PostgreSQL → RDS, observabilité → opérateur in-cluster |
| Pas de backup PostgreSQL | RPO infini | CronJob pg_dump → S3 |
| Flannel sans Network Policies actives | Isolation réseau déclarative seulement | Migrer vers Cilium |
| Chiffrement EBS clé par défaut | Audit cryptographique limité | Clé KMS dédiée |

---

## Structure du dépôt

```
app/
├── src/
│   ├── auth.py              Authentification JWT (HS256)
│   ├── config.py            Settings Pydantic (lecture .env)
│   ├── main.py              Routes FastAPI
│   ├── services.py          Logique métier
│   └── models.py            Modèles SQLAlchemy
├── tests/                   12 tests unitaires (services + auth)
├── .env.example             Template de credentials (commité)
├── Dockerfile               Multi-stage, non-root uid 1001
└── docker-compose.yml       Dev local (env_file: .env)

scripts/                     Scripts d'exploitation locaux (gitignorés)
└── orientops.sh             Start/stop instances + affiche URLs et commandes

infra/terraform/             Infrastructure AWS (VPC, 2 EC2, security groups, cloud-init)
infra/postgres/              Docker Compose de référence — PostgreSQL sur nœud app
infra/monitoring/            Stack observabilité — nœud monitoring
├── docker-compose.yml       Prometheus + Grafana
├── prometheus.yml           Scrape config (APP_PRIVATE_IP remplacé par Terraform)
├── provisioning/            Auto-provisioning Grafana (datasource + dashboards)
└── dashboards/              JSON des 2 dashboards versionnés

infra/kubernetes/
├── base/orientapi/          Deployment, Service, Ingress, ConfigMap, NodePort metrics
├── base/network-policies/   Deny-all + allow-list
└── argo-apps/               Définitions Application Argo CD

.github/workflows/ci.yml     Pipeline CI/CD
tests/k6/                    Script de charge Parcoursup
docs/                        Documentation opérationnelle + screenshots
```

---

Auteur : **Guy Florian KOPA** · [GitHub @guykopa](https://github.com/guykopa) · [LinkedIn](https://linkedin.com/in/kopaguy) · kopaguy@yahoo.com
