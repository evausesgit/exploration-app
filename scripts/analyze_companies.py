"""
Script d'exemple pour analyser des entreprises via l'API Pappers
"""

import os
import sys

# Ajoute le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import os
from loguru import logger
from dotenv import load_dotenv

from src.strategies.companies import CompanyAnalyzer
from src.data.storage import OpportunityStorage


def main():
    """
    Analyse des entreprises et sauvegarde des insights
    """
    # Charge les variables d'environnement
    load_dotenv()

    # Configure le logging
    logger.add("logs/companies_{time}.log", rotation="1 day")

    print("=" * 60)
    print("ANALYSEUR D'ENTREPRISES - API PAPPERS")
    print("=" * 60)
    print()

    # Vérifie la clé API
    if not os.getenv('PAPPERS_API_KEY'):
        print("⚠️  ERREUR: Clé API Pappers manquante")
        print("   Ajoutez PAPPERS_API_KEY dans votre fichier .env")
        print("   Obtenez une clé gratuite sur: https://www.pappers.fr/api")
        return

    # Initialise le stockage
    storage = OpportunityStorage("data/companies.db")

    # MÉTHODE 1: Analyser une liste de SIREN
    print("\n📊 Méthode 1: Analyse d'une liste de SIREN")
    print("-" * 60)

    # Exemples de SIREN (entreprises françaises connues)
    # Vous pouvez remplacer par vos propres SIREN
    siren_list = [
        "552032534",  # TOTAL ENERGIES
        "542065479",  # CARREFOUR
        "775684019",  # AMAZON FRANCE
    ]

    config = {
        'siren_list': siren_list,
        'min_ca': 100000,  # CA minimum: 100k€
        'min_growth_rate': 10,  # Croissance minimum: 10%
        'min_margin': 5,  # Marge minimum: 5%
        'min_confidence': 50
    }

    analyzer = CompanyAnalyzer(config)

    print(f"Analyse de {len(siren_list)} entreprises...")
    opportunities = analyzer.run_scan()

    if opportunities:
        print(f"\n✅ {len(opportunities)} insights détectés:\n")
        for opp in opportunities:
            print(f"  • {opp.data['denomination']}")
            print(f"    Type: {opp.opportunity_type.value}")
            print(f"    {opp.metadata['message']}")
            print(f"    Confiance: {opp.confidence:.0f}/100")
            print()

        # Sauvegarde
        storage.save_batch(opportunities)
        print(f"💾 Sauvegardé dans: data/companies.db")
    else:
        print("❌ Aucun insight détecté")

    # MÉTHODE 2: Rechercher et analyser
    print("\n" + "=" * 60)
    print("📊 Méthode 2: Recherche et analyse")
    print("-" * 60)

    query = input("\nEntrez un nom d'entreprise à rechercher (ou ENTER pour passer): ").strip()

    if query:
        print(f"\nRecherche de '{query}'...")
        opportunities = analyzer.search_and_analyze(query, max_companies=3)

        if opportunities:
            print(f"\n✅ {len(opportunities)} insights détectés:\n")
            for opp in opportunities:
                print(f"  • {opp.data['denomination']}")
                print(f"    Type: {opp.opportunity_type.value}")
                print(f"    {opp.metadata['message']}")
                print(f"    Confiance: {opp.confidence:.0f}/100")
                print()

            storage.save_batch(opportunities)
        else:
            print("❌ Aucun insight détecté")

    # Statistiques
    print("\n" + "=" * 60)
    print("📈 STATISTIQUES GLOBALES")
    print("-" * 60)

    stats = storage.get_statistics()
    print(f"\nTotal d'insights en base: {stats['total_opportunities']}")

    if stats['by_strategy']:
        print("\nPar stratégie:")
        for item in stats['by_strategy']:
            print(f"  • {item['strategy']}: {item['count']}")

    print("\n" + "=" * 60)
    print("Terminé !")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Arrêté par l'utilisateur")
    except Exception as e:
        logger.exception("Erreur fatale")
        print(f"\n❌ Erreur: {e}")
