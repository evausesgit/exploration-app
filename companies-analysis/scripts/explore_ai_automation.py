#!/usr/bin/env python3
"""
Script d'exploration des opportunités d'automatisation IA

Usage:
    python scripts/explore_ai_automation.py
    python scripts/explore_ai_automation.py --secteurs conseil marketing_digital
    python scripts/explore_ai_automation.py --departements 75 92 --min-ca 2000000
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

from src.strategies.ai_automation_scanner import AIAutomationScanner, SECTEURS_PRIORITAIRES

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def main():
    parser = argparse.ArgumentParser(
        description="Explorer les opportunités d'automatisation IA dans les entreprises françaises"
    )

    # Secteurs
    parser.add_argument(
        '--secteurs',
        nargs='+',
        choices=list(SECTEURS_PRIORITAIRES.keys()),
        default=['conseil', 'marketing_digital', 'saas_tech'],
        help="Secteurs à scanner (défaut: conseil marketing_digital saas_tech)"
    )

    # Géographie
    parser.add_argument(
        '--departements',
        nargs='+',
        help="Départements à cibler (ex: 75 92 93). Laisser vide pour toute la France"
    )

    # Critères financiers
    parser.add_argument(
        '--min-ca',
        type=int,
        default=1000000,
        help="CA minimum en euros (défaut: 1000000)"
    )

    parser.add_argument(
        '--max-effectif',
        type=int,
        default=10,
        help="Effectif maximum (défaut: 10)"
    )

    parser.add_argument(
        '--min-ca-per-employee',
        type=int,
        default=100000,
        help="CA par salarié minimum en euros (défaut: 100000)"
    )

    parser.add_argument(
        '--min-age-years',
        type=int,
        default=2,
        help="Âge minimum de l'entreprise en années (défaut: 2)"
    )

    # Filtres de résultats
    parser.add_argument(
        '--min-score',
        type=int,
        default=50,
        help="Score minimum d'automatisation (0-100, défaut: 50)"
    )

    parser.add_argument(
        '--max-results-per-sector',
        type=int,
        default=20,
        help="Nombre max d'entreprises à analyser par secteur (défaut: 20)"
    )

    # Sortie
    parser.add_argument(
        '--output',
        default='data/automation_opportunities.json',
        help="Fichier de sortie JSON (défaut: data/automation_opportunities.json)"
    )

    parser.add_argument(
        '--output-csv',
        help="Fichier de sortie CSV optionnel"
    )

    args = parser.parse_args()

    # Charger l'API key
    load_dotenv()
    api_key = os.getenv('PAPPERS_API_KEY')

    if not api_key:
        logger.error("PAPPERS_API_KEY non trouvée dans .env")
        sys.exit(1)

    # Configuration du scanner
    config = {
        'pappers_api_key': api_key,
        'secteurs': args.secteurs,
        'departements': args.departements,
        'min_ca': args.min_ca,
        'max_effectif': args.max_effectif,
        'min_ca_per_employee': args.min_ca_per_employee,
        'min_age_years': args.min_age_years
    }

    logger.info("=" * 60)
    logger.info("🤖 AI AUTOMATION SCANNER")
    logger.info("=" * 60)
    logger.info(f"Secteurs: {', '.join(args.secteurs)}")
    logger.info(f"Départements: {', '.join(args.departements) if args.departements else 'Tous'}")
    logger.info(f"CA min: {args.min_ca:,}€")
    logger.info(f"Effectif max: {args.max_effectif}")
    logger.info(f"CA/salarié min: {args.min_ca_per_employee:,}€")
    logger.info(f"Score min: {args.min_score}/100")
    logger.info("=" * 60)

    try:
        # Créer le scanner
        scanner = AIAutomationScanner(config)

        # Scanner tous les secteurs
        all_opportunities = []

        for secteur in args.secteurs:
            logger.info(f"\n📊 Scanning sector: {secteur}")
            logger.info("-" * 60)

            opportunities = scanner.search_by_sector(
                secteur,
                max_companies=args.max_results_per_sector
            )

            # Filtrer par score minimum
            filtered_opps = [
                opp for opp in opportunities
                if opp.confidence >= args.min_score
            ]

            logger.info(f"✅ {len(filtered_opps)} opportunités détectées (score >= {args.min_score})")

            all_opportunities.extend(filtered_opps)

        # Trier par score
        all_opportunities.sort(key=lambda x: x.confidence, reverse=True)

        logger.info("\n" + "=" * 60)
        logger.info(f"🎯 TOTAL: {len(all_opportunities)} opportunités détectées")
        logger.info("=" * 60)

        if all_opportunities:
            # Statistiques
            avg_score = sum(opp.confidence for opp in all_opportunities) / len(all_opportunities)
            avg_ca_per_employee = sum(opp.data['ca_per_employee'] for opp in all_opportunities) / len(all_opportunities)
            total_ca = sum(opp.data['ca'] for opp in all_opportunities)

            logger.info(f"\n📈 Statistiques:")
            logger.info(f"  Score moyen: {avg_score:.1f}/100")
            logger.info(f"  CA/salarié moyen: {avg_ca_per_employee:,.0f}€")
            logger.info(f"  CA total: {total_ca/1e6:.1f}M€")

            # Top 10
            logger.info(f"\n🏆 Top 10 opportunités:")
            logger.info("-" * 60)
            for i, opp in enumerate(all_opportunities[:10], 1):
                data = opp.data
                logger.info(
                    f"{i:2d}. {data['denomination'][:40]:40s} | "
                    f"Score: {opp.confidence:3.0f} | "
                    f"CA/sal: {data['ca_per_employee']:>8,.0f}€ | "
                    f"Effectif: {data['effectif']:2d}"
                )

            # Sauvegarder en JSON
            os.makedirs(os.path.dirname(args.output), exist_ok=True)

            output_data = {
                'metadata': {
                    'scan_date': datetime.now().isoformat(),
                    'total_opportunities': len(all_opportunities),
                    'config': {
                        'secteurs': args.secteurs,
                        'departements': args.departements,
                        'min_ca': args.min_ca,
                        'max_effectif': args.max_effectif,
                        'min_ca_per_employee': args.min_ca_per_employee,
                        'min_score': args.min_score
                    },
                    'statistics': {
                        'avg_score': avg_score,
                        'avg_ca_per_employee': avg_ca_per_employee,
                        'total_ca': total_ca
                    }
                },
                'opportunities': [
                    {
                        'rank': i + 1,
                        'denomination': opp.data['denomination'],
                        'siren': opp.data['siren'],
                        'automation_score': opp.confidence,
                        'ca': opp.data['ca'],
                        'effectif': opp.data['effectif'],
                        'ca_per_employee': opp.data['ca_per_employee'],
                        'resultat': opp.data['resultat'],
                        'marge_pct': opp.data['marge'],
                        'secteur': opp.data.get('secteur_hint', 'N/A'),
                        'activite': opp.data['activite'],
                        'objet_social': opp.data['objet_social'],
                        'date_creation': opp.data['date_creation'],
                        'ville': opp.data['ville'],
                        'code_postal': opp.data['code_postal']
                    }
                    for i, opp in enumerate(all_opportunities)
                ]
            }

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            logger.info(f"\n💾 Résultats sauvegardés: {args.output}")

            # Export CSV optionnel
            if args.output_csv:
                import pandas as pd

                df = pd.DataFrame([
                    {
                        'Rang': i + 1,
                        'Entreprise': opp.data['denomination'],
                        'SIREN': opp.data['siren'],
                        'Score': int(opp.confidence),
                        'CA': opp.data['ca'],
                        'Effectif': opp.data['effectif'],
                        'CA_par_salarie': int(opp.data['ca_per_employee']),
                        'Resultat': opp.data['resultat'],
                        'Marge_pct': f"{opp.data['marge']:.1f}",
                        'Secteur': opp.data.get('secteur_hint', 'N/A'),
                        'Activite': opp.data['activite'],
                        'Ville': opp.data['ville'],
                        'Code_postal': opp.data['code_postal'],
                        'Date_creation': opp.data['date_creation']
                    }
                    for i, opp in enumerate(all_opportunities)
                ])

                df.to_csv(args.output_csv, index=False, encoding='utf-8-sig')
                logger.info(f"💾 Export CSV sauvegardé: {args.output_csv}")

        else:
            logger.warning("Aucune opportunité trouvée avec les critères spécifiés")

    except Exception as e:
        logger.exception(f"Erreur lors du scan: {e}")
        sys.exit(1)

    logger.info("\n✅ Scan terminé avec succès")


if __name__ == '__main__':
    main()
