#!/usr/bin/env python3
"""
Script pour enrichir la base de données avec les données financières INPI (GRATUIT)

Usage:
    python scripts/enrich_with_inpi.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
from dotenv import load_dotenv
from loguru import logger

from src.data.inpi_client import INPIClient

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def main():
    load_dotenv()

    print("=" * 80)
    print("💰 ENRICHISSEMENT GRATUIT AVEC INPI DATA")
    print("=" * 80)
    print()

    # Connexion à la base de données cache
    db_path = "data/pappers_cache.db"

    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Récupérer tous les SIREN
    cursor.execute("SELECT siren FROM entreprises")
    sirens = [row[0] for row in cursor.fetchall()]

    logger.info(f"📊 Found {len(sirens)} companies in cache")
    print()

    # Initialiser le client INPI
    try:
        inpi_client = INPIClient()
    except Exception as e:
        logger.error(f"Failed to initialize INPI client: {e}")
        logger.info(
            "\n💡 Pour utiliser l'API INPI :\n"
            "   1. Créer un compte sur https://data.inpi.fr\n"
            "   2. Obtenir une clé API (gratuit)\n"
            "   3. Ajouter INPI_API_KEY dans votre fichier .env\n"
        )
        sys.exit(1)

    # Enrichir les entreprises
    print("🔍 Enrichissement en cours (GRATUIT - 0€)...")
    print("-" * 80)

    enriched_data = inpi_client.enrich_companies_batch(sirens)

    # Créer une table pour stocker les données INPI si elle n'existe pas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inpi_financials (
            siren TEXT PRIMARY KEY,
            exercice_date TEXT,
            date_depot TEXT,
            chiffre_affaires REAL,
            resultat_net REAL,
            capitaux_propres REAL,
            immobilisations REAL,
            dettes REAL,
            effectif INTEGER,
            marge_pct REAL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (siren) REFERENCES entreprises(siren)
        )
    """)

    # Sauvegarder les données enrichies
    for siren, financial_data in enriched_data.items():
        cursor.execute("""
            INSERT OR REPLACE INTO inpi_financials (
                siren, exercice_date, date_depot, chiffre_affaires, resultat_net,
                capitaux_propres, immobilisations, dettes, effectif, marge_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            siren,
            financial_data.get('exercice_date'),
            financial_data.get('date_depot'),
            financial_data.get('chiffre_affaires'),
            financial_data.get('resultat_net'),
            financial_data.get('capitaux_propres'),
            financial_data.get('immobilisations'),
            financial_data.get('dettes'),
            financial_data.get('effectif'),
            financial_data.get('marge_pct')
        ))

    conn.commit()

    print()
    print("=" * 80)
    print("📊 RÉSULTATS DE L'ENRICHISSEMENT")
    print("=" * 80)
    print()

    # Statistiques
    cursor.execute("SELECT COUNT(*) FROM inpi_financials")
    total_enriched = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM inpi_financials
        WHERE chiffre_affaires IS NOT NULL AND resultat_net IS NOT NULL
    """)
    with_financials = cursor.fetchone()[0]

    enrichment_rate = (total_enriched / len(sirens) * 100) if len(sirens) > 0 else 0

    print(f"✅ Entreprises enrichies : {total_enriched}/{len(sirens)} ({enrichment_rate:.1f}%)")
    print(f"💰 Avec données financières complètes : {with_financials}")
    print()

    if with_financials > 0:
        # Statistiques financières
        cursor.execute("""
            SELECT
                AVG(chiffre_affaires) as avg_ca,
                AVG(resultat_net) as avg_result,
                AVG(marge_pct) as avg_marge,
                MIN(chiffre_affaires) as min_ca,
                MAX(chiffre_affaires) as max_ca
            FROM inpi_financials
            WHERE chiffre_affaires IS NOT NULL
        """)

        stats = cursor.fetchone()

        print("📈 Statistiques financières (données INPI) :")
        print(f"   CA moyen : {stats[0]:,.0f}€" if stats[0] else "   CA moyen : N/A")
        print(f"   Résultat moyen : {stats[1]:,.0f}€" if stats[1] else "   Résultat moyen : N/A")
        print(f"   Marge moyenne : {stats[2]:.1f}%" if stats[2] else "   Marge moyenne : N/A")
        print(f"   CA min : {stats[3]:,.0f}€" if stats[3] else "   CA min : N/A")
        print(f"   CA max : {stats[4]:,.0f}€" if stats[4] else "   CA max : N/A")
        print()

    # Comparaison Pappers vs INPI
    cursor.execute("""
        SELECT COUNT(*)
        FROM entreprises e
        JOIN inpi_financials i ON e.siren = i.siren
        WHERE i.chiffre_affaires IS NOT NULL
    """)
    overlap = cursor.fetchone()[0]

    print("🔄 Comparaison des sources :")
    print(f"   Pappers : {len(sirens)} entreprises")
    print(f"   INPI : {total_enriched} entreprises enrichies")
    print(f"   Chevauchement : {overlap} entreprises")
    print()

    print("💰 Économie réalisée :")
    print(f"   Crédits Pappers économisés : ~{total_enriched}")
    print(f"   Coût INPI : 0€ (GRATUIT)")
    print()

    print("=" * 80)
    print("✅ Enrichissement terminé avec succès !")
    print("=" * 80)
    print()
    print("💡 Les données INPI sont maintenant disponibles dans la table 'inpi_financials'")
    print("   Utilisez-les pour compléter ou valider les données Pappers")
    print()

    conn.close()


if __name__ == '__main__':
    main()
