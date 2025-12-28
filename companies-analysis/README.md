# 🏢 Companies Analysis

Exploration et analyse d'entreprises françaises via l'API Pappers.

## 🎯 Objectif

Détecter automatiquement des insights financiers intéressants :
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

# 4. Lancement
python scripts/demo_companies.py
```

## 📖 Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Démarrage en 3 minutes
- **[docs/GUIDE.md](docs/GUIDE.md)** - Guide complet avec exemples
- **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Guide détaillé

## 📊 Scripts disponibles

| Script | Description |
|--------|-------------|
| `demo_companies.py` | Démonstration complète |
| `analyze_companies.py` | Analyse interactive |
| `test_pappers_connection.py` | Test de connexion API |

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
