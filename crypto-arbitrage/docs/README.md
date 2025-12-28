# 💰 Crypto Opportunity Scanner

Scanner modulaire et intelligent pour **identifier, visualiser et exploiter** des opportunités d'arbitrage crypto entre exchanges.

> **Objectif:** Comprendre les flux financiers crypto et détecter des opportunités profitables en tant que développeur/trader particulier.

## ✨ Fonctionnalités

- 🔍 **Scan d'arbitrage en temps réel** entre exchanges (Binance, Kraken, Coinbase, etc.)
- 📊 **Dashboard interactif** pour visualiser les opportunités
- 💾 **Stockage historique** pour analyser les patterns
- 🎯 **Calcul précis** du profit net (incluant tous les fees)
- 🧩 **Architecture modulaire** pour ajouter vos propres stratégies
- ⚡ **Scan continu** pour surveillance 24/7

## 🚀 Quick Start

```bash
# 1. Installation
pip install -r requirements.txt

# 2. Premier scan
python main.py --scan

# 3. Dashboard visuel
python main.py --dashboard
```

➡️ **Nouveau ?** Consultez [QUICKSTART.md](QUICKSTART.md) pour un guide en 5 minutes

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Démarrage rapide (5 min)
- **[GUIDE.md](GUIDE.md)** - Guide complet pour apprendre et gagner de l'argent
- **[config/config.example.yaml](config/config.example.yaml)** - Toutes les options de configuration

## 🎯 Modes d'Utilisation

### 1. Scan Unique
Vérifiez rapidement les opportunités actuelles :
```bash
python main.py --scan
```

### 2. Scan Continu
Surveillez en continu et accumulez des données :
```bash
python main.py --watch
```

### 3. Dashboard
Analysez visuellement les opportunités :
```bash
python main.py --dashboard
```

## 🏗️ Architecture

Le projet est **100% modulaire** pour faciliter l'extension :

```
src/
├── core/              # Framework de base
│   ├── scanner_base.py      # Classe abstraite pour scanners
│   ├── opportunity.py       # Modèle de données
│   └── exchange_manager.py  # Gestion des exchanges
├── strategies/        # Modules de stratégies
│   └── arbitrage/          # Arbitrage crypto
│       └── crypto_arbitrage.py
├── data/             # Stockage et persistence
│   └── storage.py
└── visualization/    # Dashboard Streamlit
    └── dashboard.py
```

## 📊 Stratégies Disponibles

### ✅ Arbitrage Crypto (Implémenté)
Détecte les différences de prix entre exchanges.

**Calcule :**
- Spread brut entre exchanges
- Frais de trading (maker/taker)
- Frais de retrait estimés
- Profit NET exploitable

**Exemple de détection :**
```
BTC/USDT: 0.75% profit
├─ Achat: Binance @ $50,000
├─ Vente: Kraken @ $50,400
├─ Spread: 0.80%
├─ Fees: -0.05%
└─ Profit NET: 0.75%
```

### 🔜 Stratégies Futures

Ajoutez facilement vos propres stratégies :
- **Triangular Arbitrage** : BTC → ETH → USDT → BTC
- **Funding Rate Arbitrage** : Long spot + Short perpetual
- **Mean Reversion** : Détection de sur/sous-évaluation
- **Momentum Trading** : Tendances fortes
- **Liquidation Sniping** : Cascades de liquidations

## 🎓 Pour les Débutants

**Vous avez peu de connaissances financières ?** Parfait ! Ce projet est fait pour :

1. **APPRENDRE** : Observer où sont les vrais flux financiers
2. **COMPRENDRE** : Identifier ce qui est exploitable
3. **TESTER** : Valider avec de petites sommes
4. **GAGNER** : Scaler progressivement ce qui marche

➡️ Lisez le [GUIDE.md](GUIDE.md) pour un plan d'action détaillé

## 📈 Exemple de Workflow

```bash
# Semaine 1-2 : Observer
python main.py --watch  # Laissez tourner 24-48h

# Analyser les données
python main.py --dashboard

# Identifier les meilleurs symboles et exchanges
# → Affiner config/config.yaml

# Semaine 3+ : Tester manuellement
# → Exécuter 1-2 arbitrages avec 100€
# → Mesurer profit réel vs théorique

# Mois 2+ : Automatiser si profitable
# → Ajouter auto-execution via API
```

## 🛠️ Personnalisation

### Modifier la Configuration

Éditez `config/config.yaml` :

```yaml
exchanges:
  - binance
  - kraken
  - coinbase

symbols:
  - BTC/USDT
  - ETH/USDT

scanner:
  min_profit: 0.5          # Profit minimum requis (%)
  min_confidence: 50       # Score de confiance minimum
  min_volume_24h: 1000000  # Volume minimum en USD
```

### Ajouter une Stratégie

```python
# src/strategies/ma_strategie/scanner.py
from src.core.scanner_base import ScannerBase
from src.core.opportunity import Opportunity, OpportunityType

class MaStrategieScanner(ScannerBase):
    def get_name(self) -> str:
        return "Ma Stratégie Personnalisée"

    def scan(self) -> List[Opportunity]:
        opportunities = []
        # Votre logique ici
        return opportunities
```

## ⚠️ Disclaimer Important

- Ce projet est **éducatif**
- Le trading comporte des **risques de perte**
- **Testez** avec de petites sommes d'abord
- Pas de garantie de profit
- Respectez les régulations locales

**Vous êtes seul responsable de vos décisions de trading.**

## 🧪 Tests

```bash
# Lancer les tests
pytest tests/ -v

# Test rapide
python tests/test_scanner.py
```

## 📦 Dépendances Principales

- **ccxt** : API unifiée pour exchanges crypto
- **streamlit** : Dashboard interactif
- **pandas / plotly** : Analyse et visualisation
- **loguru** : Logging avancé

## 🗺️ Roadmap

- [x] Architecture modulaire
- [x] Scanner arbitrage crypto
- [x] Dashboard de visualisation
- [x] Stockage historique SQLite
- [ ] Scanner triangular arbitrage
- [ ] Scanner funding rate arbitrage
- [ ] Auto-execution via API
- [ ] Système d'alertes (Telegram/Email)
- [ ] Backtesting engine
- [ ] Mobile app (React Native)

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des nouvelles stratégies
- Améliorer la documentation
- Partager vos résultats (anonymisés)

## 📜 License

MIT License - Utilisez librement pour apprendre et gagner de l'argent légalement.

---

**Fait par des développeurs, pour des développeurs qui veulent comprendre la finance.** 💪

Questions ? Consultez le [GUIDE.md](GUIDE.md) ou ouvrez une issue !
