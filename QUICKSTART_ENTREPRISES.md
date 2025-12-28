# Démarrage rapide - Analyse d'entreprises

## 🚀 En 3 minutes

### 1. Obtenez une clé API Pappers

Créez un compte gratuit : https://www.pappers.fr/api

### 2. Configurez

```bash
# Copiez le fichier d'exemple
cp .env.example .env

# Éditez .env et ajoutez votre clé
# PAPPERS_API_KEY=votre_cle_ici
```

### 3. Installez les dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancez l'analyse

```bash
python analyze_companies.py
```

## ✨ C'est tout !

Le script va :
- Analyser quelques entreprises de démonstration
- Détecter des insights intéressants (croissance, marges, changements)
- Sauvegarder les résultats dans `data/companies.db`

## 📊 Pour analyser vos propres entreprises

Éditez `analyze_companies.py` ligne 37 et ajoutez vos numéros SIREN :

```python
siren_list = [
    "552032534",  # Votre entreprise
    "542065479",  # Une autre
]
```

## 📖 Documentation complète

Consultez `GUIDE_ENTREPRISES.md` pour :
- API Reference complète
- Exemples avancés
- Configuration détaillée
- Export de données

## 🔍 Que fait l'analyseur ?

Il détecte automatiquement :

- ✅ **Croissance forte** : CA en hausse significative
- ✅ **Marges élevées** : Bonne rentabilité
- ✅ **Nouveaux dirigeants** : Changements récents

## 💡 Besoin d'aide ?

Consultez le guide complet : `GUIDE_ENTREPRISES.md`
