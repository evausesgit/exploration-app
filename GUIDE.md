# Guide Complet - Crypto Opportunity Scanner

## 🎯 Objectif

Ce projet vous permet de **détecter automatiquement des opportunités d'arbitrage** entre exchanges crypto et de **les visualiser** dans un dashboard interactif.

## 🚀 Démarrage Rapide

### 1. Installation

```bash
# Installer les dépendances
pip install -r requirements.txt
```

### 2. Premier Scan

```bash
# Lancer un scan unique
python main.py --scan
```

### 3. Dashboard de Visualisation

```bash
# Lancer le dashboard web
python main.py --dashboard
```

Le dashboard s'ouvrira automatiquement dans votre navigateur à l'adresse: `http://localhost:8501`

## 📊 Modes d'Utilisation

### Mode 1: Scan Unique

Pour tester et voir les opportunités actuelles :

```bash
python main.py --scan
```

**Quand l'utiliser:** Pour vérifier rapidement s'il y a des opportunités intéressantes en ce moment.

### Mode 2: Scan Continu (Watch Mode)

Pour surveiller en continu et accumuler des données :

```bash
python main.py --watch
```

**Quand l'utiliser:**
- Pour accumuler des données historiques
- Pour identifier des patterns récurrents
- Laissez tourner pendant quelques heures/jours

**Astuce:** Lancez-le en arrière-plan avec `nohup` ou dans un `screen`/`tmux`

### Mode 3: Dashboard

Pour analyser visuellement les opportunités :

```bash
python main.py --dashboard
```

**Fonctionnalités du Dashboard:**
- 🔍 **Scan en Direct:** Lancer des scans manuels
- 📊 **Opportunités Récentes:** Voir l'historique avec filtres
- 📈 **Analyses:** Graphiques de tendances, top symboles, meilleurs exchanges
- ⚙️ **Paramètres:** Configurer le scanner

## 🎓 Comment Apprendre et Gagner de l'Argent

### Phase 1: APPRENDRE (1-2 semaines)

**Objectif:** Comprendre où est l'argent, sans risque

1. **Lancer le scan en continu pendant 3-7 jours**
   ```bash
   python main.py --watch
   ```

2. **Observer dans le dashboard:**
   - Quels symboles ont le plus d'opportunités?
   - Quelles paires d'exchanges reviennent souvent?
   - À quels moments de la journée?
   - Quel est le profit moyen réaliste?

3. **Questions à se poser:**
   - Les opportunités > 1% sont-elles fréquentes?
   - Combien de temps durent-elles?
   - Y a-t-il des patterns récurrents?

**Résultat attendu:** Vous SAVEZ maintenant où sont les vraies opportunités.

### Phase 2: COMPRENDRE (2-4 semaines)

**Objectif:** Identifier ce qui est VRAIMENT exploitable

1. **Affinez la configuration** (`config/config.yaml`)
   - Réduisez la liste de symboles aux plus profitables
   - Ajustez `min_profit` selon vos observations
   - Testez différents exchanges

2. **Analysez la liquidité**
   - Les opportunités avec gros volumes sont plus sûres
   - Vérifiez si vous pouvez réellement exécuter (orderbook depth)

3. **Calculez les coûts réels:**
   - Frais de trading: 0.1-0.2% par exchange
   - Frais de retrait: variable (Bitcoin ~$2-10, stablecoins ~$1-5)
   - Slippage: ~0.1-0.3% sur gros ordres

**Règle d'or:** Une opportunité n'est réelle que si profit > tous les coûts + 0.2% de marge

### Phase 3: TESTER (avec PETIT capital)

**Objectif:** Valider en réel avec risque minimal

1. **Commencez avec 100-200€**
   - Créez des comptes sur les exchanges identifiés
   - Testez MANUELLEMENT l'arbitrage sur 1-2 opportunités
   - Notez le temps d'exécution, les difficultés

2. **Checklist avant d'exécuter:**
   - [ ] Profit net > 0.5% (après TOUS les frais)
   - [ ] Volume suffisant (> 10k$ sur les deux exchanges)
   - [ ] Vous avez des fonds sur l'exchange d'achat
   - [ ] Retrait rapide possible (vérifiez délais)

3. **Mesurez TOUT:**
   - Temps total de l'opération
   - Profit réel vs prévu
   - Problèmes rencontrés (KYC, limites, délais)

### Phase 4: AUTOMATISER (si Phase 3 est profitable)

**Objectif:** Scaler ce qui marche

1. **Ajoutez l'auto-exécution** (à coder)
   - Connexion aux exchanges via API
   - Ordres automatiques
   - Gestion des erreurs

2. **Gestion du risque:**
   - Max 10-20% du capital par trade
   - Stop-loss si ça bloque trop longtemps
   - Diversifier sur plusieurs paires

## ⚠️ Pièges à Éviter

### 1. Faux Signaux

**Problème:** Le scanner détecte 2% de profit mais c'est inexploitable

**Causes:**
- Manque de liquidité (orderbook trop fin)
- Délai de retrait trop long (le prix change)
- Exchange avec problèmes techniques

**Solution:** Toujours vérifier manuellement avant d'exécuter

### 2. Frais Cachés

**Problème:** Profit théorique vs réel très différent

**Frais souvent oubliés:**
- Withdrawal fees (variable par crypto)
- Network fees (gas pour ETH, etc.)
- Spread bid-ask
- Slippage sur gros ordres

**Solution:** Inclure TOUS les frais dans le calcul (activez `include_withdrawal_fee: true`)

### 3. Timing

**Problème:** L'opportunité disparaît avant exécution

**Réalité:** Les vrais arbitrages durent quelques secondes à minutes

**Solutions:**
- Avoir des fonds PRÉ-POSITIONNÉS sur les exchanges
- Exécuter très vite (automatisation)
- Cibler les inefficiences qui durent (exchanges régionaux)

### 4. Régulation et Limites

**Problème:** Bloqué par KYC, limites de retrait

**Avant de commencer:**
- Vérifiez les limites de retrait quotidiennes
- Complétez le KYC avancé si nécessaire
- Testez un retrait avant d'engager gros capital

## 🎯 Stratégie Réaliste pour Débutant

### Objectif Réaliste: 2-5% par mois

**Plan d'action:**

1. **Semaine 1-2:** Observer uniquement (scan continu)
2. **Semaine 3-4:** Analyser les données, identifier 2-3 paires profitables
3. **Semaine 5:** Premier test avec 100€
4. **Semaine 6-8:** Affiner, tester différentes approches
5. **Mois 2+:** Scaler progressivement si profitable

### Capital Recommandé par Phase

- **Apprentissage:** 0€ (simulation uniquement)
- **Test:** 100-200€
- **Validation:** 500-1000€
- **Scaling:** 2000-5000€
- **Sérieux:** 10000€+

**Règle:** Ne jamais risquer plus que ce que vous pouvez perdre entièrement

## 📈 Optimisations Futures

### Stratégies à Ajouter

Le projet est modulaire. Vous pouvez ajouter:

1. **Triangular Arbitrage:** BTC → ETH → USDT → BTC
2. **Funding Rate Arbitrage:** Long spot + Short perpetual
3. **DEX vs CEX:** Uniswap vs Binance
4. **Mean Reversion:** Acheter les dips, vendre les pics
5. **Liquidation Sniping:** Détecter les cascades de liquidations

### Données Supplémentaires

- Order flow (gros ordres)
- Whale movements (on-chain data)
- Social sentiment (Twitter, Reddit)
- News events

## 💡 Conseils de Pro

1. **Commencez PETIT:** 99% des débutants perdent en commençant trop gros
2. **Loggez TOUT:** Chaque trade, chaque profit/perte
3. **Restez humble:** Si c'était facile, tout le monde serait riche
4. **Automatisez progressivement:** D'abord manuel, puis semi-auto, puis full auto
5. **Diversifiez:** Ne misez pas tout sur une stratégie
6. **Éduquez-vous:** Lisez, apprenez, testez

## 🛠️ Personnalisation

### Ajouter Votre Propre Stratégie

1. Créez un nouveau fichier dans `src/strategies/votre_strategie/`
2. Héritez de `ScannerBase`
3. Implémentez `scan()` qui retourne des `Opportunity`
4. Enregistrez dans `main.py`

Exemple:
```python
from src.core.scanner_base import ScannerBase
from src.core.opportunity import Opportunity, OpportunityType

class MaStrategieScanner(ScannerBase):
    def get_name(self) -> str:
        return "Ma Stratégie"

    def scan(self) -> List[Opportunity]:
        # Votre logique ici
        opportunities = []
        # ...
        return opportunities
```

### Modifier les Paramètres

Éditez `config/config.yaml`:

```yaml
scanner:
  min_profit: 0.3  # Moins strict
  min_confidence: 40
  scan_interval: 30  # Scan toutes les 30s
```

## 📞 Support & Contribution

- **Issues:** Signalez bugs et suggestions
- **Améliorations:** Les pull requests sont bienvenues
- **Questions:** Documentez vos learnings pour aider les autres

## ⚖️ Disclaimer

**IMPORTANT:**

- Ce projet est éducatif
- Le trading comporte des risques
- Pas de garantie de profit
- Testez avec de petites sommes
- Respectez les lois et régulations locales
- Les exchanges peuvent bannir les bots (vérifiez ToS)

**Vous êtes seul responsable de vos décisions de trading.**

---

Bonne chance et tradez intelligemment ! 🚀
