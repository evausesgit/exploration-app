"""
Core framework pour les scanners d'opportunités
"""

from .opportunity import Opportunity, OpportunityType
from .scanner_base import ScannerBase

__all__ = ['Opportunity', 'OpportunityType', 'ScannerBase']
