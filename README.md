# 🏢 Exploration App - Analyseur d'Entreprises

Application d'analyse d'entreprises françaises via l'API Pappers. Détection automatique d'insights financiers : croissance, marges élevées, changements de direction.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 Fonctionnalités

- 📊 **Analyse financière automatique** : Détection de croissance du CA et marges élevées
- 👔 **Suivi des dirigeants** : Identification des changements de direction récents
- 💾 **Stockage SQLite** : Historique de tous les insights détectés
- 🔍 **Recherche intelligente** : Recherche d'entreprises par nom, secteur, département
- 📈 **Score de santé financière** : Évaluation automatique basée sur les indicateurs
- 🤖 **API Pappers** : Accès aux données officielles d'entreprises françaises

## 🚀 Démarrage rapide

### 1. Installation

```bash
# Cloner le repository
git clone https://github.com/evausesgit/exploration-app.git
cd exploration-app

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copier le fichier de configuration
cp .env.example .env

# Éditer .env et ajouter votre clé API Pappers
# PAPPERS_API_KEY=votre_cle_ici
```

Obtenez une clé API gratuite sur : https://www.pappers.fr/api
(Plan gratuit : 500 requêtes/mois)

### 3. Test

```bash
# Tester la connexion API
python test_pappers_connection.py
```

### 4. Utilisation

```bash
# Script de démonstration complet
python demo_companies.py

# Ou script interactif
python analyze_companies.py
```

## 📖 Documentation

- 📘 **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Guide de démarrage complet
- 📗 **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Démarrage en 3 minutes
- 📕 **[docs/GUIDE.md](docs/GUIDE.md)** - Documentation détaillée avec exemples
- 📊 **[docs/PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Résumé technique du projet

👉 **[Voir toute la documentation](docs/)**

## 💡 Exemples

### Analyser une liste d'entreprises

```python
from src.strategies.companies import CompanyAnalyzer

config = {
    'siren_list': ['552032534', '542051180'],  # DANONE, L'ORÉAL
    'min_growth_rate': 10,  # Croissance minimum 10%
    'min_margin': 5,        # Marge minimum 5%
}

analyzer = CompanyAnalyzer(config)
insights = analyzer.run_scan()

for insight in insights:
    print(f"{insight.data['denomination']}: {insight.metadata['message']}")
```

### Rechercher et analyser

```python
from src.data.pappers_client import PappersClient

client = PappersClient()

# Recherche
companies = client.recherche("carrefour", max_results=10)

# Détails d'une entreprise
data = client.get_entreprise("552032534")
print(f"{data['nom_entreprise']} - CA: {data['finances'][0]['chiffre_affaires']:,.0f}€")
```

## 🔍 Types d'insights détectés

| Type | Description | Critères |
|------|-------------|----------|
| **FINANCIAL_GROWTH** | Croissance forte du CA | Croissance ≥ 10% |
| **HIGH_MARGIN** | Marges élevées | Marge nette ≥ 5% |
| **MANAGEMENT_CHANGE** | Nouveaux dirigeants | Prise de poste < 6 mois |

## 📊 Architecture

```
exploration-app/
├── src/
│   ├── core/                  # Classes de base
│   │   ├── scanner_base.py    # Scanner abstrait
│   │   └── opportunity.py     # Modèle d'insight
│   ├── data/
│   │   ├── pappers_client.py  # Client API Pappers
│   │   └── storage.py         # Stockage SQLite
│   └── strategies/
│       ├── companies/         # Analyse d'entreprises ⭐
│       │   └── company_analyzer.py
│       └── arbitrage/         # Analyse crypto (legacy)
│
├── demo_companies.py          # Script de démonstration
├── analyze_companies.py       # Script interactif
└── test_pappers_connection.py # Test API
```

## 🛠️ Technologies

- **Python 3.9+**
- **API Pappers** - Données d'entreprises françaises
- **SQLite** - Stockage local
- **Loguru** - Logging avancé
- **Requests** - Client HTTP

## 📝 Exemples de résultats

```
📊 Analyse de 3 grandes entreprises françaises...

✅ 4 insights détectés:

1. DANONE
   └─ Type: financial_growth
   └─ Croissance de 47.4% du CA
   └─ Confiance: 74/100

2. DANONE
   └─ Type: high_margin
   └─ Marge nette de 57.5%
   └─ Confiance: 100/100

3. TOTALENERGIES SE
   └─ Type: financial_growth
   └─ Croissance de 924887.7% du CA
   └─ Confiance: 100/100
```

## 🔒 Sécurité

- ✅ Clés API protégées dans `.env` (non versionné)
- ✅ Rate limiting automatique
- ✅ Gestion d'erreurs robuste
- ✅ Validation des entrées

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commiter vos changements (`git commit -m 'Add: nouvelle fonctionnalité'`)
4. Pusher (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE) pour plus de détails

## ⚠️ Avertissement

Cette application est à but éducatif et d'analyse. Vérifiez toujours les données avant toute utilisation professionnelle. Les données proviennent de l'API Pappers et peuvent être incomplètes pour certaines entreprises.

## 🔗 Liens utiles

- **API Pappers** : https://www.pappers.fr/api
- **Documentation API** : https://www.pappers.fr/api/documentation
- **Support** : [Issues GitHub](https://github.com/evausesgit/exploration-app/issues)

## ✨ Crédits

Développé avec l'aide de [Claude Code](https://claude.com/claude-code)

---

**Made with ❤️ for French company analysis**
