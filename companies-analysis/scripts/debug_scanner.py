#!/usr/bin/env python3
"""
Script de debug pour comprendre pourquoi les entreprises sont filtrées
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from loguru import logger

from src.data.pappers_client import PappersClient

# Configure logger
logger.remove()
logger.add(sys.stderr, level="DEBUG")

load_dotenv()
api_key = os.getenv('PAPPERS_API_KEY')

if not api_key:
    logger.error("PAPPERS_API_KEY non trouvée dans .env")
    sys.exit(1)

pappers = PappersClient(api_key=api_key)

# Rechercher quelques entreprises
logger.info("Recherche d'entreprises dans le secteur conseil...")
companies = pappers.recherche(query="conseil", max_results=5)

logger.info(f"\nAnalyse de {len(companies)} entreprises:")
logger.info("=" * 80)

for i, company in enumerate(companies, 1):
    siren = company.get('siren')
    nom = company.get('nom_entreprise', 'N/A')

    logger.info(f"\n{i}. {nom} ({siren})")
    logger.info("-" * 80)

    try:
        data = pappers.get_entreprise(siren)

        # Infos de base
        effectif = data.get('effectif', 0)
        activite = data.get('libelle_code_naf', 'N/A')
        date_creation = data.get('date_creation_entreprise', 'N/A')

        logger.info(f"  Activité: {activite}")
        logger.info(f"  Effectif: {effectif}")
        logger.info(f"  Date création: {date_creation}")

        # Finances
        finances = data.get('finances', [])
        if finances:
            dernier = finances[0]
            ca = dernier.get('chiffre_affaires')
            resultat = dernier.get('resultat')
            immobilisations = dernier.get('immobilisations')
            annee = dernier.get('annee_fin_exercice')

            logger.info(f"  Exercice: {annee}")
            logger.info(f"  CA: {ca:,}€" if ca else "  CA: Non disponible")
            logger.info(f"  Résultat: {resultat:,}€" if resultat else "  Résultat: Non disponible")
            logger.info(f"  Immobilisations: {immobilisations:,}€" if immobilisations else "  Immobilisations: Non disponible")

            if ca and effectif and effectif > 0:
                ca_per_employee = ca / effectif
                logger.info(f"  CA/salarié: {ca_per_employee:,.0f}€")

                # Vérification des critères
                logger.info(f"\n  Critères:")
                logger.info(f"    ✓ CA > 300k€: {'✓' if ca >= 300000 else '✗'} ({ca:,}€)" if ca else "    ✗ CA non disponible")
                logger.info(f"    ✓ Effectif < 15: {'✓' if 0 < effectif <= 15 else '✗'} ({effectif})")
                logger.info(f"    ✓ CA/salarié > 50k€: {'✓' if ca_per_employee >= 50000 else '✗'} ({ca_per_employee:,.0f}€)")
                logger.info(f"    ✓ Résultat positif: {'✓' if resultat and resultat > 0 else '✗'}")
            else:
                logger.info(f"  ✗ Impossible de calculer CA/salarié")
        else:
            logger.info(f"  ✗ Pas de données financières disponibles")

    except Exception as e:
        logger.error(f"  Erreur: {e}")

logger.info("\n" + "=" * 80)
logger.info("Fin de l'analyse de debug")
