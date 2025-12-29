# Application Web - Exploration App

Interface web pour visualiser les opportunités d'automatisation IA détectées.

## 🚀 Déploiement sur Vercel

### 1. Connecter le repository GitHub à Vercel

1. Aller sur [vercel.com](https://vercel.com)
2. Importer le repository GitHub
3. Vercel détectera automatiquement la configuration dans `vercel.json`

### 2. Configuration automatique

Le fichier `vercel.json` à la racine configure :
- Build command: `cd web && npm install && npm run build`
- Output directory: `web/out`
- Region: Paris (cdg1)

### 3. Déploiement automatique

Chaque push sur `main` déploiera automatiquement sur Vercel.

## 📊 Mise à jour des données

### Automatique
Quand vous lancez un scan avec `explore_ai_automation.py`, les données sont automatiquement synchronisées vers `web/public/data/`.

### Manuel
```bash
python companies-analysis/scripts/sync_to_web.py
```

Puis commit et push :
```bash
git add web/public/data/automation_opportunities.json
git commit -m "update: sync latest scan results"
git push
```

Vercel redéploiera automatiquement avec les nouvelles données.

## 🛠️ Développement local

```bash
cd web
npm install
npm run dev
```

Ouvrir http://localhost:3000

## 📁 Structure

```
web/
├── pages/
│   ├── _app.tsx        # Configuration Next.js
│   └── index.tsx       # Page principale
├── public/
│   └── data/
│       └── automation_opportunities.json  # Données
├── styles/
│   └── globals.css     # Styles Tailwind
├── package.json        # Dépendances
├── next.config.js      # Configuration Next.js
└── vercel.json         # Configuration Vercel (à la racine)
```

## 🎨 Technologies

- **Next.js 14** : Framework React
- **TypeScript** : Typage statique
- **Tailwind CSS** : Styling
- **Vercel** : Hébergement et déploiement
