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
from .pappers_cache import PappersCache


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

    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        Initialise le client Pappers

        Args:
            api_key: Clé API Pappers (ou via env var PAPPERS_API_KEY)
            use_cache: Activer le cache SQLite (défaut: True, fortement recommandé pour économiser les crédits)
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

        # Cache SQLite pour économiser les crédits API
        self.use_cache = use_cache
        self.cache = PappersCache() if use_cache else None

        if self.use_cache:
            stats = self.cache.get_stats()
            logger.info(f"PappersClient initialized with cache ({stats['entreprises']} entreprises cached)")
        else:
            logger.info("PappersClient initialized WITHOUT cache (not recommended)")

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

    @staticmethod
    def _parse_effectif(effectif_str) -> int:
        """
        Parse l'effectif de Pappers (peut être un texte ou un nombre)

        Args:
            effectif_str: Effectif brut de l'API (ex: "Entre 20 et 49 salariés", "3", etc.)

        Returns:
            Nombre d'employés (moyenne de la tranche si texte)
        """
        if isinstance(effectif_str, int):
            return effectif_str

        if not effectif_str or effectif_str == '0 salarié':
            return 0

        effectif_lower = str(effectif_str).lower()

        # Mapping des tranches d'effectif
        if 'entre 1 et 2' in effectif_lower or '1 ou 2' in effectif_lower:
            return 2
        elif 'entre 3 et 5' in effectif_lower or '3 à 5' in effectif_lower:
            return 4
        elif 'entre 6 et 9' in effectif_lower or '6 à 9' in effectif_lower:
            return 8
        elif 'entre 10 et 19' in effectif_lower or '10 à 19' in effectif_lower:
            return 15
        elif 'entre 20 et 49' in effectif_lower or '20 à 49' in effectif_lower:
            return 35
        elif 'entre 50 et 99' in effectif_lower or '50 à 99' in effectif_lower:
            return 75
        elif 'entre 100 et 199' in effectif_lower or '100 à 199' in effectif_lower:
            return 150
        elif 'entre 200 et 249' in effectif_lower or '200 à 249' in effectif_lower:
            return 225
        elif 'entre 250 et 499' in effectif_lower or '250 à 499' in effectif_lower:
            return 375
        elif 'entre 500 et 999' in effectif_lower or '500 à 999' in effectif_lower:
            return 750
        elif 'au moins 1 salarié' in effectif_lower or 'au moins 1' in effectif_lower:
            return 1
        elif '2000' in effectif_lower or 'plus de' in effectif_lower:
            return 2000  # Grande entreprise

        # Tenter d'extraire un nombre
        try:
            # Chercher des nombres dans la chaîne
            import re
            numbers = re.findall(r'\d+', effectif_lower)
            if numbers:
                return int(numbers[0])
        except:
            pass

        return 0

    def get_entreprise(self, siren: str) -> Dict:
        """
        Récupère les informations complètes d'une entreprise

        Args:
            siren: Numéro SIREN (9 chiffres)

        Returns:
            Dict contenant toutes les données de l'entreprise
        """
        # Validation SIREN
        siren = siren.replace(' ', '')
        if not siren.isdigit() or len(siren) != 9:
            raise ValueError(f"SIREN invalide: {siren} (doit être 9 chiffres)")

        # Vérifier le cache d'abord
        if self.use_cache:
            cached_data = self.cache.get_entreprise(siren)
            if cached_data:
                logger.info(f"💾 Cache HIT for SIREN {siren} (économie de 1 crédit API)")
                # Normaliser l'effectif en nombre
                if 'effectif' in cached_data:
                    cached_data['effectif'] = self._parse_effectif(cached_data['effectif'])
                return cached_data

        # Si pas en cache, faire la requête API
        logger.info(f"🌐 Fetching from API for SIREN: {siren} (consomme 1 crédit)")

        data = self._make_request('entreprise', {
            'siren': siren,
            # Options pour récupérer toutes les données
            'avec_donnees_financieres': 'true',
            'avec_dirigeants': 'true',
            'avec_beneficiaires': 'true',
            'avec_comptes': 'true'
        })

        # Stocker dans le cache
        if self.use_cache:
            self.cache.set_entreprise(siren, data)
            logger.debug(f"💾 Cached data for SIREN {siren}")

        # Normaliser l'effectif en nombre
        if 'effectif' in data:
            data['effectif'] = self._parse_effectif(data['effectif'])

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
        # Vérifier le cache d'abord (uniquement pour recherches simples sans code_naf)
        if self.use_cache and not code_naf:
            cached_results = self.cache.get_recherche(query, departement)
            if cached_results:
                resultats = cached_results.get('resultats', [])
                logger.info(f"💾 Cache HIT for recherche '{query}' ({len(resultats)} résultats)")
                return resultats[:max_results]

        # Si pas en cache, faire la requête API
        params = {
            'q': query,
            'nombre': max_results
        }

        if departement:
            params['departement'] = departement
        if code_naf:
            params['code_naf'] = code_naf

        logger.info(f"🌐 Searching companies from API: '{query}' (consomme des crédits)")

        data = self._make_request('recherche', params)

        # Stocker dans le cache (uniquement si pas de code_naf pour simplifier)
        if self.use_cache and not code_naf:
            self.cache.set_recherche(query, data, departement)
            logger.debug(f"💾 Cached recherche '{query}'")

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
