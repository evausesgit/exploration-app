# Exploration App - Analyse de données

Cette application offre deux modes d'exploration :

1. **Crypto** : Arbitrage et opportunités sur les marchés crypto
2. **Entreprises** : Analyse d'entreprises françaises via API Pappers

## 🚀 Démarrage rapide

### Analyse d'entreprises (Recommandé)

```bash
# 1. Configuration
cp .env.example .env
# Ajoutez votre clé PAPPERS_API_KEY dans .env

# 2. Installation
pip install -r requirements.txt

# 3. Lancement
python analyze_companies.py
```

📖 **Guide complet** : [QUICKSTART_ENTREPRISES.md](QUICKSTART_ENTREPRISES.md)

### Analyse crypto

```bash
# 1. Configuration
cp .env.example .env

# 2. Installation
pip install -r requirements.txt

# 3. Lancement
python main.py
```

📖 **Guide complet** : [README.md](README.md) (ancien guide crypto)

## 📁 Structure du projet

```
exploration-app/
├── src/
│   ├── core/              # Classes de base (ScannerBase, Opportunity)
│   ├── data/
│   │   ├── storage.py     # Stockage SQLite
│   │   └── pappers_client.py  # Client API Pappers
│   └── strategies/
│       ├── arbitrage/     # Stratégies crypto
│       ├── triangular/    # Arbitrage triangulaire
│       └── companies/     # Analyse d'entreprises ⭐ NOUVEAU
│
├── analyze_companies.py   # Script analyse entreprises ⭐ NOUVEAU
├── main.py                # Script analyse crypto
│
├── QUICKSTART_ENTREPRISES.md  # Démarrage rapide entreprises ⭐
├── GUIDE_ENTREPRISES.md       # Guide complet entreprises ⭐
├── README.md                  # Guide crypto (ancien)
└── data/
    ├── companies.db       # Base de données entreprises
    └── opportunities.db   # Base de données crypto
```

## 🎯 Fonctionnalités

### Mode Entreprises

- ✅ Récupération de données d'entreprises françaises
- ✅ Analyse des données financières (CA, résultats, marges)
- ✅ Détection de croissance forte
- ✅ Identification de marges élevées
- ✅ Suivi des changements de direction
- ✅ Stockage et historique des insights

### Mode Crypto

- ✅ Arbitrage simple entre exchanges
- ✅ Arbitrage triangulaire
- ✅ Scanner temps réel
- ✅ Dashboard de visualisation
- ✅ Stockage des opportunités

## 🔑 Configuration

Créez un fichier `.env` :

```env
# Pour l'analyse d'entreprises
PAPPERS_API_KEY=votre_cle_pappers

# Pour le mode crypto (optionnel)
BINANCE_API_KEY=votre_cle_binance
BINANCE_API_SECRET=votre_secret_binance

# Configuration générale
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 📊 Exemples d'utilisation

### Analyser des entreprises

```python
from src.strategies.companies import CompanyAnalyzer

config = {
    'siren_list': ['552032534', '542065479'],
    'min_growth_rate': 15,
    'min_margin': 8
}

analyzer = CompanyAnalyzer(config)
insights = analyzer.run_scan()

for insight in insights:
    print(f"{insight.data['denomination']}")
    print(f"  {insight.metadata['message']}")
```

### Rechercher une entreprise

```python
from src.data.pappers_client import PappersClient

client = PappersClient()

# Recherche
results = client.recherche("carrefour", max_results=5)

# Récupère les détails
for company in results:
    siren = company['siren']
    data = client.get_entreprise(siren)
    finances = client.get_finances(siren)
```

### Scanner crypto

```python
from src.strategies.arbitrage import CryptoArbitrageScanner

config = {
    'exchanges': ['binance', 'kraken'],
    'symbols': ['BTC/USDT', 'ETH/USDT'],
    'min_profit': 0.5
}

scanner = CryptoArbitrageScanner(config)
opportunities = scanner.run_scan()
```

## 📖 Documentation

- **Entreprises** :
  - [Démarrage rapide](QUICKSTART_ENTREPRISES.md)
  - [Guide complet](GUIDE_ENTREPRISES.md)

- **Crypto** :
  - [Guide original](README.md)
  - [Guide d'utilisation](README_UTILISATION.md)

## 🛠️ Développement

### Structure modulaire

Le projet utilise une architecture modulaire :

- **`src/core/`** : Classes de base réutilisables
- **`src/strategies/`** : Stratégies d'analyse (crypto ou entreprises)
- **`src/data/`** : Clients API et stockage

### Ajouter une nouvelle stratégie

1. Créez un nouveau module dans `src/strategies/`
2. Héritez de `ScannerBase`
3. Implémentez `scan()` et `get_name()`

```python
from src.core.scanner_base import ScannerBase
from src.core.opportunity import Opportunity, OpportunityType

class MyScanner(ScannerBase):
    def get_name(self) -> str:
        return "MyScanner"

    def scan(self) -> List[Opportunity]:
        # Votre logique ici
        return opportunities
```

## 🔒 Sécurité

- Ne commitez JAMAIS votre fichier `.env`
- Utilisez des clés API en lecture seule quand possible
- Surveillez vos quotas API

## 📝 Licence

MIT License

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## ⚠️ Avertissement

- **Entreprises** : Vérifiez toujours les données avant utilisation professionnelle
- **Crypto** : Le trading comporte des risques. Cette application est à but éducatif.

## 💡 Support

- Documentation : Voir les fichiers GUIDE_*.md
- Issues : (votre repo GitHub)
- Email : (votre email)

---

**Bon voyage dans l'exploration de données ! 🚀**
