"""
Script de démonstration - Analyse d'entreprises
Lance des analyses sans interaction utilisateur
"""

import os
from loguru import logger
from dotenv import load_dotenv

from src.strategies.companies import CompanyAnalyzer
from src.data.storage import OpportunityStorage
from src.data.pappers_client import PappersClient


def main():
    """
    Démonstration complète de l'analyseur d'entreprises
    """
    # Charge les variables d'environnement
    load_dotenv()

    # Configure le logging
    logger.add("logs/demo_{time}.log", rotation="1 day")

    print("=" * 70)
    print("DÉMONSTRATION - ANALYSEUR D'ENTREPRISES")
    print("=" * 70)
    print()

    # Vérifie la clé API
    if not os.getenv('PAPPERS_API_KEY'):
        print("❌ ERREUR: Clé API Pappers manquante dans .env")
        return

    print("✅ Clé API configurée")
    print()

    # Initialise le stockage
    storage = OpportunityStorage("data/companies.db")
    print("✅ Base de données initialisée")
    print()

    # ========================================
    # DÉMO 1: Analyse d'une liste de SIREN
    # ========================================
    print("=" * 70)
    print("DÉMO 1: Analyse d'une liste d'entreprises françaises")
    print("=" * 70)
    print()

    # Entreprises de démonstration
    siren_list = [
        "552032534",  # DANONE
        "542065479",  # STELLANTIS (ex-PSA)
        "542051180",  # L'ORÉAL
    ]

    config = {
        'siren_list': siren_list,
        'min_ca': 100000,
        'min_growth_rate': 10,
        'min_margin': 5,
        'min_confidence': 50
    }

    print(f"📊 Analyse de {len(siren_list)} grandes entreprises françaises...")
    print()

    analyzer = CompanyAnalyzer(config)
    opportunities = analyzer.run_scan()

    if opportunities:
        print(f"✅ {len(opportunities)} insights détectés:\n")

        for i, opp in enumerate(opportunities, 1):
            print(f"{i}. {opp.data['denomination']}")
            print(f"   └─ Type: {opp.opportunity_type.value}")
            print(f"   └─ {opp.metadata['message']}")
            print(f"   └─ Confiance: {opp.confidence:.0f}/100")

            if 'growth_rate' in opp.data:
                print(f"   └─ Détails: CA passé de {opp.data['ca_precedent']:,.0f}€ à {opp.data['ca_dernier']:,.0f}€")
            elif 'marge' in opp.data:
                print(f"   └─ Détails: CA {opp.data['ca']:,.0f}€, Résultat {opp.data['resultat']:,.0f}€")

            print()

        # Sauvegarde
        storage.save_batch(opportunities)
        print(f"💾 {len(opportunities)} insights sauvegardés dans data/companies.db")
    else:
        print("ℹ️  Aucun insight détecté avec les critères actuels")

    print()

    # ========================================
    # DÉMO 2: Recherche et analyse
    # ========================================
    print("=" * 70)
    print("DÉMO 2: Recherche d'entreprises par nom")
    print("=" * 70)
    print()

    search_term = "carrefour"
    print(f"🔍 Recherche de '{search_term}'...")
    print()

    try:
        opportunities = analyzer.search_and_analyze(search_term, max_companies=2)

        if opportunities:
            print(f"✅ {len(opportunities)} insights détectés:\n")

            for i, opp in enumerate(opportunities, 1):
                print(f"{i}. {opp.data['denomination']}")
                print(f"   └─ SIREN: {opp.symbol}")
                print(f"   └─ {opp.metadata['message']}")
                print(f"   └─ Confiance: {opp.confidence:.0f}/100")
                print()

            storage.save_batch(opportunities)
        else:
            print("ℹ️  Aucun insight détecté pour ces entreprises")
    except Exception as e:
        print(f"⚠️  Erreur lors de la recherche: {e}")

    print()

    # ========================================
    # DÉMO 3: Utilisation du client API direct
    # ========================================
    print("=" * 70)
    print("DÉMO 3: Utilisation directe du client API")
    print("=" * 70)
    print()

    client = PappersClient()

    # Exemple avec LVMH
    siren_demo = "775684019"  # LVMH
    print(f"📄 Récupération des données pour SIREN {siren_demo}...")
    print()

    try:
        data = client.get_entreprise(siren_demo)

        print(f"Entreprise : {data.get('nom_entreprise', 'N/A')}")
        print(f"Forme      : {data.get('forme_juridique', 'N/A')}")
        print(f"Ville      : {data.get('siege', {}).get('ville', 'N/A')}")

        # Finances
        finances = data.get('finances', [])
        if finances:
            print(f"\n💰 Données financières ({len(finances)} exercices disponibles):")
            for exercice in finances[:3]:  # Top 3
                ca = exercice.get('chiffre_affaires')
                resultat = exercice.get('resultat')
                date = exercice.get('date_cloture_exercice', 'N/A')

                if ca:
                    print(f"   • {date}: CA = {ca:,.0f}€", end="")
                    if resultat:
                        print(f", Résultat = {resultat:,.0f}€")
                    else:
                        print()

        # Dirigeants
        dirigeants = data.get('representants', [])
        if dirigeants:
            print(f"\n👔 Dirigeants ({len(dirigeants)} personnes):")
            for dir in dirigeants[:5]:  # Top 5
                nom = dir.get('nom', '')
                prenom = dir.get('prenom', '')
                qualite = dir.get('qualite', 'N/A')
                print(f"   • {prenom} {nom} - {qualite}")

    except Exception as e:
        print(f"⚠️  Erreur: {e}")

    print()

    # ========================================
    # STATISTIQUES
    # ========================================
    print("=" * 70)
    print("STATISTIQUES GLOBALES")
    print("=" * 70)
    print()

    stats = storage.get_statistics()

    print(f"📊 Total d'insights en base : {stats['total_opportunities']}")

    if stats['total_opportunities'] > 0:
        print(f"📈 Profit potentiel moyen   : {stats['average_profit']:.2f}%")

    if stats['by_strategy']:
        print("\n🎯 Par stratégie:")
        for item in stats['by_strategy']:
            print(f"   • {item['strategy']}: {item['count']} insights")

    print()
    print("=" * 70)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("=" * 70)
    print()
    print("💡 Pour analyser vos propres entreprises:")
    print("   1. Modifiez la liste 'siren_list' dans ce script")
    print("   2. Ou utilisez: python analyze_companies.py")
    print()
    print("📖 Documentation complète: GUIDE_ENTREPRISES.md")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Arrêté par l'utilisateur")
    except Exception as e:
        logger.exception("Erreur fatale")
        print(f"\n❌ Erreur: {e}")
