# France Market Scanner

Système de collecte et d'analyse de données d'entreprises françaises via les APIs publiques gratuites.

## Objectif

**Identifier des "pépites" d'entreprises** : sociétés avec peu d'employés mais fort CA/bénéfices — cibles idéales pour l'automatisation IA ou l'acquisition.

### Données nécessaires

| Donnée | Source | Status | Couverture |
|--------|--------|--------|------------|
| **Effectifs** (tranche) | SIRENE | ✅ Chargé | ~1.7M entreprises ont l'info (10%) |
| **CA** (chiffre d'affaires) | INPI | ✅ Chargé | Comptes non-confidentiels 2017-2023 |
| **Résultat net** | INPI | ✅ Chargé | Idem |
| **Bilan** (actif/passif) | INPI | ✅ Chargé | Idem |

> **Note** : 90% des entreprises ont "NN" (non renseigné) pour l'effectif dans SIRENE.
> On filtrera sur les ~1.7M qui ont des données complètes.

### Critères de scoring (à implémenter)

| Critère | Description | Poids |
|---------|-------------|-------|
| CA/Employé | Productivité par tête | 40% |
| Secteur | Activités automatisables (conseil, SaaS, formation...) | 30% |
| Marge nette | Résultat / CA | 15% |
| Actifs légers | Peu d'immobilisations | 15% |

---

## Architecture

```
france-market-scanner/
├── cli.py                 # Interface ligne de commande (Click)
├── config/config.yaml     # Configuration
├── .env                   # Credentials (INPI)
├── src/
│   ├── core/
│   │   ├── database.py    # DuckDB manager + schéma
│   │   ├── config.py      # Chargement configuration
│   │   └── downloader.py  # Téléchargements HTTP async
│   └── extractors/
│       ├── sirene.py      # Pipeline SIRENE (INSEE)
│       ├── inpi.py        # Pipeline INPI (comptes annuels)
│       └── bodacc.py      # Pipeline BODACC (annonces légales)
└── data/
    ├── france_companies.duckdb  # Base de données (5.6 GB)
    └── downloads/               # Fichiers sources
```

---

## Sources de données

### 1. SIRENE (INSEE) ✅ Implémenté

**Registre officiel des entreprises françaises**

| Donnée | Description |
|--------|-------------|
| SIREN/SIRET | Identifiants uniques |
| Dénomination | Nom de l'entreprise |
| NAF/APE | Code activité (ex: 62.01Z = développement informatique) |
| Tranche effectifs | Approximation nb employés |
| Catégorie juridique | SAS, SARL, SA... |
| État administratif | Active / Cessée |
| Adresse | Siège social |

- **Source** : https://files.data.gouv.fr (Parquet)
- **Volume** : ~29M entreprises, ~42M établissements
- **Mise à jour** : Mensuelle

### 2. INPI (Data INPI) ✅ Implémenté

**Comptes annuels déposés (depuis 2017)**

| Donnée | Description |
|--------|-------------|
| Chiffre d'affaires | CA déclaré |
| Résultat net | Bénéfice/perte |
| Charges personnel | Masse salariale |
| Total actif/passif | Bilan |
| Capitaux propres | Fonds propres |
| Immobilisations | Actifs physiques |

- **Source** : data.cquest.org/inpi_rncs (miroir - recommandé)
- **Alternative** : SFTP data.inpi.fr (souvent indisponible)
- **Volume** : ~300 archives/an, ~6K bilans/archive
- **Format** : Archives 7z contenant XML (liasses fiscales)

> **Note** : Le SFTP officiel de l'INPI est hors service depuis octobre 2023.
> Le miroir data.cquest.org contient les données 2017-2023.

### 3. BODACC ✅ Implémenté

**Annonces légales (Bulletin Officiel)**

| Type | Contenu |
|------|---------|
| BODACC A | Ventes, créations, procédures collectives |
| BODACC B | Modifications, radiations |
| BODACC C | Dépôts de comptes annuels |

- **Source** : API OpenDataSoft (gratuit, sans auth)
- **Volume** : ~49K annonces/mois, ~1.6K/jour
- **Utilité** : Signaux (liquidations, dépôts récents, cessions)
- **Fonctionnalité** : Date windowing automatique (7 jours) pour contourner la limite API de 10K records

---

## État actuel

### ✅ Fait

- [x] Structure du projet Python
- [x] CLI avec Click (commandes `sirene`, `inpi`, `bodacc`, `search`, `export`)
- [x] Schéma DuckDB (6 tables)
- [x] Pipeline SIRENE complet (download + load)
- [x] **29M unités légales chargées**
- [x] **42M établissements chargées**
- [x] Base de données opérationnelle (5.6 GB)
- [x] Commande de recherche fonctionnelle
- [x] Pipeline BODACC complet avec date windowing
- [x] **~50K annonces légales chargées** (30 jours)
- [x] Pipeline INPI complet (via miroir data.cquest.org)
- [x] Support bilans Complets (C) et Simplifiés (S)
- [x] **Données financières 2020-2023 en cours de chargement**

### 🔄 À faire

- [ ] **Implémenter le scoring** (prochaine étape)
  - [ ] Créer une vue `v_opportunities` avec le scoring calculé
  - [ ] Ajouter commande `python cli.py scan` pour lancer l'analyse
- [ ] Export des résultats vers le dashboard web existant

### 💡 Améliorations futures

- [ ] Déduplication SIRENE (garder dernière période par SIREN)
- [ ] Enrichissement données (codes NAF → libellés)
- [ ] Dashboard web dédié
- [ ] Scoring configurables
- [ ] Alertes sur nouveaux dépôts BODACC

---

## Utilisation

### Installation

```bash
cd /home/jack/Trading/exploration-app/france-market-scanner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Commandes principales

```bash
# Initialiser la base
python cli.py init-db

# SIRENE (déjà fait)
python cli.py sirene download    # Télécharge ~2.8 GB
python cli.py sirene load        # Charge dans DuckDB

# INPI (via miroir data.cquest.org)
python cli.py inpi sync --years 2020-2023     # Télécharge + charge (recommandé)
python cli.py inpi download --years 2020-2023 --max-files 5  # Pour tester
python cli.py inpi load --year 2023           # Charge une année spécifique

# BODACC (chargé - 30 jours)
python cli.py bodacc sync --days 30     # Télécharge + charge (30 jours)
python cli.py bodacc sync --days 365    # Pour une année complète
python cli.py bodacc sync --year 2024   # Pour une année spécifique

# Recherche
python cli.py search --naf 62.01Z --departement 75
python cli.py search --name "CAPGEMINI"

# Export
python cli.py export \
  --query "SELECT * FROM sirene_unites_legales WHERE activite_principale LIKE '62%'" \
  --output tech_companies.parquet

# Stats
python cli.py db-info
```

### Requêtes SQL directes

```python
import duckdb

conn = duckdb.connect("data/france_companies.duckdb")

# Entreprises tech actives à Paris
conn.execute("""
    SELECT
        ul.siren,
        ul.denomination,
        ul.activite_principale,
        ul.tranche_effectifs,
        e.code_postal,
        e.libelle_commune
    FROM sirene_unites_legales ul
    JOIN sirene_etablissements e ON ul.siren = e.siren
    WHERE ul.activite_principale LIKE '62%'
      AND ul.etat_administratif = 'A'
      AND e.etablissement_siege = 'true'
      AND e.departement = '75'
    LIMIT 100
""").df()
```

---

## Schéma de données

### Tables SIRENE

```
sirene_unites_legales (29M lignes)
├── siren (identifiant)
├── denomination
├── activite_principale (NAF)
├── categorie_juridique
├── tranche_effectifs
├── etat_administratif (A=Active, C=Cessée)
└── date_creation

sirene_etablissements (42M lignes)
├── siret (identifiant)
├── siren (lien vers unité légale)
├── etablissement_siege (true/false)
├── activite_principale
├── tranche_effectifs
├── code_postal, libelle_commune, departement
└── etat_administratif
```

### Tables INPI (à remplir)

```
inpi_comptes_annuels
├── siren
├── date_cloture, annee_cloture
└── type_comptes (simplifié/complet)

inpi_compte_resultat
├── siren, annee_cloture
├── chiffre_affaires
├── charges_personnel
├── resultat_exploitation
└── resultat_net

inpi_bilan
├── siren, annee_cloture
├── total_actif, total_passif
├── capitaux_propres
├── immobilisations
└── disponibilites
```

### Table BODACC (~50K lignes)

```
bodacc_annonces
├── id (identifiant annonce)
├── siren (lien vers unité légale)
├── date_parution
├── type_bulletin (A/B/C)
├── famille, nature
├── denomination
├── adresse, code_postal, ville
├── type_procedure, tribunal (procédures collectives)
└── details (JSON - données complémentaires)
```

---

## Codes utiles

### Tranches d'effectifs

| Code | Signification |
|------|---------------|
| 00 | 0 salarié |
| 01 | 1-2 salariés |
| 02 | 3-5 salariés |
| 03 | 6-9 salariés |
| 11 | 10-19 salariés |
| 12 | 20-49 salariés |
| 21 | 50-99 salariés |
| 22 | 100-199 salariés |
| 31 | 200-249 salariés |
| 32 | 250-499 salariés |
| 41 | 500-999 salariés |
| 42 | 1000-1999 salariés |
| 51 | 2000-4999 salariés |
| 52 | 5000-9999 salariés |
| 53 | 10000+ salariés |
| NN | Non renseigné |

### Codes NAF intéressants (automatisables)

| Code | Activité |
|------|----------|
| 62.01Z | Programmation informatique |
| 62.02A | Conseil en systèmes informatiques |
| 62.09Z | Autres activités informatiques |
| 70.22Z | Conseil pour les affaires |
| 73.11Z | Activités des agences de publicité |
| 74.10Z | Activités spécialisées de design |
| 85.59A | Formation continue d'adultes |

---

## Prochaine étape immédiate

```bash
# 1. Charger les données financières INPI (optionnel pour scoring avancé)
python cli.py inpi sync --years 2020-2024

# 2. Implémenter le scoring des opportunités
python cli.py scan  # À implémenter
```

### Scoring à implémenter

Le scoring identifie les "pépites" : entreprises avec peu d'employés mais fort potentiel.

| Critère | Description | Poids |
|---------|-------------|-------|
| CA/Employé | Productivité par tête | 40% |
| Secteur | Activités automatisables (62.xx, 70.22Z...) | 30% |
| Marge nette | Résultat / CA | 15% |
| Actifs légers | Peu d'immobilisations | 15% |

**Signaux BODACC à exploiter :**
- Procédures collectives (opportunités de reprise)
- Cessions d'entreprises
- Modifications récentes (changement de dirigeant, etc.)

---

## Liens utiles

- [API SIRENE (INSEE)](https://api.gouv.fr/les-api/sirene_v3)
- [Data INPI](https://data.inpi.fr)
- [BODACC OpenData](https://bodacc-datadila.opendatasoft.com)
- [DuckDB Documentation](https://duckdb.org/docs/)
