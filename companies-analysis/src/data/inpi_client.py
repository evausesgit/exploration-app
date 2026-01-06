"""
Client pour l'API INPI Data - Accès gratuit aux données financières

Documentation: https://data.inpi.fr/content/editorial/Acces_API_Entreprises
API: https://registre-national-entreprises.inpi.fr/api/companies/{siren}
"""

import os
import requests
from typing import Dict, Optional, List
from loguru import logger
from datetime import datetime


class INPIClient:
    """
    Client pour interroger l'API INPI Data gratuitement

    Données disponibles :
    - Bilans comptables
    - Comptes de résultats
    - Immobilisations
    - CA, résultat, capitaux propres
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le client INPI

        Args:
            api_key: Clé API INPI (optionnel si dans .env)
        """
        self.api_key = api_key or os.getenv('INPI_API_KEY')
        self.base_url = "https://registre-national-entreprises.inpi.fr/api"
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json'
            })
            logger.info("INPIClient initialized with API key")
        else:
            logger.warning("INPI_API_KEY not found - API calls may be limited")

    def get_company_info(self, siren: str) -> Optional[Dict]:
        """
        Récupère les informations d'entreprise depuis l'API INPI

        Args:
            siren: Numéro SIREN (9 chiffres)

        Returns:
            Dictionnaire avec les données de l'entreprise ou None
        """
        try:
            url = f"{self.base_url}/companies/{siren}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                logger.debug(f"✅ INPI data retrieved for {siren}")
                return response.json()
            elif response.status_code == 404:
                logger.debug(f"❌ No INPI data for {siren}")
                return None
            else:
                logger.warning(f"INPI API error {response.status_code} for {siren}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {siren}: {e}")
            return None

    def get_financial_data(self, siren: str) -> Optional[Dict]:
        """
        Récupère les données financières (bilans) depuis l'API INPI

        Args:
            siren: Numéro SIREN

        Returns:
            Dict avec CA, résultat, immobilisations, etc.
        """
        try:
            url = f"{self.base_url}/companies/{siren}/attachments"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Chercher le dernier bilan comptable
                bilans = [
                    doc for doc in data.get('documents', [])
                    if doc.get('type') == 'BILAN' or doc.get('type') == 'COMPTES_ANNUELS'
                ]

                if not bilans:
                    logger.debug(f"No financial statements found for {siren}")
                    return None

                # Prendre le plus récent
                latest_bilan = sorted(
                    bilans,
                    key=lambda x: x.get('dateDepot', ''),
                    reverse=True
                )[0]

                return self._extract_financial_metrics(latest_bilan, siren)

            elif response.status_code == 404:
                logger.debug(f"No attachments for {siren}")
                return None
            else:
                logger.warning(f"INPI attachments API error {response.status_code} for {siren}")
                return None

        except Exception as e:
            logger.error(f"Error fetching financial data for {siren}: {e}")
            return None

    def _extract_financial_metrics(self, bilan: Dict, siren: str) -> Dict:
        """
        Extrait les métriques financières d'un document de bilan

        Args:
            bilan: Document de bilan INPI
            siren: Numéro SIREN

        Returns:
            Dict avec les métriques extraites
        """
        # Note: La structure exacte dépend du format INPI
        # Il faudra ajuster selon la vraie réponse de l'API

        financials = bilan.get('financialData', {})

        metrics = {
            'siren': siren,
            'exercice_date': bilan.get('dateClotureExercice'),
            'date_depot': bilan.get('dateDepot'),
            'chiffre_affaires': financials.get('chiffreAffaires'),
            'resultat_net': financials.get('resultatNet'),
            'capitaux_propres': financials.get('capitauxPropres'),
            'immobilisations': financials.get('immobilisations'),
            'dettes': financials.get('dettes'),
            'effectif': financials.get('effectif'),
            'source': 'INPI'
        }

        # Calculer la marge si possible
        if metrics['chiffre_affaires'] and metrics['resultat_net']:
            ca = metrics['chiffre_affaires']
            if ca > 0:
                metrics['marge_pct'] = (metrics['resultat_net'] / ca) * 100

        logger.info(
            f"💰 INPI financials for {siren}: "
            f"CA={metrics.get('chiffre_affaires', 'N/A')}, "
            f"Résultat={metrics.get('resultat_net', 'N/A')}"
        )

        return metrics

    def enrich_companies_batch(self, sirens: List[str]) -> Dict[str, Dict]:
        """
        Enrichit un lot de SIREN avec les données INPI

        Args:
            sirens: Liste de numéros SIREN

        Returns:
            Dict {siren: financial_data}
        """
        results = {}

        logger.info(f"🔍 Enriching {len(sirens)} companies with INPI data...")

        for i, siren in enumerate(sirens, 1):
            logger.info(f"[{i}/{len(sirens)}] Processing {siren}...")

            financial_data = self.get_financial_data(siren)

            if financial_data:
                results[siren] = financial_data

            # Rate limiting - respecter les limites de l'API
            import time
            time.sleep(0.5)  # 2 requêtes/seconde max

        logger.info(
            f"✅ INPI enrichment complete: {len(results)}/{len(sirens)} "
            f"companies enriched ({len(results)/len(sirens)*100:.1f}%)"
        )

        return results
