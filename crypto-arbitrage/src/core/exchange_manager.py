"""
Gestionnaire d'exchanges pour récupérer les prix et données
"""

import ccxt
from typing import Dict, List, Optional
from loguru import logger
import asyncio


class ExchangeManager:
    """
    Gère les connexions aux exchanges et récupération de données

    Supporte tous les exchanges via CCXT
    """

    def __init__(self, exchange_ids: List[str] = None):
        """
        Initialise les connexions aux exchanges

        Args:
            exchange_ids: Liste des IDs d'exchanges (ex: ['binance', 'kraken'])
        """
        self.exchange_ids = exchange_ids or ['binance', 'kraken', 'coinbase']
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self._initialize_exchanges()

    def _initialize_exchanges(self):
        """Initialise les connexions aux exchanges"""
        for exchange_id in self.exchange_ids:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                self.exchanges[exchange_id] = exchange_class({
                    'enableRateLimit': True,  # Important pour éviter ban
                    'timeout': 30000,
                })
                logger.info(f"Exchange {exchange_id} initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize {exchange_id}: {e}")

    def get_ticker(self, exchange_id: str, symbol: str) -> Optional[dict]:
        """
        Récupère le ticker pour un symbole sur un exchange

        Args:
            exchange_id: ID de l'exchange
            symbol: Symbole (ex: 'BTC/USDT')

        Returns:
            Ticker data ou None si erreur
        """
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                return None

            ticker = exchange.fetch_ticker(symbol)
            return ticker

        except Exception as e:
            logger.debug(f"Error fetching ticker {symbol} from {exchange_id}: {e}")
            return None

    def get_tickers_all_exchanges(self, symbol: str) -> Dict[str, dict]:
        """
        Récupère le ticker pour un symbole sur tous les exchanges

        Args:
            symbol: Symbole (ex: 'BTC/USDT')

        Returns:
            Dict {exchange_id: ticker_data}
        """
        tickers = {}

        for exchange_id, exchange in self.exchanges.items():
            try:
                # Vérifie si le symbole existe sur cet exchange
                if not self._symbol_exists(exchange, symbol):
                    continue

                ticker = exchange.fetch_ticker(symbol)
                tickers[exchange_id] = ticker

            except Exception as e:
                logger.debug(f"Error fetching {symbol} from {exchange_id}: {e}")
                continue

        return tickers

    def _symbol_exists(self, exchange: ccxt.Exchange, symbol: str) -> bool:
        """Vérifie si un symbole existe sur un exchange"""
        try:
            if not hasattr(exchange, 'markets') or not exchange.markets:
                exchange.load_markets()
            return symbol in exchange.markets
        except:
            return False

    def get_orderbook(self, exchange_id: str, symbol: str, limit: int = 5) -> Optional[dict]:
        """
        Récupère l'orderbook pour analyser la liquidité

        Args:
            exchange_id: ID de l'exchange
            symbol: Symbole
            limit: Nombre de niveaux de prix

        Returns:
            Orderbook data ou None
        """
        try:
            exchange = self.exchanges[exchange_id]
            orderbook = exchange.fetch_order_book(symbol, limit)
            return orderbook
        except Exception as e:
            logger.debug(f"Error fetching orderbook {symbol} from {exchange_id}: {e}")
            return None

    def get_trading_fee(self, exchange_id: str, symbol: str = None) -> float:
        """
        Récupère les frais de trading

        Args:
            exchange_id: ID de l'exchange
            symbol: Symbole (optionnel)

        Returns:
            Fee en % (ex: 0.1 pour 0.1%)
        """
        try:
            exchange = self.exchanges[exchange_id]

            # Certains exchanges ont des fees par symbole
            if symbol and hasattr(exchange, 'markets'):
                if not exchange.markets:
                    exchange.load_markets()
                if symbol in exchange.markets:
                    market = exchange.markets[symbol]
                    if 'taker' in market:
                        return market['taker'] * 100

            # Fee par défaut
            if hasattr(exchange, 'fees'):
                return exchange.fees.get('trading', {}).get('taker', 0.001) * 100

            # Fallback
            return 0.1  # 0.1% par défaut

        except Exception as e:
            logger.debug(f"Error getting fees for {exchange_id}: {e}")
            return 0.1

    def get_available_symbols(self, min_exchanges: int = 2) -> List[str]:
        """
        Récupère les symboles disponibles sur au moins X exchanges

        Args:
            min_exchanges: Nombre minimum d'exchanges

        Returns:
            Liste de symboles
        """
        symbols_count = {}

        for exchange_id, exchange in self.exchanges.items():
            try:
                if not exchange.markets:
                    exchange.load_markets()

                for symbol in exchange.markets:
                    symbols_count[symbol] = symbols_count.get(symbol, 0) + 1

            except Exception as e:
                logger.warning(f"Error loading markets for {exchange_id}: {e}")

        # Filtre les symboles présents sur au moins min_exchanges
        available = [
            symbol for symbol, count in symbols_count.items()
            if count >= min_exchanges
        ]

        logger.info(f"Found {len(available)} symbols on {min_exchanges}+ exchanges")
        return available
