# ₿ Crypto Arbitrage

Exploration des opportunités d'arbitrage sur les marchés crypto.

## 🎯 Objectif

Détecter automatiquement les opportunités d'arbitrage :
- Arbitrage simple entre exchanges
- Arbitrage triangulaire
- Différences de prix significatives

## 🚀 Démarrage rapide

```bash
# 1. Configuration (optionnelle pour lecture seule)
cp .env.example .env

# 2. Installation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Scanner simple
python scripts/main.py

# 4. Scanner continu
./scripts/run_continuous_scan.sh
```

## 📖 Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Démarrage rapide
- **[docs/GUIDE.md](docs/GUIDE.md)** - Guide complet
- **[docs/README.md](docs/README.md)** - Documentation générale

## 📊 Scripts disponibles

| Script | Description |
|--------|-------------|
| `main.py` | Scanner principal |
| `analyze_opportunities.py` | Analyse des résultats |
| `run_continuous_scan.sh` | Scanner en continu (arrière-plan) |

## 📈 Exchanges supportés

10 exchanges majeurs :
- Binance, Kraken, Coinbase
- KuCoin, Bybit, OKX
- Gate.io, Huobi, Bitfinex, MEXC

## 📁 Structure

```
crypto-arbitrage/
├── scripts/         Scripts exécutables
├── docs/           Documentation
├── data/           Opportunités détectées (non versionné)
├── src/            Code source
└── config/         Configuration
```

## 💡 Exemples

```python
from src.strategies.arbitrage import CryptoArbitrageScanner

scanner = CryptoArbitrageScanner({
    'exchanges': ['binance', 'kraken'],
    'symbols': ['BTC/USDT'],
    'min_profit': 0.5
})
opportunities = scanner.run_scan()
```

## ⚠️ Avertissement

Le trading crypto comporte des risques. Cette application est à but éducatif.

## 🔙 Retour

← [Retour au projet principal](../README.md)
