# 🔍 Exploration App

Collection d'explorations et d'analyses de données dans différents domaines.

## 🗂️ Organisation

Chaque exploration est **autonome et complète** dans son propre répertoire :

### 🏢 [Companies Analysis](companies-analysis/)

Analyse d'entreprises françaises via l'API Pappers.

**Objectif** : Détecter automatiquement des insights financiers (croissance, marges, changements de direction)

```bash
cd companies-analysis
python scripts/demo_companies.py
```

👉 **[Voir la documentation](companies-analysis/README.md)**

---

### ₿ [Crypto Arbitrage](crypto-arbitrage/)

Détection d'opportunités d'arbitrage sur les marchés crypto.

**Objectif** : Scanner les différences de prix entre exchanges

```bash
cd crypto-arbitrage
python scripts/main.py
```

👉 **[Voir la documentation](crypto-arbitrage/README.md)**

---

## 📁 Structure du projet

Chaque exploration contient :

```
nom-exploration/
├── scripts/         # Scripts exécutables
├── docs/           # Documentation complète
├── data/           # Données (non versionnées)
├── src/            # Code source
├── config/         # Configuration
├── .env.example    # Template configuration
├── requirements.txt # Dépendances Python
└── README.md       # Documentation de l'exploration
```

## 🚀 Démarrage rapide

### Choisissez votre exploration

**Pour analyser des entreprises** :
```bash
cd companies-analysis
cp .env.example .env
# Ajoutez votre PAPPERS_API_KEY
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/demo_companies.py
```

**Pour l'arbitrage crypto** :
```bash
cd crypto-arbitrage
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/main.py
```

## 📖 Documentation

Chaque exploration a sa propre documentation détaillée dans son dossier `docs/`.

## 🎯 Philosophie

**Une exploration = Un projet complet**

- ✅ Autonome : tout est dans son répertoire
- ✅ Indépendant : pas de dépendances croisées
- ✅ Documenté : docs complètes dans chaque exploration
- ✅ Prêt à l'emploi : scripts + config + exemples

## 🔒 Sécurité

Chaque exploration a son propre `.env` pour les clés API.
Les fichiers `.env` ne sont jamais versionnés.

## 📝 Ajouter une nouvelle exploration

1. Créez un nouveau dossier : `nouvelle-exploration/`
2. Utilisez la structure standard (scripts, docs, src, data, config)
3. Ajoutez un README.md expliquant l'objectif
4. Listez-la dans ce README principal

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE)

## ✨ Crédits

Développé avec l'aide de [Claude Code](https://claude.com/claude-code)

---

**Explorez les données ! 🚀**
