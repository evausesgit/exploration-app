"""
Tests basiques pour valider le scanner
"""

import pytest
from src.core.opportunity import Opportunity, OpportunityType
from src.strategies.arbitrage import CryptoArbitrageScanner


def test_opportunity_creation():
    """Test de création d'une opportunité"""
    opp = Opportunity(
        opportunity_type=OpportunityType.ARBITRAGE,
        symbol="BTC/USDT",
        strategy="Test Scanner",
        profit_potential=1.5,
        confidence=75.0,
        data={
            'buy_exchange': 'binance',
            'sell_exchange': 'kraken',
            'buy_price': 50000.0,
            'sell_price': 50750.0
        }
    )

    assert opp.symbol == "BTC/USDT"
    assert opp.profit_potential == 1.5
    assert opp.is_profitable(min_profit=1.0)
    assert not opp.is_profitable(min_profit=2.0)


def test_opportunity_validation():
    """Test de validation des données"""
    # Confiance invalide
    with pytest.raises(ValueError):
        Opportunity(
            opportunity_type=OpportunityType.ARBITRAGE,
            symbol="BTC/USDT",
            strategy="Test",
            profit_potential=1.0,
            confidence=150  # > 100
        )


def test_scanner_initialization():
    """Test d'initialisation du scanner"""
    config = {
        'exchanges': ['binance', 'kraken'],
        'symbols': ['BTC/USDT', 'ETH/USDT'],
        'min_profit': 0.5,
        'min_confidence': 50
    }

    scanner = CryptoArbitrageScanner(config)

    assert scanner.get_name() == "Crypto Arbitrage Scanner"
    assert scanner.get_config('min_profit') == 0.5


def test_opportunity_to_dict():
    """Test de conversion en dictionnaire"""
    opp = Opportunity(
        opportunity_type=OpportunityType.ARBITRAGE,
        symbol="ETH/USDT",
        strategy="Test",
        profit_potential=2.0,
        confidence=80.0
    )

    data = opp.to_dict()

    assert data['symbol'] == "ETH/USDT"
    assert data['type'] == "arbitrage"
    assert data['profit_potential'] == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
