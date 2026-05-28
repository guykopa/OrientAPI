---
layout: default
title: Post-mortem
nav_order: 3
---

# Post-mortem — Saturation du pool de connexions PostgreSQL

**Référence :** OrientSup-INC-2024-001  
**Date de l'incident :** 2024-11-20  
**Rédigé par :** Guy Florian KOPA, Ingénieur DevOps — OrientSup  
**Statut :** Clôturé — actions préventives en cours  
**Sévérité :** P2 — Dégradation majeure de service (non-production)

---

## 1. Résumé exécutif

Le 20 novembre 2024, lors d'un test de charge simulant un pic de trafic Parcoursup sur l'environnement de démonstration OrientAPI, une saturation du pool de connexions PostgreSQL a provoqué une indisponibilité partielle de l'API pendant **8 minutes**. Le taux d'erreur 5xx a atteint **47 %** au pic. L'incident a été détecté par les alertes Grafana, diagnostiqué via les métriques Prometheus et les logs applicatifs OrientAPI, et résolu par un ajustement de la configuration PostgreSQL sans interruption complète du service.

Aucune donnée n'a été perdue. L'incident s'est produit en environnement de démonstration, hors production réelle.

---

## 2. Chronologie

| Heure (UTC) | Événement |
|-------------|-----------|
| 14:02       | Lancement du test k6 — montée progressive vers 200 req/s |
| 14:15       | Début de la phase de montée vers 1 000 req/s |
| 14:18       | Première alerte Grafana : taux d'erreur 5xx > 5 % |
| 14:19       | Taux d'erreur atteint 47 % — latence P95 dépasse 8 secondes |
| 14:20       | Diagnostic : métriques Prometheus (`pg_stat_activity_count`) confirment la saturation ; message `FATAL: remaining connection slots are reserved` visible dans les logs applicatifs OrientAPI |
| 14:21       | Identification de la cause racine : `max_connections = 10` dans la ConfigMap PostgreSQL |
| 14:23       | Application du correctif : `max_connections = 100`, redémarrage du pod postgres |
| 14:26       | Stabilisation du service — taux d'erreur redescend à 0 % |
| 14:30       | Fin du test k6 — rapport exporté |
| 15:00       | Ouverture du ticket post-mortem |

---

## 3. Cause racine

### 3.1 Cause immédiate

La ConfigMap PostgreSQL définissait `max_connections = 10`, une valeur de configuration adaptée à un environnement de développement local mais inadaptée à une charge de 1 000 req/s avec 2 pods OrientAPI.

Chaque pod OrientAPI maintient un pool de connexions SQLAlchemy (paramètre par défaut : `pool_size=5`, `max_overflow=10`). Avec 2 réplicas, le nombre maximum de connexions simultanées est donc **30** en situation normale, mais peut atteindre **40** en surcharge. La valeur `max_connections = 10` a été saturée dès la montée à 200 req/s.

### 3.2 Cause profonde

La valeur `max_connections` n'a pas été dimensionnée en fonction du nombre de réplicas applicatifs ni testée lors du déploiement initial. Aucune alerte préventive n'avait été configurée sur le taux de connexions actives par rapport à `max_connections`.

La formule de dimensionnement correcte est :

```
max_connections ≥ (nb_replicas × pool_size) + (nb_replicas × max_overflow) + 5 (connexions admin)
               ≥ (2 × 5) + (2 × 10) + 5 = 35
```

La valeur retenue après correctif est **100** pour disposer d'une marge confortable face aux variations du nombre de réplicas.

### 3.3 Facteur aggravant

L'absence de `PgBouncer` (connection pooler externe) en frontal de PostgreSQL amplifie la sensibilité au nombre de connexions. Chaque connexion SQL consomme ~5 MiB de mémoire sur le pod postgres, ce qui représente un facteur limitant supplémentaire sur un nœud à 2 Gio.

---

## 4. Impact

| Dimension         | Mesure                                               |
|-------------------|------------------------------------------------------|
| Durée             | 8 minutes (14:18 → 14:26)                           |
| Environnement     | Démonstration (non-production)                       |
| Utilisateurs      | 0 utilisateur réel impacté                           |
| Erreurs HTTP 5xx  | ~3 200 requêtes sur les 8 minutes d'incident         |
| Taux d'erreur pic | 47 %                                                 |
| Latence P95 pic   | 8,4 secondes                                         |
| Perte de données  | Aucune                                               |

---

## 5. Remédiation appliquée

### 5.1 Correctif immédiat (J0)

Mise à jour de la ConfigMap PostgreSQL :

```yaml
# Avant
POSTGRES_MAX_CONNECTIONS: "10"

# Après
POSTGRES_MAX_CONNECTIONS: "100"
```

Redémarrage contrôlé du conteneur Docker PostgreSQL via `docker restart postgres` sur le nœud app. Retour à la normale en 3 minutes.

### 5.2 Correctif de fond (J+1)

- Configuration du pool SQLAlchemy dans OrientAPI rendue explicite via variable d'environnement :
  ```
  SQLALCHEMY_POOL_SIZE=5
  SQLALCHEMY_MAX_OVERFLOW=5
  ```
- Ajout d'une alerte Prometheus sur le ratio connexions actives / max_connections :
  ```promql
  pg_stat_activity_count / pg_settings_max_connections > 0.8
  ```

---

## 6. Actions préventives

| # | Action | Responsable | Délai | Statut |
|---|--------|-------------|-------|--------|
| A1 | Définir `max_connections` selon la formule documentée ci-dessus | G. KOPA | J+1 | ✅ Fait |
| A2 | Ajouter alerte Prometheus sur saturation connexions DB | G. KOPA | J+2 | ✅ Fait |
| A3 | Documenter la formule de dimensionnement dans le runbook d'exploitation | G. KOPA | J+2 | ✅ Fait |
| A4 | Évaluer PgBouncer pour v2 du projet | G. KOPA | V2 | 📋 Backlog |
| A5 | Ajouter un test de charge systématique dans la pipeline CI (seuil d'erreur < 1 %) | G. KOPA | J+5 | 📋 Backlog |
| A6 | Configurer `HorizontalPodAutoscaler` sur OrientAPI pour absorber les pics | G. KOPA | V2 | 📋 Backlog |

---

## 7. Leçons apprises

**Ce qui a bien fonctionné :**
- La stack d'observabilité (Grafana + Prometheus) a permis de détecter et diagnostiquer l'incident en **moins de 2 minutes** après le premier signal.
- La structure en couches de l'application (services → modèles) a facilité l'identification rapide du composant défaillant sans avoir à parcourir tout le code.
- Le redémarrage contrôlé du conteneur Docker PostgreSQL a évité une interruption totale grâce aux 2 réplicas OrientAPI restants.

**Ce qui doit être amélioré :**
- Le dimensionnement des paramètres PostgreSQL doit être systématiquement vérifié en fonction du nombre de réplicas lors de tout changement de topologie.
- Un runbook d'incident doit être rédigé avant la mise en production pour chaque composant critique (PostgreSQL, OrientAPI).
- L'absence de PgBouncer est une limitation architecturale identifiée — à traiter en priorité avant tout passage en production réelle.

---

*Ce post-mortem est rédigé dans un esprit blameless. L'objectif est d'améliorer les systèmes, pas d'identifier des responsabilités individuelles.*
