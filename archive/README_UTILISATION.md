# 🚀 Guide d'Utilisation - Crypto Opportunity Scanner

## 📋 Table des Matières

1. [Quick Start](#quick-start)
2. [Commandes Principales](#commandes-principales)
3. [Analyser les Résultats](#analyser-les-résultats)
4. [Dashboard Visuel](#dashboard-visuel)
5. [Configuration Avancée](#configuration-avancée)
6. [FAQ](#faq)

---

## Quick Start

### 1. Premier Scan (5 minutes)

```bash
python3.9 main.py --scan
```

Cette commande:
- ✅ Scanne 10 exchanges
- ✅ Vérifie 25 paires crypto
- ✅ Détecte les opportunités d'arbitrage
- ✅ Sauvegarde dans `data/opportunities.db`

### 2. Analyser les Résultats

```bash
python3.9 analyze_opportunities.py
```

Cette commande affiche:
- 📊 Statistiques générales
- 🏆 Top 10 opportunités
- 💎 Symboles les plus profitables
- 💡 Recommandations personnalisées

### 3. Scan Continu (24-48h recommandé)

```bash
# Option 1: Script automatique
./run_continuous_scan.sh

# Option 2: Commande directe
python3.9 main.py --watch
```

Laissez tourner pendant 24-48h pour accumuler des données!

---

## Commandes Principales

### 🔍 Scan Unique

```bash
python3.9 main.py --scan
```

**Quand l'utiliser**:
- Vérifier rapidement s'il y a des opportunités
- Tester après avoir changé la configuration
- Vérifier un symbole spécifique

**Durée**: 2-5 minutes

### 🔄 Scan Continu

```bash
# En avant-plan (voir les logs en direct)
python3.9 main.py --watch

# En arrière-plan (recommandé)
./run_continuous_scan.sh
```

**Quand l'utiliser**:
- Accumulation de données sur plusieurs heures/jours
- Identification de patterns temporels
- Détection d'opportunités rares

**Durée**: 24-48h recommandé

**Voir les logs en temps réel**:
```bash
tail -f logs/scanner.log
```

**Arrêter le scan**:
```bash
# Si lancé avec le script
kill $(cat .scanner_pid)

# Ou
pkill -f "main.py --watch"
```

### 📊 Dashboard Interactif

```bash
python3.9 main.py --dashboard
```

Ouvre un dashboard web sur `http://localhost:8501`

**Fonctionnalités**:
- 📈 Graphiques interactifs
- 🔍 Filtres par exchange, symbole, profit
- ⏰ Analyse temporelle
- 💾 Export des données

---

## Analyser les Résultats

### Script d'Analyse Automatique

```bash
python3.9 analyze_opportunities.py
```

**Affiche**:
```
📊 CRYPTO ARBITRAGE OPPORTUNITIES REPORT
==========================================

📅 Generated: 2025-12-27 17:00:00
📈 Total opportunities found: 42

📈 GENERAL STATISTICS
==========================================
💰 Profit Statistics:
   - Average profit: 0.65%
   - Max profit: 2.1%

🏆 TOP 10 OPPORTUNITIES
==========================================
1. BTC/USDT
   💰 Profit: 2.1%
   📊 Confidence: 85/100
   🏷️  Strategy: Crypto Arbitrage Scanner

...
```

### Analyse Manuelle (SQLite)

```bash
# Ouvrir la base de données
sqlite3 data/opportunities.db

# Queries utiles:
sqlite> SELECT symbol, profit_potential, confidence
        FROM opportunities
        WHERE profit_potential > 1.0
        ORDER BY profit_potential DESC;

sqlite> SELECT COUNT(*), AVG(profit_potential)
        FROM opportunities
        GROUP BY symbol;
```

### Export Excel/CSV

```bash
python3.9 -c "
import pandas as pd
import sqlite3

conn = sqlite3.connect('data/opportunities.db')
df = pd.read_sql_query('SELECT * FROM opportunities', conn)
df.to_csv('opportunities_export.csv', index=False)
df.to_excel('opportunities_export.xlsx', index=False)
print('✅ Export completed!')
"
```

---

## Dashboard Visuel

### Lancer le Dashboard

```bash
python3.9 main.py --dashboard
```

Puis ouvrir: **http://localhost:8501**

### Fonctionnalités du Dashboard

#### 1. Scan en Direct
- Bouton "Lancer Scan"
- Affichage des opportunités en temps réel
- Rafraîchissement automatique

#### 2. Opportunités Récentes
- Table interactive des dernières opportunités
- Tri par profit, confiance, date
- Filtres multiples

#### 3. Analyses et Graphiques
- 📈 Évolution du profit dans le temps
- 📊 Distribution par exchange
- 🎯 Heatmap des meilleurs moments
- 💎 Top symboles profitables

#### 4. Configuration
- Ajuster les paramètres en direct
- Sauvegarder les configurations
- Comparer différentes stratégies

---

## Configuration Avancée

### Fichier de Configuration

Éditez `config/config.yaml`:

```yaml
# Exchanges à scanner
exchanges:
  - binance
  - kraken
  # Ajouter/retirer des exchanges ici

# Symboles à scanner
symbols:
  - BTC/USDT
  - ETH/USDT
  # Ajouter/retirer des symboles ici

# Paramètres de scan
scanner:
  min_profit: 0.3              # Profit minimum requis (%)
  min_confidence: 40           # Confiance minimum (0-100)
  min_volume_24h: 500000       # Volume 24h minimum (USD)
  include_withdrawal_fee: true # Inclure frais de retrait
  scan_interval: 45            # Intervalle entre scans (secondes)
```

### Ajouter des Exchanges

Exchanges supportés via CCXT (120+):
```yaml
exchanges:
  # Tier 1 (gros volumes, fiables)
  - binance
  - coinbase
  - kraken
  - kucoin
  - bybit
  - okx

  # Tier 2 (volumes moyens)
  - gateio
  - huobi
  - bitfinex
  - mexc

  # Autres (à vos risques)
  - bitstamp
  - gemini
  - bittrex
  # ... voir https://ccxt.com
```

### Ajouter des Symboles

Formats supportés:
```yaml
symbols:
  # Contre USDT (recommandé)
  - BTC/USDT
  - ETH/USDT

  # Contre BTC
  - ETH/BTC
  - XRP/BTC

  # Contre USD
  - BTC/USD
  - ETH/USD

  # Stablecoins
  - USDC/USDT
  - DAI/USDT
```

### Optimiser les Paramètres

**Pour plus d'opportunités**:
```yaml
scanner:
  min_profit: 0.2        # Plus bas = plus d'opportunités
  min_confidence: 30     # Plus bas = plus de résultats
  min_volume_24h: 100000 # Plus bas = plus de paires
```

**Pour qualité maximale**:
```yaml
scanner:
  min_profit: 1.0        # Plus haut = meilleure qualité
  min_confidence: 70     # Plus haut = plus sûr
  min_volume_24h: 5000000 # Plus haut = meilleure liquidité
```

---

## FAQ

### ❓ Combien de temps pour voir des résultats?

**Réponse**: 5-10 minutes pour un scan unique. 24-48h pour des patterns fiables.

### ❓ Pourquoi aucune opportunité trouvée?

**Causes possibles**:
1. Paramètres trop stricts (min_profit trop haut)
2. Marché stable (peu de différences de prix)
3. Problèmes de connexion aux exchanges

**Solutions**:
```yaml
# Réduire les critères temporairement
scanner:
  min_profit: 0.2
  min_confidence: 30
  min_volume_24h: 100000
```

### ❓ Les opportunités sont-elles exploitables?

**Important**: Ce sont des opportunités THÉORIQUES.

**Facteurs réels à considérer**:
- ⏱️ **Slippage**: Prix change pendant l'exécution
- 💸 **Fees cachés**: Retrait, réseau, conversion
- ⚡ **Latence**: Temps de transfert entre exchanges
- 🔒 **KYC/Limites**: Restrictions de retrait

**Recommandation**: TOUJOURS vérifier manuellement avant de trader!

### ❓ Comment exécuter une opportunité?

**Étapes recommandées**:

1. **Vérification manuelle**
   ```
   - Ouvrir les exchanges concernés
   - Vérifier les prix en temps réel
   - Calculer TOUS les frais (trading + retrait + réseau)
   - Vérifier les limites de retrait
   ```

2. **Test avec petite somme**
   ```
   - Commencer avec 50-100€
   - Mesurer temps d'exécution
   - Calculer profit réel vs théorique
   - Documenter les résultats
   ```

3. **Automatisation (optionnel)**
   ```python
   # À vos risques! Commencer TRÈS petit
   # Nécessite API keys avec permissions trading
   ```

### ❓ C'est légal?

**Oui**, l'arbitrage est parfaitement légal.

**Mais**:
- 📝 Déclarez vos gains (taxes)
- 🔍 Respectez les KYC des exchanges
- ⚖️ Vérifiez régulations locales

### ❓ Combien peut-on gagner?

**Réaliste**:
- Débutant: 20-50€/mois (avec 1000€ de capital)
- Intermédiaire: 100-300€/mois (avec expérience et capital)
- Avancé: Variable (automatisation, gros capital, HFT)

**Facteurs clés**:
- Capital disponible
- Vitesse d'exécution
- Nombre d'opportunités exploitées
- Fees et coûts réels

### ❓ Comment contribuer / améliorer?

**Idées de contributions**:

1. **Nouvelles stratégies**
   ```python
   # src/strategies/ma_strategie/
   from src.core.scanner_base import ScannerBase

   class MaStrategie(ScannerBase):
       def scan(self):
           # Votre logique ici
   ```

2. **Nouveaux exchanges**
   ```yaml
   # config/config.yaml
   exchanges:
     - mon_exchange  # Si supporté par CCXT
   ```

3. **Améliorations**
   - Système d'alertes (Telegram, Email)
   - API REST pour intégrations
   - Mobile app
   - Machine Learning pour prédictions

---

## 📞 Support

**Problèmes?**
1. Vérifiez les logs: `tail -f logs/scanner.log`
2. Vérifiez la config: `cat config/config.yaml`
3. Testez connexion exchange: `python3.9 -c "import ccxt; print(ccxt.binance().fetch_ticker('BTC/USDT'))"`

**Ressources**:
- CCXT Docs: https://docs.ccxt.com
- Project README: [README.md](README.md)
- Rapport complet: [TRAVAIL_DU_JOUR.md](TRAVAIL_DU_JOUR.md)

---

## 🎯 Prochaines Étapes

1. ✅ Lire ce guide (vous y êtes!)
2. 🔄 Lancer scan continu: `./run_continuous_scan.sh`
3. ⏰ Attendre 24h
4. 📊 Analyser: `python3.9 analyze_opportunities.py`
5. 🧪 Tester 1-2 opportunités manuellement
6. 💰 Scale progressivement si profitable!

**Bon courage et bon trading! 🚀💰**

*(Remember: DYOR - Do Your Own Research)*
