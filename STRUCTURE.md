# 📁 Structure du Projet

## 🗂️ Organisation

```
exploration-app/
│
├── 📄 README.md                    # Documentation principale du projet
├── 📄 LICENSE                      # Licence MIT
├── 📄 requirements.txt             # Dépendances Python
├── 📄 .env.example                 # Template de configuration
├── 📄 .gitignore                   # Fichiers ignorés par git
│
├── 📚 docs/                        # Documentation
│   ├── README.md                   # Index de la documentation
│   ├── GETTING_STARTED.md          # Guide de démarrage complet
│   ├── QUICKSTART.md               # Démarrage rapide (3 min)
│   ├── GUIDE.md                    # Guide détaillé avec exemples
│   └── PROJECT_SUMMARY.md          # Résumé technique du projet
│
├── 🐍 Scripts Python
│   ├── demo_companies.py           # Démonstration complète
│   ├── analyze_companies.py        # Script interactif
│   ├── test_pappers_connection.py  # Test de connexion API
│   ├── main.py                     # Script crypto (legacy)
│   └── analyze_opportunities.py    # Analyse crypto (legacy)
│
├── 📦 src/                         # Code source
│   ├── core/                       # Classes de base
│   │   ├── scanner_base.py         # Scanner abstrait
│   │   ├── opportunity.py          # Modèle d'insights
│   │   └── exchange_manager.py     # Gestion exchanges (crypto)
│   │
│   ├── data/                       # Couche données
│   │   ├── pappers_client.py       # Client API Pappers ⭐
│   │   └── storage.py              # Stockage SQLite
│   │
│   ├── strategies/                 # Stratégies d'analyse
│   │   ├── companies/              # Analyse d'entreprises ⭐
│   │   │   └── company_analyzer.py
│   │   ├── arbitrage/              # Arbitrage crypto (legacy)
│   │   └── triangular/             # Arbitrage triangulaire (legacy)
│   │
│   └── visualization/              # Visualisation (legacy)
│       └── dashboard.py
│
├── 🧪 tests/                       # Tests unitaires
│   ├── __init__.py
│   └── test_scanner.py
│
├── ⚙️ config/                      # Configuration
│   ├── config.yaml
│   └── config.example.yaml
│
├── 📦 archive/                     # Fichiers historiques
│   └── README.md                   # Index de l'archive
│
├── 📊 data/                        # Données (non versionnées)
│   └── companies.db                # Base SQLite des insights
│
├── 📝 logs/                        # Logs (non versionnés)
│   └── *.log
│
└── 🐍 venv/                        # Environnement virtuel (non versionné)
```

## 🎯 Fichiers principaux

### À la racine

| Fichier | Description |
|---------|-------------|
| `README.md` | Documentation principale, point d'entrée du projet |
| `LICENSE` | Licence MIT |
| `requirements.txt` | Dépendances Python à installer |
| `.env.example` | Template pour les variables d'environnement |
| `.gitignore` | Fichiers ignorés par Git |

### Documentation (`docs/`)

| Fichier | Quand l'utiliser |
|---------|------------------|
| `GETTING_STARTED.md` | Première fois, vue d'ensemble complète |
| `QUICKSTART.md` | Pour démarrer rapidement (3 min) |
| `GUIDE.md` | Documentation détaillée, exemples avancés |
| `PROJECT_SUMMARY.md` | Comprendre l'architecture technique |

### Scripts

| Script | Usage |
|--------|-------|
| `demo_companies.py` | **Recommandé** - Démonstration complète automatique |
| `analyze_companies.py` | Script interactif avec saisie utilisateur |
| `test_pappers_connection.py` | Tester la connexion API Pappers |

## 🚀 Démarrage rapide

```bash
# 1. Configuration
cp .env.example .env
# Ajoutez votre PAPPERS_API_KEY dans .env

# 2. Installation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Test
python test_pappers_connection.py

# 4. Lancement
python demo_companies.py
```

## 📚 Navigation

- **Débuter** : `docs/GETTING_STARTED.md`
- **Vite commencer** : `docs/QUICKSTART.md`
- **Apprendre** : `docs/GUIDE.md`
- **Architecture** : `docs/PROJECT_SUMMARY.md`

## 🔒 Fichiers non versionnés

Ces fichiers sont dans `.gitignore` :

- `.env` - Vos clés API (sécurité)
- `venv/` - Environnement virtuel Python
- `data/` - Bases de données SQLite
- `logs/` - Fichiers de logs
- `__pycache__/` - Fichiers Python compilés
- `*.db`, `*.sqlite` - Bases de données

## 📦 Archive

Le dossier `archive/` contient les fichiers historiques du développement (documentation ancienne, notes de développement). Ces fichiers ne sont plus utilisés mais conservés pour référence.
