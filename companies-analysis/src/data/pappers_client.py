"""
Client pour l'API Pappers.fr
Permet de récupérer les données d'entreprises françaises
"""

import os
import time
import requests
from typing import Dict, List, Optional, Any
from loguru import logger
from datetime import datetime


class PappersAPIError(Exception):
    """Exception levée lors d'erreurs API Pappers"""
    pass


class PappersClient:
    """
    Client pour interagir avec l'API Pappers

    Documentation: https://www.pappers.fr/api/documentation

    Endpoints principaux:
    - /v2/entreprise : Récupère les informations d'une entreprise
    - /v2/recherche : Recherche d'entreprises
    """

    BASE_URL = "https://api.pappers.fr/v2"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le client Pappers

        Args:
            api_key: Clé API Pappers (ou via env var PAPPERS_API_KEY)
        """
        self.api_key = api_key or os.getenv('PAPPERS_API_KEY')

        if not self.api_key:
            raise ValueError(
                "Clé API Pappers requise. "
                "Définissez PAPPERS_API_KEY dans .env ou passez-la au constructeur"
            )

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ExplorationApp/1.0'
        })

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 5 req/sec max

        logger.info("PappersClient initialized")

    def _wait_for_rate_limit(self):
        """Attend pour respecter le rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict:
        """
        Effectue une requête à l'API Pappers

        Args:
            endpoint: Endpoint API (ex: '/entreprise')
            params: Paramètres de la requête

        Returns:
            Réponse JSON

        Raises:
            PappersAPIError: En cas d'erreur API
        """
        self._wait_for_rate_limit()

        # Ajoute la clé API
        params['api_token'] = self.api_key

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)

            # Parse le JSON (même en cas d'erreur HTTP)
            try:
                data = response.json()
            except:
                data = {}

            # Vérifie le status HTTP
            if response.status_code != 200:
                # Analyse le message d'erreur
                if 'error' in data or 'erreur' in data:
                    error_msg = data.get('error', data.get('erreur', 'Erreur inconnue'))
                    message = data.get('message', '')

                    # Cas spécifique : plus de crédits
                    if 'crédits' in error_msg.lower() or 'crédits' in message.lower():
                        raise PappersAPIError(
                            f"❌ Plus de crédits API disponibles.\n"
                            f"   Message: {message}\n"
                            f"   → Consultez votre compte sur https://www.pappers.fr"
                        )
                    # Cas spécifique : 401
                    elif response.status_code == 401:
                        raise PappersAPIError(
                            f"❌ Erreur d'authentification.\n"
                            f"   Message: {error_msg}\n"
                            f"   → Vérifiez votre clé API dans le fichier .env"
                        )
                    # Cas spécifique : 429 (rate limit)
                    elif response.status_code == 429:
                        raise PappersAPIError(
                            f"❌ Limite de requêtes dépassée.\n"
                            f"   → Attendez quelques secondes avant de réessayer"
                        )
                    else:
                        raise PappersAPIError(f"Erreur API ({response.status_code}): {error_msg} - {message}")
                else:
                    raise PappersAPIError(f"Erreur HTTP {response.status_code}")

            # Vérifie les erreurs dans la réponse (même avec status 200)
            if 'erreur' in data:
                raise PappersAPIError(f"Erreur API: {data['erreur']}")

            return data

        except PappersAPIError:
            # Re-raise les erreurs API qu'on a déjà formatées
            raise
        except requests.exceptions.Timeout:
            raise PappersAPIError("❌ Timeout: l'API Pappers met trop de temps à répondre")
        except requests.exceptions.ConnectionError:
            raise PappersAPIError("❌ Erreur de connexion: vérifiez votre connexion internet")
        except requests.exceptions.RequestException as e:
            raise PappersAPIError(f"❌ Erreur réseau: {str(e)}")

    def get_entreprise(self, siren: str) -> Dict:
        """
        Récupère les informations complètes d'une entreprise

        Args:
            siren: Numéro SIREN (9 chiffres)

        Returns:
            Dict contenant toutes les données de l'entreprise
        """
        logger.info(f"Fetching data for SIREN: {siren}")

        # Validation SIREN
        siren = siren.replace(' ', '')
        if not siren.isdigit() or len(siren) != 9:
            raise ValueError(f"SIREN invalide: {siren} (doit être 9 chiffres)")

        data = self._make_request('entreprise', {
            'siren': siren,
            # Options pour récupérer toutes les données
            'avec_donnees_financieres': 'true',
            'avec_dirigeants': 'true',
            'avec_beneficiaires': 'true',
            'avec_comptes': 'true'
        })

        return data

    def get_finances(self, siren: str) -> List[Dict]:
        """
        Récupère uniquement les données financières d'une entreprise

        Args:
            siren: Numéro SIREN

        Returns:
            Liste des exercices financiers (années)
        """
        data = self.get_entreprise(siren)

        finances = data.get('finances', [])

        if not finances:
            logger.warning(f"Aucune donnée financière pour SIREN {siren}")

        return finances

    def get_dirigeants(self, siren: str) -> List[Dict]:
        """
        Récupère les dirigeants d'une entreprise

        Args:
            siren: Numéro SIREN

        Returns:
            Liste des dirigeants
        """
        data = self.get_entreprise(siren)

        dirigeants = data.get('representants', [])

        if not dirigeants:
            logger.warning(f"Aucun dirigeant trouvé pour SIREN {siren}")

        return dirigeants

    def get_beneficiaires(self, siren: str) -> List[Dict]:
        """
        Récupère les bénéficiaires effectifs d'une entreprise

        Args:
            siren: Numéro SIREN

        Returns:
            Liste des bénéficiaires effectifs
        """
        data = self.get_entreprise(siren)

        beneficiaires = data.get('beneficiaires_effectifs', [])

        if not beneficiaires:
            logger.info(f"Aucun bénéficiaire effectif pour SIREN {siren}")

        return beneficiaires

    def recherche(
        self,
        query: str,
        max_results: int = 10,
        departement: Optional[str] = None,
        code_naf: Optional[str] = None
    ) -> List[Dict]:
        """
        Recherche des entreprises par nom ou critères

        Args:
            query: Terme de recherche (nom, raison sociale)
            max_results: Nombre max de résultats
            departement: Filtrer par département (ex: "75" pour Paris)
            code_naf: Filtrer par code NAF

        Returns:
            Liste d'entreprises trouvées
        """
        params = {
            'q': query,
            'nombre': max_results
        }

        if departement:
            params['departement'] = departement
        if code_naf:
            params['code_naf'] = code_naf

        logger.info(f"Searching companies: '{query}'")

        data = self._make_request('recherche', params)

        resultats = data.get('resultats', [])

        logger.info(f"Found {len(resultats)} companies")

        return resultats

    def get_financial_health_score(self, siren: str) -> Optional[float]:
        """
        Calcule un score de santé financière basique

        Args:
            siren: Numéro SIREN

        Returns:
            Score de 0 à 100 (ou None si pas de données)
        """
        try:
            finances = self.get_finances(siren)

            if not finances:
                return None

            # Prend le dernier exercice
            dernier_exercice = finances[0]

            ca = dernier_exercice.get('chiffre_affaires')
            resultat = dernier_exercice.get('resultat')

            if ca is None or resultat is None:
                return None

            # Score simple basé sur la marge et la rentabilité
            if ca == 0:
                return 0.0

            marge = (resultat / ca) * 100 if ca > 0 else 0

            # Score de 0 à 100
            # Marge > 10% = 100
            # Marge < -10% = 0
            score = max(0, min(100, 50 + (marge * 5)))

            return round(score, 2)

        except Exception as e:
            logger.error(f"Error calculating financial score for {siren}: {e}")
            return None
