# 🏢 Companies Analysis

Exploration et analyse d'entreprises françaises via l'API Pappers.

## 🎯 Objectif

Détecter automatiquement des insights financiers intéressants :
- **🤖 Opportunités d'automatisation IA** : Entreprises à fort ratio CA/effectif dans des secteurs automatisables
- Croissance forte du chiffre d'affaires
- Marges élevées
- Changements de direction récents

## 🚀 Démarrage rapide

```bash
# 1. Configuration
cp .env.example .env
# Ajoutez votre PAPPERS_API_KEY

# 2. Installation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Test
python scripts/test_pappers_connection.py

# 4. Scanner d'automatisation IA
python scripts/explore_ai_automation.py

# Ou lancer le dashboard interactif
streamlit run dashboard.py
```

## 📖 Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Démarrage en 3 minutes
- **[docs/GUIDE.md](docs/GUIDE.md)** - Guide complet avec exemples
- **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Guide détaillé

## 📊 Scripts disponibles

| Script | Description |
|--------|-------------|
| `explore_ai_automation.py` | 🤖 Scanner d'opportunités d'automatisation IA |
| `demo_companies.py` | Démonstration complète |
| `analyze_companies.py` | Analyse interactive |
| `test_pappers_connection.py` | Test de connexion API |

## 🤖 Scanner d'automatisation IA

Le scanner d'automatisation IA identifie les entreprises avec un fort potentiel d'automatisation en analysant :

### Critères de détection
- **Ratio CA/effectif élevé** (>100k€/salarié) : Indicateur de productivité automatisable
- **Secteurs à fort levier IA** : Conseil, marketing digital, SaaS, formation, courtage, services spécialisés
- **Peu d'actifs physiques** : Favorise les activités de services immatériels
- **Rentabilité démontrée** : Entreprises saines avec marges positives

### Dashboard interactif

```bash
streamlit run dashboard.py
```

Le dashboard permet de :
- Configurer les filtres de recherche (secteurs, départements, critères financiers)
- Visualiser les opportunités détectées avec scores d'automatisation
- Analyser les distributions par secteur et ratios financiers
- Exporter les résultats en CSV

### Utilisation CLI

```bash
# Scanner de base
python scripts/explore_ai_automation.py

# Scanner personnalisé
python scripts/explore_ai_automation.py \
  --secteurs conseil saas_tech formation \
  --departements 75 92 \
  --min-ca 2000000 \
  --max-effectif 5 \
  --min-score 70 \
  --output-csv data/top_opportunities.csv
```

## 🔑 API Pappers

Obtenez une clé gratuite : https://www.pappers.fr/api
- Plan gratuit : 500 requêtes/mois
- Données officielles d'entreprises françaises

## 📁 Structure

```
companies-analysis/
├── scripts/         Scripts exécutables
├── docs/           Documentation
├── data/           Bases de données (non versionné)
├── src/            Code source
└── config/         Configuration
```

## 💡 Exemples

### Scanner d'automatisation IA

```python
from src.strategies.ai_automation_scanner import AIAutomationScanner

scanner = AIAutomationScanner({
    'pappers_api_key': 'YOUR_API_KEY',
    'secteurs': ['conseil', 'marketing_digital', 'saas_tech'],
    'min_ca': 1000000,  # 1M€
    'max_effectif': 10,
    'min_ca_per_employee': 100000  # 100k€
})

opportunities = scanner.scan()
for opp in opportunities:
    print(f"{opp.data['denomination']}: Score {opp.confidence}/100")
```

### Analyse d'entreprises spécifiques

```python
from src.strategies.companies import CompanyAnalyzer

analyzer = CompanyAnalyzer({
    'siren_list': ['552032534'],  # DANONE
    'min_growth_rate': 10
})
insights = analyzer.run_scan()
```

## 🔙 Retour

← [Retour au projet principal](../README.md)
