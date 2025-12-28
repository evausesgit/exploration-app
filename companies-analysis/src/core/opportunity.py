"""
Modèle de données pour représenter une opportunité de trading
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class OpportunityType(Enum):
    """Types d'opportunités"""
    # Crypto
    ARBITRAGE = "arbitrage"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    FUNDING_RATE = "funding_rate"
    LIQUIDATION = "liquidation"

    # Entreprises
    FINANCIAL_GROWTH = "financial_growth"  # Croissance financière
    HIGH_MARGIN = "high_margin"  # Marges élevées
    UNDERVALUED = "undervalued"  # Potentiellement sous-évaluée
    MANAGEMENT_CHANGE = "management_change"  # Changement de direction

    OTHER = "other"


@dataclass
class Opportunity:
    """
    Représente une opportunité de trading détectée

    Attributes:
        opportunity_type: Type d'opportunité
        symbol: Paire de trading (ex: 'BTC/USDT')
        strategy: Nom de la stratégie qui a détecté l'opportunité
        profit_potential: Profit potentiel en % (après fees)
        confidence: Score de confiance (0-100)
        timestamp: Moment de détection
        data: Données spécifiques à la stratégie
        metadata: Informations additionnelles
    """
    opportunity_type: OpportunityType
    symbol: str
    strategy: str
    profit_potential: float  # en %
    confidence: float  # 0-100
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validation des données"""
        if not 0 <= self.confidence <= 100:
            raise ValueError("Confidence must be between 0 and 100")

    def is_profitable(self, min_profit: float = 0.5) -> bool:
        """
        Vérifie si l'opportunité est suffisamment profitable

        Args:
            min_profit: Profit minimum requis en %

        Returns:
            True si profit_potential >= min_profit
        """
        return self.profit_potential >= min_profit

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'opportunité en dictionnaire"""
        return {
            'type': self.opportunity_type.value,
            'symbol': self.symbol,
            'strategy': self.strategy,
            'profit_potential': self.profit_potential,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'metadata': self.metadata
        }

    def __repr__(self) -> str:
        return (
            f"Opportunity({self.opportunity_type.value}, {self.symbol}, "
            f"profit={self.profit_potential:.2f}%, confidence={self.confidence:.0f})"
        )
