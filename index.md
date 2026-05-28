---
layout: home
title: Accueil
nav_order: 1
---

# OrientOps
{: .fs-9 }

Infrastructure GitOps complète sur AWS pour le déploiement et l'opération d'une API de recommandation de formations post-bac.
{: .fs-6 .fw-300 }

[![CI](https://github.com/guykopa/OrientAPI/actions/workflows/ci.yml/badge.svg)](https://github.com/guykopa/OrientAPI/actions/workflows/ci.yml)
&nbsp;
[Voir sur GitHub](https://github.com/guykopa/OrientAPI){: .btn .btn-outline }

---

## Vue d'ensemble

OrientAPI est une API REST qui retourne des recommandations de formations post-bac à partir d'un profil élève (filière, moyenne, niveau visé). Ce projet couvre l'ensemble de la chaîne DevOps : infrastructure cloud en Terraform, conteneurisation, orchestration Kubernetes, pipeline CI/CD, GitOps avec Argo CD, observabilité, tests de charge — et la documentation opérationnelle qui va avec.

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
                                                Prometheus ← /metrics + node-exporter
                                                Grafana    → dashboards
```

Deux nœuds EC2 en `eu-west-3` : le nœud **app** (t3.small) héberge k3s, Argo CD et PostgreSQL en Docker ; le nœud **monitoring** (t3.micro) héberge Prometheus et Grafana via Docker Compose. L'observabilité est isolée du cluster pour préserver la RAM du nœud app (2 Gio).

---

## Stack technique

| Couche | Technologie |
|---|---|
| Application | Python 3.12 · FastAPI · SQLAlchemy · Pydantic v2 · structlog |
| Authentification | JWT HS256 — tous les endpoints métier protégés |
| Infrastructure | Terraform ≥ 1.6 · AWS eu-west-3 · EC2 t3.small + t3.micro |
| Orchestration | k3s · Argo CD · Traefik · Network Policies |
| CI/CD | GitHub Actions · Trivy (scan image) · GHCR · bump tag automatique |
| Observabilité | Prometheus · Grafana · node-exporter · 2 dashboards versionnés |
| Tests | pytest (12 tests, SQLite in-memory) · k6 (spike 1 000 req/s) |
| Coût AWS | < 0,04 €/heure (t3.small + t3.micro + EBS gp3) |

---

## Démarrage rapide

```bash
# Dev local
cd app && docker compose up

# Obtenir un token
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d "username=demo&password=orientops2026" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Appeler l'API
curl -s -X POST http://localhost:8000/recommend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filiere_souhaitee": "informatique", "moyenne": 14.0, "niveau_vise": "BAC+3"}' \
  | python3 -m json.tool
```

---

## Documentation

| Document | Description |
|---|---|
| [Cahier des charges](docs/01-cahier-des-charges) | Spécification technique : 9 exigences (infra, sécurité, performance, RGPD), critères de recette |
| [Post-mortem](docs/02-post-mortem-incident) | Incident saturation PostgreSQL : chronologie, cause racine, 6 actions préventives |
| [Revue d'architecture](docs/03-revue-architecture-presta) | 6 écarts identifiés, tableau de risques, décision motivée |

---

## Limites assumées

| Limite | Risque | Plan v2 |
|---|---|---|
| Single-node, single-AZ | Pas de HA, RTO ~15 min | k3s multi-nœuds ou EKS |
| PostgreSQL hors k8s | Hors GitOps, pas d'auto-réparation | RDS Multi-AZ |
| Pas de logs centralisés | Observabilité métriques uniquement | Loki + Promtail |
| Network Policies sans Cilium | Politiques déclaratives sans effet | Déployer Cilium |
| Pas de backup automatique | RPO infini en cas de sinistre | CronJob pg_dump → S3 |
