"""
Classe abstraite de base pour tous les scanners de stratégies
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from loguru import logger
import time

from .opportunity import Opportunity


class ScannerBase(ABC):
    """
    Classe de base pour tous les scanners d'opportunités

    Chaque stratégie doit hériter de cette classe et implémenter:
    - scan(): logique de détection
    - get_name(): nom de la stratégie
    """

    def __init__(self, config: dict = None):
        """
        Initialise le scanner

        Args:
            config: Configuration spécifique à la stratégie
        """
        self.config = config or {}
        self.is_running = False
        self.last_scan_time = None
        self.opportunities_found = []

        logger.info(f"Scanner {self.get_name()} initialized")

    @abstractmethod
    def scan(self) -> List[Opportunity]:
        """
        Scanne le marché et retourne les opportunités détectées

        Returns:
            Liste d'opportunités trouvées
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Retourne le nom de la stratégie

        Returns:
            Nom du scanner
        """
        pass

    def run_scan(self) -> List[Opportunity]:
        """
        Execute un scan avec gestion d'erreurs et logging

        Returns:
            Liste d'opportunités trouvées
        """
        try:
            logger.info(f"Starting scan: {self.get_name()}")
            start_time = time.time()

            opportunities = self.scan()

            elapsed = time.time() - start_time
            self.last_scan_time = time.time()

            logger.info(
                f"Scan completed: {self.get_name()} - "
                f"Found {len(opportunities)} opportunities in {elapsed:.2f}s"
            )

            # Filtre les opportunités selon config
            opportunities = self._filter_opportunities(opportunities)

            self.opportunities_found = opportunities
            return opportunities

        except Exception as e:
            logger.error(f"Error during scan {self.get_name()}: {str(e)}")
            return []

    def _filter_opportunities(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """
        Filtre les opportunités selon la configuration

        Args:
            opportunities: Liste d'opportunités brutes

        Returns:
            Liste d'opportunités filtrées
        """
        min_profit = self.config.get('min_profit', 0.5)
        min_confidence = self.config.get('min_confidence', 50)

        filtered = [
            opp for opp in opportunities
            if opp.profit_potential >= min_profit
            and opp.confidence >= min_confidence
        ]

        if len(filtered) < len(opportunities):
            logger.debug(
                f"Filtered {len(opportunities) - len(filtered)} opportunities "
                f"(min_profit={min_profit}%, min_confidence={min_confidence})"
            )

        return filtered

    def get_config(self, key: str, default=None):
        """Helper pour récupérer une config"""
        return self.config.get(key, default)

    def validate_config(self, required_keys: List[str]) -> bool:
        """
        Valide que les clés requises sont présentes dans la config

        Args:
            required_keys: Liste des clés requises

        Returns:
            True si toutes les clés sont présentes
        """
        missing = [key for key in required_keys if key not in self.config]
        if missing:
            logger.warning(f"Missing config keys for {self.get_name()}: {missing}")
            return False
        return True
