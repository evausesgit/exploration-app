# 🚀 Quick Start - 5 Minutes

## Installation

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. (Optionnel) Créer les dossiers nécessaires
mkdir -p data logs
```

## Premier Test

```bash
# Lance un scan unique pour voir des opportunités
python main.py --scan
```

Vous devriez voir quelque chose comme :
```
Found 3 opportunities
Top 5 Opportunities:
1. BTC/USDT: 0.75% (binance → kraken)
2. ETH/USDT: 0.52% (coinbase → binance)
3. SOL/USDT: 0.48% (kraken → coinbase)
```

## Dashboard Visuel

```bash
# Lance le dashboard web
python main.py --dashboard
```

Ouvrez votre navigateur à: **http://localhost:8501**

### Dans le Dashboard:

1. **Tab "Scan en Direct"** → Cliquez sur "Lancer Scan"
2. **Tab "Opportunités Récentes"** → Voir l'historique
3. **Tab "Analyses"** → Graphiques et statistiques

## Scan Continu (Accumuler des Données)

```bash
# Scanne toutes les minutes et enregistre les données
python main.py --watch
```

Laissez tourner quelques heures pour accumuler des données, puis lancez le dashboard pour analyser.

## Personnalisation

Éditez `config/config.yaml` :

```yaml
# Ajoutez vos symboles préférés
symbols:
  - BTC/USDT
  - ETH/USDT
  - VOTRE/CRYPTO

# Ajustez les critères
scanner:
  min_profit: 0.5  # Profit minimum en %
  min_confidence: 50
```

## Prochaines Étapes

1. Lisez **GUIDE.md** pour comprendre comment gagner de l'argent
2. Laissez le scan tourner 24-48h
3. Analysez les patterns dans le dashboard
4. Testez manuellement avec un petit montant

## Problèmes Courants

### Erreur: "No module named 'ccxt'"
```bash
pip install ccxt
```

### Erreur: "Rate limit exceeded"
→ Normal, le scanner respecte les limites. Attendez quelques secondes.

### Aucune opportunité trouvée
→ C'est normal ! Les vraies opportunités sont rares (c'est pour ça qu'elles sont profitables).
Essayez:
- Réduire `min_profit` à 0.3%
- Lancer le scan plusieurs fois
- Utiliser le mode `--watch` pour surveiller en continu

## Support

Questions? Consultez:
- **README.md** : Vue d'ensemble du projet
- **GUIDE.md** : Guide complet pour gagner de l'argent
- **config/config.example.yaml** : Toutes les options disponibles

---

**Conseil Pro:** Commencez par observer (pas de trading) pendant 1-2 semaines. Comprenez d'abord où est l'argent ! 💡
