# 👋 Bienvenue dans votre application d'exploration !

## 🎯 Par où commencer ?

Votre application peut maintenant analyser **deux types de données** :

### 🏢 Analyse d'entreprises (NOUVEAU !)

Analysez les entreprises françaises via l'API Pappers.

**→ Lisez :** [`NOUVEAU_SYSTEME_ENTREPRISES.md`](NOUVEAU_SYSTEME_ENTREPRISES.md)

**Démarrage rapide :**
1. Obtenez une clé API gratuite sur https://www.pappers.fr/api
2. Ajoutez-la dans `.env` : `PAPPERS_API_KEY=votre_cle`
3. Activez l'environnement : `source venv/bin/activate`
4. Testez la connexion : `python test_pappers_connection.py`
5. Lancez l'analyse : `python analyze_companies.py`

**Documentation :**
- 🚀 [`QUICKSTART_ENTREPRISES.md`](QUICKSTART_ENTREPRISES.md) - Démarrage en 3 minutes
- 📖 [`GUIDE_ENTREPRISES.md`](GUIDE_ENTREPRISES.md) - Guide complet avec exemples

---

### ₿ Analyse crypto (Original)

Détectez les opportunités d'arbitrage sur les marchés crypto.

**→ Lisez :** [`README.md`](README.md) ou [`README_UTILISATION.md`](README_UTILISATION.md)

**Démarrage rapide :**
1. Activez l'environnement : `source venv/bin/activate`
2. Lancez : `python main.py`

---

## 📚 Index des fichiers

### Fichiers importants pour COMMENCER

| Fichier | Description |
|---------|-------------|
| **`NOUVEAU_SYSTEME_ENTREPRISES.md`** | ⭐ Tout sur le nouveau système entreprises |
| **`QUICKSTART_ENTREPRISES.md`** | Démarrage rapide entreprises (3 min) |
| **`test_pappers_connection.py`** | Tester votre clé API Pappers |
| **`analyze_companies.py`** | Script principal analyse entreprises |
| `.env.example` | Configuration (copiez vers `.env`) |

### Documentation détaillée

| Fichier | Description |
|---------|-------------|
| **`GUIDE_ENTREPRISES.md`** | Guide complet analyse entreprises |
| **`README_PRINCIPAL.md`** | Vue d'ensemble du projet complet |
| `README.md` | Guide original (crypto) |
| `README_UTILISATION.md` | Utilisation détaillée (crypto) |

### Scripts d'exécution

| Fichier | Description |
|---------|-------------|
| `analyze_companies.py` | 🏢 Analyse d'entreprises |
| `main.py` | ₿ Analyse crypto |
| `test_pappers_connection.py` | Test connexion API Pappers |

### Code source

| Dossier/Fichier | Description |
|-----------------|-------------|
| `src/data/pappers_client.py` | Client API Pappers |
| `src/strategies/companies/` | Analyseur d'entreprises |
| `src/strategies/arbitrage/` | Stratégies crypto |
| `src/core/` | Classes de base |

## 🎯 Workflow recommandé

### Pour l'analyse d'entreprises

```bash
# 1. Activez l'environnement virtuel
source venv/bin/activate

# 2. Testez votre clé API (une fois)
python test_pappers_connection.py

# 3. Lancez l'analyse
python analyze_companies.py

# 4. Consultez les résultats
# Base de données : data/companies.db
# Logs : logs/companies_*.log
```

### Pour l'analyse crypto

```bash
# 1. Activez l'environnement virtuel
source venv/bin/activate

# 2. Lancez le scanner
python main.py
```

## ⚙️ Configuration initiale

### 1. Créez votre fichier `.env`

```bash
cp .env.example .env
```

### 2. Ajoutez vos clés API

Éditez `.env` :

```env
# Pour les entreprises
PAPPERS_API_KEY=votre_cle_pappers

# Pour le crypto (optionnel)
BINANCE_API_KEY=votre_cle_binance
BINANCE_API_SECRET=votre_secret_binance
```

### 3. Activez l'environnement virtuel

```bash
source venv/bin/activate
```

## 🆘 Besoin d'aide ?

### Problème : "ModuleNotFoundError"
**Solution :** Activez l'environnement virtuel
```bash
source venv/bin/activate
```

### Problème : "Clé API invalide"
**Solution :** Vérifiez votre `.env`
1. Le fichier `.env` existe (copié depuis `.env.example`)
2. La clé `PAPPERS_API_KEY` est correcte
3. La clé est active sur pappers.fr

### Problème : "Aucune donnée financière"
**Solution :** Normal pour certaines entreprises
- Micro-entreprises sans comptes publics
- Entreprises récentes
- Testez avec des grandes entreprises connues (ex: SIREN 552032534)

## 📖 Ressources

- **API Pappers :** https://www.pappers.fr/api/documentation
- **Plan gratuit :** 500 requêtes/mois
- **Support Pappers :** contact via pappers.fr

## 🎉 Prêt à commencer ?

### Option 1 : Analyse d'entreprises (Recommandé pour débuter)

```bash
source venv/bin/activate
python test_pappers_connection.py
python analyze_companies.py
```

### Option 2 : Analyse crypto

```bash
source venv/bin/activate
python main.py
```

---

**Bonne exploration ! 🚀**
