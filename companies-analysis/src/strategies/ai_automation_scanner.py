"""
Scanner spécialisé pour identifier les entreprises à fort potentiel d'automatisation IA

Critères principaux :
- CA élevé / effectif faible (ratio CA/salarié)
- Secteurs à fort levier IA (conseil, marketing, SaaS, formation, etc.)
- Peu d'actifs physiques
- Services répétables
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional
from loguru import logger

from core.scanner_base import ScannerBase
from core.opportunity import Opportunity, OpportunityType
from data.pappers_client import PappersClient, PappersAPIError


# Secteurs à fort potentiel d'automatisation IA
SECTEURS_PRIORITAIRES = {
    'conseil': [
        'conseil', 'consulting', 'audit', 'accompagnement',
        'stratégie', 'transformation digitale', 'organisation'
    ],
    'marketing_digital': [
        'marketing', 'publicité', 'communication', 'seo', 'sem',
        'social media', 'content', 'influence', 'ads', 'media'
    ],
    'saas_tech': [
        'saas', 'software', 'logiciel', 'plateforme', 'application',
        'cloud', 'api', 'développement'
    ],
    'formation': [
        'formation', 'training', 'coaching', 'enseignement',
        'e-learning', 'éducation', 'pédagogie'
    ],
    'courtage_intermediation': [
        'courtage', 'courtier', 'intermédiaire', 'intermédiation',
        'plateforme', 'marketplace', 'broker'
    ],
    'services_rh': [
        'recrutement', 'rh', 'ressources humaines', 'talent',
        'headhunting', 'staffing', 'interim'
    ],
    'services_financiers': [
        'comptabilité', 'expertise comptable', 'finance', 'gestion',
        'compliance', 'contrôle de gestion', 'audit financier'
    ],
    'services_juridiques': [
        'juridique', 'legal', 'droit', 'avocat', 'notaire',
        'propriété intellectuelle', 'compliance'
    ]
}

# Secteurs à éviter (trop physiques/peu automatisables)
SECTEURS_EXCLUS = [
    'btp', 'construction', 'bâtiment', 'travaux',
    'restauration', 'hôtellerie', 'café', 'bar',
    'industrie', 'fabrication', 'manufacture', 'production',
    'logistique', 'transport', 'livraison', 'entreposage',
    'commerce de détail', 'magasin', 'boutique',
    'agriculture', 'élevage', 'pêche'
]


class AIAutomationScanner(ScannerBase):
    """
    Scanner pour identifier les entreprises à fort potentiel d'automatisation IA

    Utilise des critères sophistiqués pour scorer les entreprises selon :
    - Ratio CA/effectif (proxy d'automatisation)
    - Secteur d'activité (fort levier IA)
    - Rentabilité et stabilité
    - Absence d'actifs physiques lourds
    """

    def __init__(self, config: dict = None):
        """
        Initialise le scanner

        Config attendue:
        - min_ca: CA minimum (défaut: 1000000 = 1M€)
        - max_effectif: Effectif maximum (défaut: 10)
        - min_ca_per_employee: CA/salarié minimum (défaut: 100000 = 100k€)
        - min_age_years: Âge minimum de l'entreprise en années (défaut: 2)
        - secteurs: Liste de secteurs à cibler (optionnel)
        - departements: Liste de départements à cibler (optionnel)
        """
        super().__init__(config)

        # Initialise le client Pappers
        api_key = self.config.get('pappers_api_key')
        try:
            self.pappers = PappersClient(api_key=api_key)
        except ValueError as e:
            logger.error(f"Failed to initialize Pappers client: {e}")
            raise

        # Critères de filtrage
        self.min_ca = self.config.get('min_ca', 1000000)  # 1M€
        self.max_effectif = self.config.get('max_effectif', 10)
        self.min_ca_per_employee = self.config.get('min_ca_per_employee', 100000)  # 100k€
        self.min_age_years = self.config.get('min_age_years', 2)

        # Secteurs et zones
        self.secteurs_cibles = self.config.get('secteurs', list(SECTEURS_PRIORITAIRES.keys()))
        self.departements = self.config.get('departements', None)

    def get_name(self) -> str:
        return "AIAutomationScanner"

    def scan(self) -> List[Opportunity]:
        """
        Scanner principal - recherche par secteurs prioritaires

        Returns:
            Liste d'opportunités d'automatisation détectées
        """
        opportunities = []

        # Si des SIREN sont fournis directement, les analyser
        siren_list = self.config.get('siren_list', [])
        if siren_list:
            logger.info(f"Analyzing {len(siren_list)} companies from SIREN list")
            for siren in siren_list:
                try:
                    company_opps = self._analyze_company(siren)
                    opportunities.extend(company_opps)
                except Exception as e:
                    logger.error(f"Error analyzing SIREN {siren}: {e}")
            return opportunities

        # Sinon, rechercher par secteurs
        logger.info(f"Scanning sectors: {', '.join(self.secteurs_cibles)}")

        for secteur in self.secteurs_cibles:
            try:
                secteur_opps = self._scan_secteur(secteur)
                opportunities.extend(secteur_opps)
            except Exception as e:
                logger.error(f"Error scanning sector {secteur}: {e}")

        return opportunities

    def _scan_secteur(self, secteur: str, max_results: int = 20) -> List[Opportunity]:
        """
        Scanne un secteur spécifique

        Args:
            secteur: Nom du secteur (clé de SECTEURS_PRIORITAIRES)
            max_results: Nombre max de résultats à analyser

        Returns:
            Liste d'opportunités pour ce secteur
        """
        opportunities = []

        # Récupère les mots-clés pour ce secteur
        keywords = SECTEURS_PRIORITAIRES.get(secteur, [secteur])

        logger.info(f"Scanning sector: {secteur}")

        # Recherche avec le premier mot-clé (le plus générique)
        main_keyword = keywords[0] if keywords else secteur

        try:
            # Recherche d'entreprises
            companies = self.pappers.recherche(
                query=main_keyword,
                max_results=max_results,
                departement=self.departements[0] if self.departements else None
            )

            logger.info(f"Found {len(companies)} companies for '{main_keyword}'")

            # Analyser chaque entreprise
            for company in companies:
                siren = company.get('siren')
                if not siren:
                    continue

                try:
                    company_opps = self._analyze_company(siren, secteur)
                    opportunities.extend(company_opps)
                except Exception as e:
                    logger.debug(f"Error analyzing {siren}: {e}")

        except Exception as e:
            logger.error(f"Error searching sector {secteur}: {e}")

        return opportunities

    def _analyze_company(self, siren: str, secteur_hint: str = None) -> List[Opportunity]:
        """
        Analyse une entreprise pour détecter son potentiel d'automatisation

        Args:
            siren: Numéro SIREN
            secteur_hint: Indice sur le secteur (optionnel)

        Returns:
            Liste d'opportunités (vide si ne correspond pas aux critères)
        """
        opportunities = []

        # Récupère les données complètes
        try:
            data = self.pappers.get_entreprise(siren)
        except PappersAPIError as e:
            logger.debug(f"API error for {siren}: {e}")
            return []

        denomination = data.get('nom_entreprise', 'Inconnue')

        # === FILTRES CRITIQUES ===

        # 1. Vérifier le secteur (exclure les secteurs physiques)
        activite = data.get('libelle_code_naf', '').lower()
        objet_social = data.get('objet_social', '').lower()

        # Exclure si dans un secteur à éviter
        for exclus in SECTEURS_EXCLUS:
            if exclus in activite or exclus in objet_social:
                logger.debug(f"Excluded {denomination}: sector {exclus}")
                return []

        # 2. Effectif
        effectif = data.get('effectif', 0)
        if effectif == 0 or effectif > self.max_effectif:
            logger.debug(f"Excluded {denomination}: effectif {effectif}")
            return []

        # 3. Données financières
        finances = data.get('finances', [])
        if not finances:
            logger.debug(f"Excluded {denomination}: no financial data")
            return []

        # Prend le dernier exercice
        dernier_exercice = finances[0]
        ca = dernier_exercice.get('chiffre_affaires')
        resultat = dernier_exercice.get('resultat')

        if ca is None or ca < self.min_ca:
            logger.debug(f"Excluded {denomination}: CA {ca}")
            return []

        # 4. Ratio CA/salarié
        ca_per_employee = ca / effectif if effectif > 0 else 0
        if ca_per_employee < self.min_ca_per_employee:
            logger.debug(f"Excluded {denomination}: CA/employee {ca_per_employee}")
            return []

        # 5. Rentabilité
        if resultat is None or resultat < 0:
            logger.debug(f"Excluded {denomination}: negative result")
            return []

        # 6. Âge de l'entreprise
        date_creation = data.get('date_creation_entreprise', '')
        if date_creation:
            from datetime import datetime
            try:
                creation = datetime.strptime(date_creation, '%Y-%m-%d')
                age_days = (datetime.now() - creation).days
                age_years = age_days / 365.25

                if age_years < self.min_age_years:
                    logger.debug(f"Excluded {denomination}: too young ({age_years:.1f} years)")
                    return []
            except:
                pass

        # === SCORING ===

        score = self._calculate_automation_score(
            ca=ca,
            effectif=effectif,
            resultat=resultat,
            activite=activite,
            objet_social=objet_social,
            data=data
        )

        if score < 50:  # Score minimum
            return []

        # === CRÉATION DE L'OPPORTUNITÉ ===

        logger.info(f"✨ Found automation opportunity: {denomination} (score: {score:.0f}/100)")

        marge = (resultat / ca * 100) if ca > 0 else 0

        # Récupérer les immobilisations pour le recalcul du score
        immobilisations = data.get('finances', [{}])[0].get('immobilisations', 0) or 0

        opportunity = Opportunity(
            opportunity_type=OpportunityType.UNDERVALUED,  # Utilisé pour "high automation potential"
            symbol=siren,
            strategy=self.get_name(),
            profit_potential=ca_per_employee / 1000,  # En k€ (pour comparaison)
            confidence=score,
            data={
                'denomination': denomination,
                'siren': siren,
                'ca': ca,
                'effectif': effectif,
                'ca_per_employee': ca_per_employee,
                'resultat': resultat,
                'marge': marge,
                'activite': activite,
                'objet_social': objet_social[:200],  # Tronqué
                'secteur_hint': secteur_hint,
                'automation_score': score,
                'date_creation': date_creation,
                'ville': data.get('siege', {}).get('ville', 'N/A'),
                'code_postal': data.get('siege', {}).get('code_postal', 'N/A'),
                # Données brutes pour recalcul du score
                'immobilisations': immobilisations
            },
            metadata={
                'type': 'ai_automation',
                'message': f"CA/salarié: {ca_per_employee:,.0f}€ | Score IA: {score:.0f}/100"
            }
        )

        opportunities.append(opportunity)
        return opportunities

    def _calculate_automation_score(
        self,
        ca: float,
        effectif: int,
        resultat: float,
        activite: str,
        objet_social: str,
        data: dict
    ) -> float:
        """
        Calcule un score de potentiel d'automatisation (0-100)

        Critères :
        - Ratio CA/effectif (40 points)
        - Secteur d'activité (30 points)
        - Rentabilité (15 points)
        - Absence d'actifs physiques (15 points)
        """
        score = 0.0

        # 1. Ratio CA/effectif (40 points max)
        ca_per_employee = ca / effectif if effectif > 0 else 0
        if ca_per_employee >= 500000:  # 500k€+
            score += 40
        elif ca_per_employee >= 300000:  # 300k€+
            score += 35
        elif ca_per_employee >= 200000:  # 200k€+
            score += 30
        elif ca_per_employee >= 150000:  # 150k€+
            score += 25
        elif ca_per_employee >= 100000:  # 100k€+
            score += 20
        else:
            score += 10

        # 2. Secteur d'activité (30 points max)
        texte_complet = f"{activite} {objet_social}".lower()

        # Bonus si dans un secteur prioritaire
        secteur_matches = 0
        for secteur, keywords in SECTEURS_PRIORITAIRES.items():
            for keyword in keywords:
                if keyword in texte_complet:
                    secteur_matches += 1
                    break

        if secteur_matches >= 3:
            score += 30
        elif secteur_matches >= 2:
            score += 25
        elif secteur_matches >= 1:
            score += 20
        else:
            score += 10

        # 3. Rentabilité (15 points max)
        marge = (resultat / ca * 100) if ca > 0 else 0
        if marge >= 30:
            score += 15
        elif marge >= 20:
            score += 12
        elif marge >= 10:
            score += 9
        elif marge >= 5:
            score += 6
        else:
            score += 3

        # 4. Absence d'actifs physiques (15 points max)
        # Indicateurs : peu d'immobilisations, activité de service
        immobilisations = data.get('finances', [{}])[0].get('immobilisations', 0) or 0

        if immobilisations == 0:
            score += 15
        elif immobilisations < ca * 0.1:  # Moins de 10% du CA
            score += 12
        elif immobilisations < ca * 0.3:  # Moins de 30% du CA
            score += 8
        else:
            score += 3

        # Bonus si mots-clés de services immatériels
        service_keywords = ['conseil', 'formation', 'digital', 'logiciel', 'plateforme', 'saas']
        for keyword in service_keywords:
            if keyword in texte_complet:
                score += 2
                break

        return min(100, score)  # Cap à 100

    def search_by_sector(self, secteur: str, max_companies: int = 20) -> List[Opportunity]:
        """
        Recherche publique par secteur (helper)

        Args:
            secteur: Nom du secteur ou mot-clé
            max_companies: Nombre max d'entreprises à analyser

        Returns:
            Liste d'opportunités
        """
        return self._scan_secteur(secteur, max_results=max_companies)
