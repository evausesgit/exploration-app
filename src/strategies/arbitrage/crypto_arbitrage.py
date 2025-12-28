"""
Scanner d'arbitrage crypto entre exchanges
Détecte les différences de prix exploitables
"""

from typing import List, Dict, Tuple
from loguru import logger
from itertools import combinations

from src.core.scanner_base import ScannerBase
from src.core.opportunity import Opportunity, OpportunityType
from src.core.exchange_manager import ExchangeManager


class CryptoArbitrageScanner(ScannerBase):
    """
    Scanne les opportunités d'arbitrage entre exchanges crypto

    Détecte:
    - Différences de prix entre exchanges
    - Calcule profit net après fees
    - Vérifie liquidité minimale
    """

    def __init__(self, config: dict = None):
        """
        Initialise le scanner d'arbitrage

        Config attendue:
            - exchanges: Liste d'exchanges à scanner (default: binance, kraken, coinbase)
            - symbols: Liste de symboles à scanner (default: majors)
            - min_profit: Profit minimum en % (default: 0.5%)
            - min_volume_24h: Volume minimum 24h en USD (default: 1M)
            - include_withdrawal_fee: Inclure frais de retrait (default: True)
        """
        super().__init__(config)

        # Paramètres
        exchanges = self.get_config('exchanges', ['binance', 'kraken', 'coinbase'])
        self.symbols = self.get_config('symbols', self._get_default_symbols())
        self.min_volume_24h = self.get_config('min_volume_24h', 1000000)  # 1M USD
        self.include_withdrawal_fee = self.get_config('include_withdrawal_fee', True)

        # Initialise le gestionnaire d'exchanges
        self.exchange_manager = ExchangeManager(exchanges)

        logger.info(
            f"CryptoArbitrageScanner initialized: "
            f"{len(exchanges)} exchanges, {len(self.symbols)} symbols"
        )

    def _get_default_symbols(self) -> List[str]:
        """Symboles majeurs par défaut"""
        return [
            'BTC/USDT',
            'ETH/USDT',
            'BNB/USDT',
            'SOL/USDT',
            'XRP/USDT',
            'ADA/USDT',
            'AVAX/USDT',
            'DOT/USDT',
            'MATIC/USDT',
            'LINK/USDT'
        ]

    def get_name(self) -> str:
        return "Crypto Arbitrage Scanner"

    def scan(self) -> List[Opportunity]:
        """
        Scanne toutes les paires sur tous les exchanges pour trouver des arbitrages

        Returns:
            Liste d'opportunités d'arbitrage
        """
        opportunities = []

        for symbol in self.symbols:
            # Récupère les prix sur tous les exchanges
            tickers = self.exchange_manager.get_tickers_all_exchanges(symbol)

            if len(tickers) < 2:
                logger.debug(f"Symbol {symbol} available on <2 exchanges, skipping")
                continue

            # Vérifie volume minimum
            if not self._check_volume(tickers):
                continue

            # Trouve les opportunités d'arbitrage pour ce symbole
            symbol_opportunities = self._find_arbitrage_opportunities(symbol, tickers)
            opportunities.extend(symbol_opportunities)

        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        return opportunities

    def _check_volume(self, tickers: Dict[str, dict]) -> bool:
        """
        Vérifie que le volume 24h est suffisant

        Args:
            tickers: Dict des tickers par exchange

        Returns:
            True si volume OK
        """
        for ticker in tickers.values():
            volume_usd = ticker.get('quoteVolume', 0) or 0
            if volume_usd >= self.min_volume_24h:
                return True
        return False

    def _find_arbitrage_opportunities(
        self,
        symbol: str,
        tickers: Dict[str, dict]
    ) -> List[Opportunity]:
        """
        Trouve les opportunités d'arbitrage pour un symbole

        Args:
            symbol: Symbole à analyser
            tickers: Tickers de tous les exchanges

        Returns:
            Liste d'opportunités
        """
        opportunities = []

        # Compare toutes les paires d'exchanges
        exchange_pairs = list(combinations(tickers.keys(), 2))

        for exchange_buy, exchange_sell in exchange_pairs:
            ticker_buy = tickers[exchange_buy]
            ticker_sell = tickers[exchange_sell]

            # Prix d'achat (ask) et de vente (bid)
            price_buy = ticker_buy.get('ask') or ticker_buy.get('last') or 0
            price_sell = ticker_sell.get('bid') or ticker_sell.get('last') or 0

            if not price_buy or not price_sell or price_buy <= 0 or price_sell <= 0:
                continue

            # Calcule le profit potentiel
            profit_data = self._calculate_profit(
                symbol,
                exchange_buy,
                exchange_sell,
                price_buy,
                price_sell
            )

            if profit_data['net_profit_pct'] > 0:
                # Crée l'opportunité
                opportunity = Opportunity(
                    opportunity_type=OpportunityType.ARBITRAGE,
                    symbol=symbol,
                    strategy=self.get_name(),
                    profit_potential=profit_data['net_profit_pct'],
                    confidence=self._calculate_confidence(profit_data, ticker_buy, ticker_sell),
                    data={
                        'buy_exchange': exchange_buy,
                        'sell_exchange': exchange_sell,
                        'buy_price': price_buy,
                        'sell_price': price_sell,
                        'spread_pct': profit_data['spread_pct'],
                        'total_fees_pct': profit_data['total_fees_pct'],
                        'net_profit_pct': profit_data['net_profit_pct'],
                    },
                    metadata={
                        'volume_24h_buy': ticker_buy.get('quoteVolume', 0),
                        'volume_24h_sell': ticker_sell.get('quoteVolume', 0),
                    }
                )
                opportunities.append(opportunity)

        return opportunities

    def _calculate_profit(
        self,
        symbol: str,
        exchange_buy: str,
        exchange_sell: str,
        price_buy: float,
        price_sell: float
    ) -> Dict[str, float]:
        """
        Calcule le profit net après fees

        Args:
            symbol: Symbole
            exchange_buy: Exchange d'achat
            exchange_sell: Exchange de vente
            price_buy: Prix d'achat
            price_sell: Prix de vente

        Returns:
            Dict avec spread, fees, et profit net
        """
        # Spread brut
        spread_pct = ((price_sell - price_buy) / price_buy) * 100

        # Fees de trading
        fee_buy = self.exchange_manager.get_trading_fee(exchange_buy, symbol)
        fee_sell = self.exchange_manager.get_trading_fee(exchange_sell, symbol)

        # Fees de retrait (estimation conservative)
        withdrawal_fee_pct = 0.1 if self.include_withdrawal_fee else 0

        total_fees_pct = fee_buy + fee_sell + withdrawal_fee_pct

        # Profit net
        net_profit_pct = spread_pct - total_fees_pct

        return {
            'spread_pct': spread_pct,
            'fee_buy_pct': fee_buy,
            'fee_sell_pct': fee_sell,
            'withdrawal_fee_pct': withdrawal_fee_pct,
            'total_fees_pct': total_fees_pct,
            'net_profit_pct': net_profit_pct
        }

    def _calculate_confidence(
        self,
        profit_data: dict,
        ticker_buy: dict,
        ticker_sell: dict
    ) -> float:
        """
        Calcule un score de confiance pour l'opportunité

        Facteurs:
        - Profit net (plus = mieux)
        - Volume (plus = mieux)
        - Spread bid-ask (moins = mieux)

        Returns:
            Score 0-100
        """
        confidence = 50  # Base

        # Bonus pour profit élevé
        net_profit = profit_data['net_profit_pct']
        if net_profit > 2:
            confidence += 20
        elif net_profit > 1:
            confidence += 10
        elif net_profit > 0.5:
            confidence += 5

        # Bonus pour volume élevé
        volume_buy = ticker_buy.get('quoteVolume', 0)
        volume_sell = ticker_sell.get('quoteVolume', 0)
        avg_volume = (volume_buy + volume_sell) / 2

        if avg_volume > 10000000:  # >10M
            confidence += 15
        elif avg_volume > 5000000:  # >5M
            confidence += 10
        elif avg_volume > 1000000:  # >1M
            confidence += 5

        # Pénalité si spread trop large (peut indiquer illiquidité)
        if profit_data['spread_pct'] > 5:
            confidence -= 10

        return max(0, min(100, confidence))
