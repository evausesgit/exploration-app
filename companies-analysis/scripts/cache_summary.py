#!/usr/bin/env python3
"""
Script pour afficher un résumé des entreprises en cache
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from collections import defaultdict

# Connexion à la base de données
db_path = "data/pappers_cache.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Récupérer toutes les entreprises
cursor.execute("SELECT siren, data FROM entreprises")
rows = cursor.fetchall()

print("=" * 80)
print(f"📊 RÉSUMÉ DES {len(rows)} ENTREPRISES EN CACHE")
print("=" * 80)
print()

# Statistiques par ville
villes = defaultdict(int)
secteurs = defaultdict(int)
effectifs_ranges = {
    '1-5': 0,
    '6-10': 0,
    '11-20': 0,
    '21-50': 0,
    '51-100': 0,
    '100+': 0
}

# Liste détaillée
companies = []

for siren, data_str in rows:
    data = json.loads(data_str)

    nom = data.get('nom_entreprise', 'Inconnu')
    ville = data.get('siege', {}).get('ville', 'Inconnue')
    code_postal = data.get('siege', {}).get('code_postal', '')
    effectif = data.get('effectif', 0)
    # Convertir effectif en int si c'est une string
    try:
        effectif = int(effectif) if effectif else 0
    except (ValueError, TypeError):
        effectif = 0
    secteur = data.get('libelle_code_naf', 'Non spécifié')

    # Stats
    villes[ville] += 1
    secteurs[secteur[:50]] += 1  # Tronquer les secteurs longs

    if effectif <= 5:
        effectifs_ranges['1-5'] += 1
    elif effectif <= 10:
        effectifs_ranges['6-10'] += 1
    elif effectif <= 20:
        effectifs_ranges['11-20'] += 1
    elif effectif <= 50:
        effectifs_ranges['21-50'] += 1
    elif effectif <= 100:
        effectifs_ranges['51-100'] += 1
    else:
        effectifs_ranges['100+'] += 1

    companies.append({
        'nom': nom,
        'ville': ville,
        'code_postal': code_postal,
        'effectif': effectif,
        'secteur': secteur,
        'siren': siren
    })

# Trier par ville puis nom
companies.sort(key=lambda x: (x['ville'], x['nom']))

# Afficher la liste détaillée
print("📋 LISTE DES ENTREPRISES")
print("-" * 80)
print(f"{'Nom':<40} {'Ville':<20} {'Eff.':<6} {'Secteur'}")
print("-" * 80)

for c in companies:
    nom_short = c['nom'][:38] if len(c['nom']) > 38 else c['nom']
    ville_short = f"{c['ville']} ({c['code_postal'][:2]})" if c['code_postal'] else c['ville']
    ville_short = ville_short[:18] if len(ville_short) > 18 else ville_short
    secteur_short = c['secteur'][:40] if len(c['secteur']) > 40 else c['secteur']
    print(f"{nom_short:<40} {ville_short:<20} {c['effectif']:<6} {secteur_short}")

print()
print("=" * 80)
print("📈 STATISTIQUES")
print("=" * 80)
print()

# Top 10 villes
print("🏙️  TOP 10 VILLES")
print("-" * 40)
for ville, count in sorted(villes.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{ville:<30} : {count:>3} entreprises")

print()
print("👥 RÉPARTITION PAR EFFECTIF")
print("-" * 40)
for range_name, count in effectifs_ranges.items():
    pct = (count / len(rows) * 100) if len(rows) > 0 else 0
    print(f"{range_name:<15} : {count:>3} entreprises ({pct:>5.1f}%)")

print()
print("🏢 TOP 10 SECTEURS")
print("-" * 40)
for secteur, count in sorted(secteurs.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{secteur:<45} : {count:>2}")

print()
print("=" * 80)

conn.close()
