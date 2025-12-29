# ⚙️ Configuration Dynamique du Scoring

## 🎯 Nouvelle Fonctionnalité

Vous pouvez maintenant **modifier les critères de scoring directement depuis le dashboard** et voir les résultats **recalculés en temps réel** sans avoir à relancer de scan !

## 📊 Les 4 Critères de Scoring

### 1️⃣ Ratio CA/Effectif (40 points max par défaut)

Mesure la productivité par salarié.

**Paliers par défaut** :
- ≥ 500k€ → 40 points
- ≥ 300k€ → 35 points
- ≥ 200k€ → 30 points
- ≥ 150k€ → 25 points
- ≥ 100k€ → 20 points
- < 100k€ → 10 points

### 2️⃣ Secteur d'Activité (30 points max par défaut)

Bonus si l'entreprise est dans un secteur à fort levier IA.

**Secteurs prioritaires** :
- Conseil, consulting, audit
- Marketing digital, publicité, SEO
- SaaS, logiciel, plateforme
- Formation, coaching, e-learning
- Courtage, intermédiation
- Services RH, recrutement
- Services financiers, comptabilité
- Services juridiques, legal

**Attribution** :
- 3+ secteurs correspondants → 30 points
- 2 secteurs → 25 points
- 1 secteur → 20 points
- 0 secteur → 10 points

### 3️⃣ Rentabilité - Marge (15 points max par défaut)

Marge bénéficiaire (résultat/CA).

**Paliers par défaut** :
- ≥ 30% → 15 points
- ≥ 20% → 12 points
- ≥ 10% → 9 points
- ≥ 5% → 6 points
- < 5% → 3 points

### 4️⃣ Faibles Actifs Physiques (15 points max par défaut)

Ratio immobilisations/CA. Plus c'est bas, plus l'entreprise est "légère".

**Paliers par défaut** :
- 0% du CA → 15 points
- < 10% du CA → 12 points
- < 30% du CA → 8 points
- ≥ 30% du CA → 3 points

## 🔧 Comment Utiliser la Configuration

### Sur le Dashboard Web

1. **Ouvrir la configuration**
   - Cliquer sur le bouton "Afficher" dans la section "⚙️ Configuration du Scoring"

2. **Activer/Désactiver des critères**
   - Cocher/décocher la case à côté de chaque critère
   - Un critère désactivé ne contribuera pas au score

3. **Ajuster les poids**
   - Utiliser les sliders pour modifier le nombre de points maximum de chaque critère
   - Exemple : Si vous pensez que le CA/employé est moins important, baissez de 40 à 20 points

4. **Appliquer les changements**
   - Cliquer sur "Appliquer et Recalculer"
   - Les scores sont recalculés instantanément
   - Le classement est automatiquement réorganisé
   - Les statistiques se mettent à jour

5. **Réinitialiser**
   - Cliquer sur "Réinitialiser" pour revenir à la configuration par défaut

### Exemples d'Utilisation

#### Scénario 1 : Vous privilégiez la rentabilité

```
1. Augmenter le poids "Rentabilité" de 15 à 30 points
2. Réduire "CA/Effectif" de 40 à 25 points
3. Cliquer sur "Appliquer et Recalculer"
```

Résultat : Les entreprises avec de fortes marges monteront dans le classement.

#### Scénario 2 : Vous ne voulez que des entreprises ultra-légères

```
1. Désactiver "Secteur" et "Rentabilité"
2. Augmenter "Faibles Actifs" à 50 points
3. Garder "CA/Effectif" à 40 points
4. Cliquer sur "Appliquer et Recalculer"
```

Résultat : Seuls les critères CA/employé et actifs légers comptent.

#### Scénario 3 : Focus exclusif sur le secteur

```
1. Augmenter "Secteur" à 50 points
2. Réduire les autres critères à 10 points chacun
3. Cliquer sur "Appliquer et Recalculer"
```

Résultat : Les entreprises dans les secteurs prioritaires domineront.

## 💾 Sauvegarde de Configuration

**Important** : Les modifications de configuration sont **locales** dans votre navigateur. Si vous rechargez la page, vous revenez à la configuration par défaut.

Si vous trouvez une configuration qui vous convient et voulez la garder par défaut :

1. Notez les valeurs que vous avez définies
2. Modifiez le fichier Python `src/strategies/ai_automation_scanner.py`
3. Changez les valeurs dans la méthode `_calculate_automation_score`
4. Relancez un scan
5. Les nouvelles valeurs par défaut seront utilisées

## 🔄 Workflow Complet

### Pour tester rapidement différentes configurations

1. **Une seule fois** : Lancer un scan pour avoir les données
   ```bash
   python scripts/explore_ai_automation.py --secteurs conseil marketing_digital
   ```

2. **Ensuite** : Tester autant de configurations que vous voulez dans le dashboard
   - Modifier les poids
   - Appliquer
   - Observer les changements
   - Itérer jusqu'à satisfaction

3. **Aucun nouveau scan nécessaire** ! Tout est recalculé côté client.

### Pour déployer une configuration personnalisée

1. Modifier les valeurs par défaut dans `explore_ai_automation.py`
2. Lancer un nouveau scan
3. Commit et push
4. Vercel déploiera avec votre nouvelle config par défaut

## 📝 Notes Techniques

- Le calcul côté client reproduit **exactement** l'algorithme Python
- Tous les secteurs prioritaires sont identiques
- Les paliers sont configurables mais fixés au moment du scan
- Pour modifier les paliers eux-mêmes (pas seulement les poids), il faut modifier le code Python

## 🎬 Démo Rapide

1. Allez sur https://exploration-app.vercel.app/
2. Cliquez sur "Afficher" dans la section Configuration
3. Désactivez "Secteur d'Activité"
4. Cliquez sur "Appliquer et Recalculer"
5. Observez comment le classement change instantanément !

---

**Astuce** : Partagez différentes configurations avec votre associé en lui indiquant quels curseurs ajuster pour voir ce qui vous semble le plus pertinent.
