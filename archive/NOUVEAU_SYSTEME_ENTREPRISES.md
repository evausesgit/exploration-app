# 🎉 Nouveau système d'analyse d'entreprises installé !

## ✅ Ce qui a été fait

Votre application a été transformée pour analyser les données d'entreprises françaises via l'API Pappers :

### 1. Nouveaux modules créés

- **`src/data/pappers_client.py`** : Client pour l'API Pappers
  - Récupération de données d'entreprises
  - Données financières (CA, résultats, bilans)
  - Informations sur les dirigeants
  - Bénéficiaires effectifs
  - Recherche d'entreprises

- **`src/strategies/companies/company_analyzer.py`** : Analyseur intelligent
  - Détecte la croissance financière forte
  - Identifie les marges élevées
  - Repère les changements de direction récents
  - Calcule des scores de confiance

### 2. Scripts d'utilisation

- **`analyze_companies.py`** : Script principal prêt à l'emploi
  - Analyse de listes de SIREN
  - Recherche interactive
  - Sauvegarde automatique
  - Statistiques

### 3. Documentation complète

- **`QUICKSTART_ENTREPRISES.md`** : Démarrage en 3 minutes
- **`GUIDE_ENTREPRISES.md`** : Documentation complète avec exemples
- **`README_PRINCIPAL.md`** : Vue d'ensemble du projet

### 4. Infrastructure

- Environnement virtuel créé (`venv/`)
- Dépendances installées
- Configuration `.env` mise à jour
- Types d'opportunités étendus

## 🚀 Comment utiliser

### 1. Obtenez une clé API Pappers

Créez un compte gratuit : https://www.pappers.fr/api

Le plan gratuit offre **500 requêtes/mois** - largement suffisant pour commencer !

### 2. Configurez votre clé API

Éditez le fichier `.env` (créez-le depuis `.env.example` si nécessaire) :

```bash
PAPPERS_API_KEY=votre_cle_api_ici
```

### 3. Activez l'environnement virtuel

```bash
source venv/bin/activate
```

### 4. Lancez l'analyse

```bash
python analyze_companies.py
```

## 📊 Types d'insights détectés

### Croissance financière (FINANCIAL_GROWTH)
- Entreprises avec forte hausse du CA
- Critère par défaut : +10% minimum
- Exemple : "Croissance de 25.3% du CA"

### Marges élevées (HIGH_MARGIN)
- Entreprises très rentables
- Critère par défaut : Marge nette ≥ 5%
- Exemple : "Marge nette de 12.5%"

### Changements de direction (MANAGEMENT_CHANGE)
- Nouveaux dirigeants (< 6 mois)
- Particulièrement les présidents
- Exemple : "Nouveau Président: Jean Dupont"

## 🎯 Exemples rapides

### Analyser vos propres entreprises

Éditez `analyze_companies.py` ligne 37 :

```python
siren_list = [
    "123456789",  # Votre entreprise 1
    "987654321",  # Votre entreprise 2
]
```

### Rechercher et analyser

```python
from src.strategies.companies import CompanyAnalyzer

analyzer = CompanyAnalyzer({})
insights = analyzer.search_and_analyze("carrefour", max_companies=5)

for insight in insights:
    print(f"{insight.data['denomination']} : {insight.metadata['message']}")
```

### Récupérer des données via API

```python
from src.data.pappers_client import PappersClient

client = PappersClient()

# Recherche
companies = client.recherche("restaurants", departement="75")

# Données d'une entreprise
data = client.get_entreprise("552032534")
print(data['nom_entreprise'])

# Finances uniquement
finances = client.get_finances("552032534")
```

## 📁 Où sont stockées les données ?

- **Base de données** : `data/companies.db` (SQLite)
- **Logs** : `logs/companies_*.log`
- **Configuration** : `.env`

## 🔧 Personnalisation

### Modifier les critères d'analyse

Dans `analyze_companies.py` ou votre code :

```python
config = {
    'min_ca': 500000,          # CA minimum : 500k€
    'min_growth_rate': 20,     # Croissance minimum : 20%
    'min_margin': 10,          # Marge minimum : 10%
    'min_confidence': 70       # Confiance minimum : 70/100
}
```

### Filtrer par secteur

```python
# Recherche avec filtres
companies = client.recherche(
    "restaurant",
    departement="75",      # Paris
    code_naf="5610A",      # Code NAF spécifique
    max_results=20
)
```

## 💡 Conseils d'utilisation

### Rate limiting
- L'API limite à ~5 requêtes/seconde
- Le client gère automatiquement l'attente
- Pour de gros volumes, faites des pauses

### Quotas
- **Plan gratuit** : 500 req/mois
- Une analyse complète = 1 requête
- Surveillez sur pappers.fr

### Données
- Toutes les entreprises n'ont pas de données financières publiques
- Les micro-entreprises ont rarement des comptes publiés
- Vérifiez toujours les données retournées

## 🔄 Mode hybride Crypto + Entreprises

Votre application supporte maintenant **les deux modes** :

### Pour le crypto (ancien système)
```bash
python main.py
```

### Pour les entreprises (nouveau)
```bash
python analyze_companies.py
```

### Ou les deux dans le même code
```python
# Crypto
from src.strategies.arbitrage import CryptoArbitrageScanner
crypto_scanner = CryptoArbitrageScanner(config)

# Entreprises
from src.strategies.companies import CompanyAnalyzer
company_analyzer = CompanyAnalyzer(config)

# Stockage séparé
storage_crypto = OpportunityStorage("data/crypto.db")
storage_companies = OpportunityStorage("data/companies.db")
```

## 📖 Documentation

- **Démarrage rapide** : `QUICKSTART_ENTREPRISES.md`
- **Guide complet** : `GUIDE_ENTREPRISES.md`
- **API Reference** : Dans `GUIDE_ENTREPRISES.md`
- **Vue d'ensemble** : `README_PRINCIPAL.md`

## 🐛 Problèmes courants

### "Clé API invalide"
- Vérifiez que votre clé est dans `.env`
- Vérifiez qu'elle est active sur pappers.fr

### "ModuleNotFoundError"
- Activez l'environnement virtuel : `source venv/bin/activate`
- Installez les dépendances : `pip install -r requirements.txt`

### "Aucune donnée financière"
- Normal pour certaines entreprises
- Micro-entreprises souvent sans comptes publics
- Essayez des grandes entreprises connues

## 🎯 Prochaines étapes suggérées

1. **Testez avec le script de base**
   ```bash
   python analyze_companies.py
   ```

2. **Analysez vos propres entreprises**
   - Récupérez les numéros SIREN
   - Ajoutez-les dans le script

3. **Explorez les données**
   - Consultez `data/companies.db` avec un viewer SQLite
   - Analysez les insights détectés

4. **Personnalisez**
   - Ajustez les critères d'analyse
   - Créez vos propres détecteurs
   - Exportez les données (CSV, Excel, etc.)

5. **Automatisez**
   - Créez un cron pour scanner régulièrement
   - Envoyez des alertes email
   - Intégrez à vos outils

## 🔒 Rappels de sécurité

- ✅ Le fichier `.env` est dans `.gitignore`
- ✅ Ne commitez jamais vos clés API
- ✅ Utilisez des clés en lecture seule quand possible
- ✅ Surveillez votre consommation API

## 🤝 Besoin d'aide ?

- Documentation : Voir les fichiers `GUIDE_*.md`
- API Pappers : https://www.pappers.fr/api/documentation
- Issues : (votre repo GitHub)

---

**Bonne exploration des données d'entreprises ! 🚀📊**
