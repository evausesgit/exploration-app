# Guide d'utilisation - Analyse d'entreprises avec Pappers API

## 📋 Table des matières

1. [Introduction](#introduction)
2. [Configuration](#configuration)
3. [Utilisation rapide](#utilisation-rapide)
4. [Fonctionnalités](#fonctionnalités)
5. [API Reference](#api-reference)
6. [Exemples avancés](#exemples-avancés)

## Introduction

Cette application permet d'analyser les entreprises françaises via l'API Pappers pour détecter des insights intéressants :

- **Croissance financière** : Entreprises avec forte croissance du CA
- **Marges élevées** : Entreprises avec bonne rentabilité
- **Changements de direction** : Nouveaux dirigeants récents
- **Santé financière** : Score de santé basé sur les indicateurs

## Configuration

### 1. Obtenir une clé API Pappers

1. Créez un compte sur [pappers.fr](https://www.pappers.fr/api)
2. Obtenez votre clé API (plans gratuits disponibles)
3. Le plan gratuit permet 500 requêtes/mois

### 2. Configuration de l'environnement

Copiez le fichier `.env.example` vers `.env` :

```bash
cp .env.example .env
```

Éditez `.env` et ajoutez votre clé :

```env
PAPPERS_API_KEY=votre_cle_api_ici
```

### 3. Installation des dépendances

```bash
pip install -r requirements.txt
```

## Utilisation rapide

### Script d'exemple

Le moyen le plus simple est d'utiliser le script fourni :

```bash
python analyze_companies.py
```

Ce script :
- Analyse une liste de SIREN prédéfinie
- Permet de rechercher des entreprises par nom
- Sauvegarde les insights dans `data/companies.db`
- Affiche des statistiques

### Analyser vos propres entreprises

Éditez `analyze_companies.py` et modifiez la liste de SIREN :

```python
siren_list = [
    "552032534",  # Votre entreprise 1
    "542065479",  # Votre entreprise 2
    # Ajoutez vos SIREN ici
]
```

## Fonctionnalités

### Types d'insights détectés

#### 1. Croissance financière (FINANCIAL_GROWTH)

Détecte les entreprises avec forte croissance du chiffre d'affaires.

**Critères** :
- Croissance CA ≥ 10% (configurable)
- CA minimum : 100k€ (configurable)
- Compare les 2 derniers exercices

**Exemple** :
```
Type: financial_growth
Message: Croissance de 25.3% du CA
Confiance: 62/100
```

#### 2. Marges élevées (HIGH_MARGIN)

Détecte les entreprises avec bonne rentabilité.

**Critères** :
- Marge nette ≥ 5% (configurable)
- CA minimum : 100k€

**Exemple** :
```
Type: high_margin
Message: Marge nette de 12.5%
Confiance: 77/100
```

#### 3. Changement de direction (MANAGEMENT_CHANGE)

Détecte les nouveaux dirigeants (moins de 6 mois).

**Exemple** :
```
Type: management_change
Message: Nouveau Président: Jean Dupont
Confiance: 85/100
```

### Configuration de l'analyseur

```python
config = {
    'siren_list': ['123456789', '987654321'],
    'min_ca': 100000,           # CA minimum en €
    'min_growth_rate': 10,      # Croissance minimum en %
    'min_margin': 5,            # Marge minimum en %
    'min_confidence': 50        # Confiance minimum
}

analyzer = CompanyAnalyzer(config)
```

## API Reference

### PappersClient

Client pour interagir avec l'API Pappers.

#### Méthodes principales

```python
from src.data.pappers_client import PappersClient

client = PappersClient()

# Récupérer les données complètes d'une entreprise
data = client.get_entreprise("552032534")

# Récupérer uniquement les finances
finances = client.get_finances("552032534")

# Récupérer les dirigeants
dirigeants = client.get_dirigeants("552032534")

# Rechercher des entreprises
results = client.recherche("carrefour", max_results=10)

# Calculer un score de santé financière
score = client.get_financial_health_score("552032534")
# Retourne un score de 0 à 100
```

### CompanyAnalyzer

Scanner qui analyse les entreprises et détecte les insights.

#### Méthodes principales

```python
from src.strategies.companies import CompanyAnalyzer

analyzer = CompanyAnalyzer(config)

# Scanner une liste de SIREN (depuis config)
opportunities = analyzer.run_scan()

# Analyser une seule entreprise
opportunities = analyzer.analyze_single_company("552032534")

# Rechercher et analyser
opportunities = analyzer.search_and_analyze("carrefour", max_companies=5)
```

### OpportunityStorage

Stockage et requêtes sur les insights.

```python
from src.data.storage import OpportunityStorage

storage = OpportunityStorage("data/companies.db")

# Sauvegarder
storage.save(opportunity)
storage.save_batch(opportunities)

# Récupérer les insights récents
recent = storage.get_recent(limit=100)

# Récupérer les meilleurs insights
best = storage.get_best_opportunities(
    min_profit=10,
    min_confidence=70,
    limit=50
)

# Statistiques
stats = storage.get_statistics()
```

## Exemples avancés

### Exemple 1 : Analyser un secteur spécifique

```python
from src.strategies.companies import CompanyAnalyzer
from src.data.pappers_client import PappersClient

# Recherche d'entreprises dans un secteur
pappers = PappersClient()
companies = pappers.recherche(
    "restauration",
    max_results=20,
    departement="75"  # Paris
)

# Récupère les SIREN
siren_list = [c['siren'] for c in companies if 'siren' in c]

# Analyse
config = {
    'siren_list': siren_list,
    'min_growth_rate': 15,
    'min_margin': 8
}

analyzer = CompanyAnalyzer(config)
opportunities = analyzer.run_scan()

print(f"Trouvé {len(opportunities)} insights dans le secteur restauration à Paris")
```

### Exemple 2 : Monitoring continu

```python
import time
from datetime import datetime

analyzer = CompanyAnalyzer(config)
storage = OpportunityStorage()

while True:
    print(f"\n[{datetime.now()}] Scanning...")

    opportunities = analyzer.run_scan()

    if opportunities:
        storage.save_batch(opportunities)
        print(f"Saved {len(opportunities)} new insights")

    # Attendre 1 heure
    time.sleep(3600)
```

### Exemple 3 : Filtrer les insights

```python
# Récupère tous les insights récents
opportunities = analyzer.run_scan()

# Filtre uniquement la croissance forte
growth_opps = [
    opp for opp in opportunities
    if opp.opportunity_type == OpportunityType.FINANCIAL_GROWTH
    and opp.profit_potential >= 20  # Croissance ≥ 20%
]

# Filtre par confiance
high_confidence = [
    opp for opp in opportunities
    if opp.confidence >= 80
]

print(f"Croissance forte: {len(growth_opps)}")
print(f"Haute confiance: {len(high_confidence)}")
```

### Exemple 4 : Export CSV

```python
import csv
from src.data.storage import OpportunityStorage

storage = OpportunityStorage("data/companies.db")
insights = storage.get_recent(limit=1000)

with open('export_insights.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'timestamp', 'siren', 'denomination', 'type',
        'message', 'confidence'
    ])

    writer.writeheader()

    for insight in insights:
        import json
        data = json.loads(insight['data'])
        metadata = json.loads(insight['metadata'])

        writer.writerow({
            'timestamp': insight['timestamp'],
            'siren': insight['symbol'],
            'denomination': data.get('denomination', ''),
            'type': insight['opportunity_type'],
            'message': metadata.get('message', ''),
            'confidence': insight['confidence']
        })

print("Export terminé: export_insights.csv")
```

## Limites et bonnes pratiques

### Rate limiting

- L'API Pappers limite à ~5 requêtes/seconde
- Le client gère automatiquement le rate limiting
- Pour de gros volumes, espacez vos requêtes

### Quotas

- **Plan gratuit** : 500 requêtes/mois
- **Plans payants** : Quotas plus élevés
- Surveillez votre consommation sur pappers.fr

### Performances

- Une analyse complète d'une entreprise = 1 requête API
- Utilisez `search_and_analyze()` avec parcimonie
- Privilégiez l'analyse de listes SIREN prédéfinies

### Données

- Les données financières peuvent être incomplètes
- Toutes les entreprises n'ont pas de comptes publics
- Vérifiez toujours les données avant utilisation

## Support

- Documentation API Pappers : https://www.pappers.fr/api/documentation
- Issues GitHub : (votre repo)
- Email : (votre email)

## Licence

MIT License - Voir LICENSE pour plus de détails
