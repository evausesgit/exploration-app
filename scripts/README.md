# 🐍 Scripts

Scripts Python exécutables du projet.

## 🏢 Analyse d'entreprises (Pappers API)

### `demo_companies.py` ⭐ **Recommandé**
Démonstration complète sans interaction utilisateur.

**Usage** :
```bash
source venv/bin/activate
python scripts/demo_companies.py
```

**Ce que fait le script** :
- Analyse 3 grandes entreprises françaises
- Recherche "carrefour" et analyse les résultats
- Récupère des données via l'API Pappers
- Affiche les insights détectés
- Sauvegarde dans la base de données
- Affiche les statistiques

### `analyze_companies.py`
Script interactif d'analyse d'entreprises.

**Usage** :
```bash
source venv/bin/activate
python scripts/analyze_companies.py
```

Permet la saisie interactive pour rechercher des entreprises.

### `test_pappers_connection.py`
Test de connexion à l'API Pappers.

**Usage** :
```bash
source venv/bin/activate
python scripts/test_pappers_connection.py
```

Vérifie que votre clé API fonctionne correctement.

## ₿ Analyse crypto (Legacy)

### `main.py`
Scanner d'arbitrage crypto (ancien système).

### `analyze_opportunities.py`
Analyse des opportunités crypto sauvegardées.

### `run_continuous_scan.sh`
Lance le scanner crypto en continu en arrière-plan.

**Usage** :
```bash
# Depuis la racine du projet
./scripts/run_continuous_scan.sh
```

## 🚀 Démarrage rapide

```bash
# 1. Activez l'environnement
source venv/bin/activate

# 2. Testez la connexion
python scripts/test_pappers_connection.py

# 3. Lancez la démo
python scripts/demo_companies.py
```

## 📖 Documentation

Voir [docs/](../docs/) pour la documentation complète.
