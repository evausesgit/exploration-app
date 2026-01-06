# 🆓 Configuration INPI Data - Données Financières Gratuites

## 📊 Pourquoi INPI Data ?

**INPI Data = API officielle et GRATUITE** pour accéder aux données financières des entreprises françaises.

### Avantages
- ✅ **100% GRATUIT** (vs Pappers payant)
- ✅ **Données officielles** (bilans déposés au greffe)
- ✅ **Légal et sans limite** de requêtes
- ✅ **CA, résultat, bilan complet** disponibles

### Limites
- ⚠️ Retard de 6-18 mois (derniers bilans publiés)
- ⚠️ ~45% des entreprises déclarent leurs comptes confidentiels
- ⚠️ Pas toutes les entreprises (seulement celles qui déposent)

## 🚀 Configuration en 3 étapes

### Étape 1 : Créer un compte INPI

1. Aller sur https://data.inpi.fr
2. Cliquer sur **"S'inscrire"** (en haut à droite)
3. Remplir le formulaire d'inscription
4. Confirmer votre email
5. **C'est gratuit !**

### Étape 2 : Obtenir une clé API

1. Se connecter à https://data.inpi.fr/login
2. Aller dans **"Mon espace"** → **"Mes accès API / SFTP"**
3. Cliquer sur **"Créer un nouvel accès API"**
4. Choisir :
   - Base : **"Registre National des Entreprises (RNE)"**
   - Format : **"JSON"**
5. Copier la **clé API** générée

### Étape 3 : Configurer dans le projet

Ajouter dans votre fichier `.env` :

```bash
# Clé API INPI (gratuite)
INPI_API_KEY=votre_cle_api_ici
```

## 💻 Utilisation

### Enrichir la base de données existante

```bash
cd companies-analysis
source venv/bin/activate
python scripts/enrich_with_inpi.py
```

### Ce que fait le script

1. ✅ Lit les 80 SIREN de la base Pappers
2. ✅ Interroge l'API INPI pour chaque SIREN (GRATUIT)
3. ✅ Récupère CA, résultat, immobilisations, etc.
4. ✅ Stocke dans la table `inpi_financials`
5. ✅ Affiche les statistiques

### Résultat attendu

```
📊 RÉSULTATS DE L'ENRICHISSEMENT
================================================================================

✅ Entreprises enrichies : 45/80 (56.3%)
💰 Avec données financières complètes : 40

📈 Statistiques financières (données INPI) :
   CA moyen : 3,245,000€
   Résultat moyen : 285,000€
   Marge moyenne : 12.5%
   CA min : 500,000€
   CA max : 15,000,000€

💰 Économie réalisée :
   Crédits Pappers économisés : ~45
   Coût INPI : 0€ (GRATUIT)
```

## 🔄 Stratégie hybride recommandée

**Combiner INPI + Pappers pour minimiser les coûts** :

```
1. Scanner avec critères stricts (Pappers - 20 crédits)
   ↓ 20 entreprises prometteuses

2. Enrichir avec INPI Data (GRATUIT)
   ↓ 12 entreprises avec données complètes
   ↓ 8 entreprises sans données INPI

3. Enrichir les 8 manquantes avec Pappers (8 crédits)
   ↓ 20 entreprises complètes

TOTAL : 28 crédits au lieu de 40 (économie de 30%)
```

## 📚 Documentation officielle

- Site INPI Data : https://data.inpi.fr
- Documentation API : https://data.inpi.fr/content/editorial/Acces_API_Entreprises
- Support : contact@inpi.fr

## ❓ FAQ

### Combien de temps pour avoir accès ?
Immédiat après inscription. La clé API est générée instantanément.

### Y a-t-il des limites de requêtes ?
Non, l'API est sans limite (mais respecter un rate limit raisonnable : 2-5 req/sec)

### Les données sont-elles à jour ?
Retard de 6-18 mois selon le dépôt des bilans. Pour des données temps réel, utiliser Pappers.

### Toutes les entreprises sont-elles disponibles ?
~55% des entreprises publient leurs comptes. Les autres déclarent la confidentialité.

## 💡 Cas d'usage

### Enrichissement initial (0€)
```bash
python scripts/enrich_with_inpi.py
```

### Comparaison Pappers vs INPI
```python
from src.data.inpi_client import INPIClient
from src.data.pappers_client import PappersClient

# Comparer les données
inpi = INPIClient()
pappers = PappersClient()

siren = "832363865"
inpi_data = inpi.get_financial_data(siren)
pappers_data = pappers.get_entreprise(siren)

# Choisir la source la plus récente
```

### Validation des données
Utiliser INPI pour **valider** les données Pappers (cross-checking).

---

**🎉 Vous pouvez maintenant enrichir votre base GRATUITEMENT !**
