"""
Analyseur d'entreprises via API Pappers
Détecte des insights intéressants sur les entreprises françaises
"""

from typing import List, Dict, Any
from loguru import logger

from src.core.scanner_base import ScannerBase
from src.core.opportunity import Opportunity, OpportunityType
from src.data.pappers_client import PappersClient, PappersAPIError


class CompanyAnalyzer(ScannerBase):
    """
    Scanner qui analyse les entreprises via l'API Pappers

    Détecte plusieurs types d'insights:
    - Croissance financière forte
    - Marges élevées
    - Changements de direction
    - Entreprises potentiellement intéressantes
    """

    def __init__(self, config: dict = None):
        """
        Initialise l'analyseur

        Config attendue:
        - pappers_api_key: Clé API Pappers (optionnel si dans .env)
        - siren_list: Liste de SIREN à analyser
        - min_ca: CA minimum pour considérer l'entreprise
        - min_growth_rate: Taux de croissance minimum (%)
        - min_margin: Marge minimum (%)
        """
        super().__init__(config)

        # Initialise le client Pappers
        api_key = self.config.get('pappers_api_key')
        try:
            self.pappers = PappersClient(api_key=api_key)
        except ValueError as e:
            logger.error(f"Failed to initialize Pappers client: {e}")
            raise

        # Paramètres d'analyse
        self.min_ca = self.config.get('min_ca', 100000)  # 100k€
        self.min_growth_rate = self.config.get('min_growth_rate', 20)  # 20%
        self.min_margin = self.config.get('min_margin', 10)  # 10%

    def get_name(self) -> str:
        return "CompanyAnalyzer"

    def scan(self) -> List[Opportunity]:
        """
        Analyse les entreprises de la liste SIREN

        Returns:
            Liste d'opportunités (insights) détectées
        """
        opportunities = []

        siren_list = self.config.get('siren_list', [])

        if not siren_list:
            logger.warning("No SIREN list provided in config")
            return []

        logger.info(f"Analyzing {len(siren_list)} companies")

        for siren in siren_list:
            try:
                company_opps = self._analyze_company(siren)
                opportunities.extend(company_opps)
            except PappersAPIError as e:
                logger.error(f"API error for SIREN {siren}: {e}")
            except Exception as e:
                logger.error(f"Error analyzing SIREN {siren}: {e}")

        return opportunities

    def _analyze_company(self, siren: str) -> List[Opportunity]:
        """
        Analyse une entreprise et détecte les insights

        Args:
            siren: Numéro SIREN

        Returns:
            Liste d'opportunités pour cette entreprise
        """
        opportunities = []

        # Récupère les données complètes
        data = self.pappers.get_entreprise(siren)

        denomination = data.get('nom_entreprise', 'Entreprise inconnue')
        logger.info(f"Analyzing: {denomination} ({siren})")

        # Analyse financière
        finances = data.get('finances', [])
        if len(finances) >= 2:
            financial_opps = self._analyze_finances(siren, denomination, finances)
            opportunities.extend(financial_opps)

        # Analyse des dirigeants
        dirigeants = data.get('representants', [])
        if dirigeants:
            management_opps = self._analyze_management(siren, denomination, dirigeants)
            opportunities.extend(management_opps)

        return opportunities

    def _analyze_finances(
        self,
        siren: str,
        denomination: str,
        finances: List[Dict]
    ) -> List[Opportunity]:
        """
        Analyse les données financières

        Détecte:
        - Croissance forte du CA
        - Marges élevées
        - Amélioration des résultats
        """
        opportunities = []

        # Trie par année décroissante
        finances = sorted(
            finances,
            key=lambda x: x.get('date_cloture_exercice', ''),
            reverse=True
        )

        # Compare les 2 derniers exercices
        if len(finances) < 2:
            return opportunities

        dernier = finances[0]
        precedent = finances[1]

        ca_dernier = dernier.get('chiffre_affaires')
        ca_precedent = precedent.get('chiffre_affaires')
        resultat_dernier = dernier.get('resultat')

        # Vérifie les données
        if None in [ca_dernier, ca_precedent, resultat_dernier]:
            logger.debug(f"Missing financial data for {siren}")
            return opportunities

        # Filtre CA minimum
        if ca_dernier < self.min_ca:
            logger.debug(f"CA too low for {siren}: {ca_dernier}")
            return opportunities

        # 1. Détecte la croissance
        if ca_precedent > 0:
            growth_rate = ((ca_dernier - ca_precedent) / ca_precedent) * 100

            if growth_rate >= self.min_growth_rate:
                confidence = min(100, 50 + (growth_rate / 2))

                opportunities.append(Opportunity(
                    opportunity_type=OpportunityType.FINANCIAL_GROWTH,
                    symbol=siren,
                    strategy=self.get_name(),
                    profit_potential=growth_rate,
                    confidence=confidence,
                    data={
                        'denomination': denomination,
                        'ca_dernier': ca_dernier,
                        'ca_precedent': ca_precedent,
                        'growth_rate': round(growth_rate, 2),
                        'exercice': dernier.get('date_cloture_exercice')
                    },
                    metadata={
                        'type': 'croissance',
                        'message': f"Croissance de {growth_rate:.1f}% du CA"
                    }
                ))

        # 2. Détecte les marges élevées
        if ca_dernier > 0:
            marge = (resultat_dernier / ca_dernier) * 100

            if marge >= self.min_margin:
                confidence = min(100, 40 + (marge * 3))

                opportunities.append(Opportunity(
                    opportunity_type=OpportunityType.HIGH_MARGIN,
                    symbol=siren,
                    strategy=self.get_name(),
                    profit_potential=marge,
                    confidence=confidence,
                    data={
                        'denomination': denomination,
                        'ca': ca_dernier,
                        'resultat': resultat_dernier,
                        'marge': round(marge, 2),
                        'exercice': dernier.get('date_cloture_exercice')
                    },
                    metadata={
                        'type': 'marge',
                        'message': f"Marge nette de {marge:.1f}%"
                    }
                ))

        return opportunities

    def _analyze_management(
        self,
        siren: str,
        denomination: str,
        dirigeants: List[Dict]
    ) -> List[Opportunity]:
        """
        Analyse les changements de direction

        Détecte:
        - Nouveaux dirigeants récents
        - Changements de président
        """
        opportunities = []

        # Cherche les dirigeants récents (moins de 6 mois)
        from datetime import datetime, timedelta

        recent_threshold = datetime.now() - timedelta(days=180)

        for dirigeant in dirigeants:
            date_prise_poste = dirigeant.get('date_prise_de_poste')

            if not date_prise_poste:
                continue

            try:
                # Parse la date (format attendu: "YYYY-MM-DD" ou "DD/MM/YYYY")
                if '/' in date_prise_poste:
                    date_obj = datetime.strptime(date_prise_poste, "%d/%m/%Y")
                else:
                    date_obj = datetime.strptime(date_prise_poste, "%Y-%m-%d")

                if date_obj >= recent_threshold:
                    qualite = dirigeant.get('qualite', 'Dirigeant')
                    nom = dirigeant.get('nom', 'Inconnu')
                    prenom = dirigeant.get('prenom', '')

                    nom_complet = f"{prenom} {nom}".strip()

                    # Score de confiance basé sur la qualité
                    confidence = 70
                    if 'président' in qualite.lower():
                        confidence = 85

                    opportunities.append(Opportunity(
                        opportunity_type=OpportunityType.MANAGEMENT_CHANGE,
                        symbol=siren,
                        strategy=self.get_name(),
                        profit_potential=0,  # Pas de profit quantifiable
                        confidence=confidence,
                        data={
                            'denomination': denomination,
                            'dirigeant': nom_complet,
                            'qualite': qualite,
                            'date_prise_poste': date_prise_poste
                        },
                        metadata={
                            'type': 'management',
                            'message': f"Nouveau {qualite}: {nom_complet}"
                        }
                    ))

            except ValueError:
                logger.debug(f"Invalid date format for {siren}: {date_prise_poste}")
                continue

        return opportunities

    def analyze_single_company(self, siren: str) -> List[Opportunity]:
        """
        Analyse une seule entreprise (helper public)

        Args:
            siren: Numéro SIREN

        Returns:
            Liste d'opportunités
        """
        return self._analyze_company(siren)

    def search_and_analyze(
        self,
        query: str,
        max_companies: int = 5
    ) -> List[Opportunity]:
        """
        Recherche des entreprises et les analyse

        Args:
            query: Terme de recherche
            max_companies: Nombre max d'entreprises à analyser

        Returns:
            Liste d'opportunités
        """
        logger.info(f"Searching and analyzing: {query}")

        # Recherche
        companies = self.pappers.recherche(query, max_results=max_companies)

        opportunities = []

        for company in companies:
            siren = company.get('siren')
            if siren:
                try:
                    opps = self._analyze_company(siren)
                    opportunities.extend(opps)
                except Exception as e:
                    logger.error(f"Error analyzing {siren}: {e}")

        return opportunities
