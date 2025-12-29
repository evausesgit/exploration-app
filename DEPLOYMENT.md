# 🚀 Guide de Déploiement Vercel

## Étapes pour déployer sur https://exploration-app.vercel.app/

### 1️⃣ Connecter GitHub à Vercel

1. Aller sur [vercel.com](https://vercel.com)
2. Se connecter avec GitHub
3. Cliquer sur "Add New..." → "Project"
4. Importer le repository `evausesgit/exploration-app`

### 2️⃣ Configuration du projet

Vercel détectera automatiquement la configuration depuis `vercel.json` :

- **Framework Preset**: Other
- **Build Command**: `cd web && npm install && npm run build`
- **Output Directory**: `web/out`
- **Install Command**: `cd web && npm install`

Laisser les autres paramètres par défaut et cliquer sur **Deploy**.

### 3️⃣ Configuration du domaine (optionnel)

Si vous voulez utiliser `exploration-app.vercel.app` :

1. Aller dans Settings → Domains
2. Le domaine `*.vercel.app` est automatiquement disponible
3. Votre site sera accessible sur `exploration-app.vercel.app`

### 4️⃣ Déploiement automatique

Une fois configuré, **chaque push sur `main`** déploiera automatiquement :

```bash
# 1. Lancer un scan
cd companies-analysis
./venv/bin/python scripts/explore_ai_automation.py --secteurs conseil marketing_digital

# 2. Les données sont automatiquement synchronisées vers web/public/data/

# 3. Commit et push
git add web/public/data/automation_opportunities.json
git commit -m "update: sync latest scan results"
git push

# 4. Vercel déploie automatiquement (1-2 minutes)
```

### 5️⃣ Vérifier le déploiement

1. Aller sur le dashboard Vercel
2. Voir le déploiement en cours
3. Une fois terminé, cliquer sur "Visit" pour voir le site

### 🔄 Workflow complet

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Lancer un scan Python                                     │
│    python scripts/explore_ai_automation.py                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├── Données sauvegardées dans data/
                      │
                      └── Auto-sync vers web/public/data/
                              │
┌─────────────────────┴───────────────────────────────────────┐
│ 2. Commit et push                                           │
│    git add web/public/data/automation_opportunities.json   │
│    git commit -m "update scan"                             │
│    git push                                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│ 3. Vercel détecte le push et déploie automatiquement       │
│    Build → Deploy → Live sur exploration-app.vercel.app    │
└─────────────────────────────────────────────────────────────┘
```

### 📊 Partager avec votre associé

Une fois déployé, votre associé peut simplement aller sur :

👉 **https://exploration-app.vercel.app/**

Aucune installation requise, aucun accès au code nécessaire.
Le site affiche automatiquement les derniers résultats de scan.

### ⚙️ Variables d'environnement (si nécessaire)

Si vous ajoutez des fonctionnalités nécessitant des secrets :

1. Aller dans Settings → Environment Variables
2. Ajouter les variables (ex: API keys)
3. Redéployer

### 🐛 Dépannage

**Le build échoue ?**
- Vérifier les logs dans le dashboard Vercel
- S'assurer que `web/public/data/automation_opportunities.json` existe

**Les données ne se mettent pas à jour ?**
- Vérifier que le fichier JSON a bien été commité
- Vérifier que le push a déclenché un déploiement

**Erreur 404 ?**
- Le chemin doit être `/` pas `/index.html`
- Next.js gère le routing automatiquement

### 📝 Notes

- Le site est **statique** (génération à la build)
- Les données sont **figées au moment du déploiement**
- Pour mettre à jour : nouveau scan → commit → push
- Temps de build : ~1-2 minutes
- Gratuit sur le plan Hobby de Vercel
