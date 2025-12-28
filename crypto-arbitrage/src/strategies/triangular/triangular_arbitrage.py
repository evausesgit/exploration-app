"""
Scanner d'arbitrage triangulaire
Détecte les opportunités d'arbitrage en effectuant 3 trades sur un même exchange

Exemple:
    USDT → BTC → ETH → USDT (profit si taux favorables)
"""

from typing import List, Dict, Tuple, Set
from loguru import logger
from itertools import combinations

from src.core.scanner_base import ScannerBase
from src.core.opportunity import Opportunity, OpportunityType
from src.core.exchange_manager import ExchangeManager


class TriangularArbitrageScanner(ScannerBase):
    """
    Scanne les opportunités d'arbitrage triangulaire sur un exchange

    L'arbitrage triangulaire exploite les inefficiences de prix entre 3 paires:
    - BTC/USDT: 50000
    - ETH/BTC: 0.06
    - ETH/USDT: 3100

    Si 50000 * 0.06 = 3000 < 3100, il y a une opportunité:
    1000 USDT → BTC → ETH → 1033 USDT (3.3% profit)
    """

    def __init__(self, config: dict = None):
        """
        Initialise le scanner d'arbitrage triangulaire

        Config attendue:
            - exchange: Exchange à scanner (default: binance)
            - base_currencies: Devises de base (default: USDT, BTC, ETH)
            - min_profit: Profit minimum en % (default: 0.5%)
            - min_volume_24h: Volume minimum 24h en USD (default: 500k)
        """
        super().__init__(config)

        # Paramètres
        self.exchange_name = self.get_config('exchange', 'binance')
        self.base_currencies = self.get_config('base_currencies', ['USDT', 'BTC', 'ETH', 'BNB'])
        self.min_volume_24h = self.get_config('min_volume_24h', 500000)

        # Initialise le gestionnaire d'exchanges
        self.exchange_manager = ExchangeManager([self.exchange_name])

        # Cache pour les symboles disponibles
        self.available_symbols = None
        self.triangles = []

        logger.info(
            f"TriangularArbitrageScanner initialized: "
            f"{self.exchange_name}, base currencies: {self.base_currencies}"
        )

    def get_name(self) -> str:
        return "Triangular Arbitrage Scanner"

    def scan(self) -> List[Opportunity]:
        """
        Scanne toutes les combinaisons triangulaires possibles

        Returns:
            Liste d'opportunités d'arbitrage triangulaire
        """
        opportunities = []

        # Charge les symboles disponibles
        if not self.available_symbols:
            self._load_available_symbols()

        # Trouve les triangles possibles
        if not self.triangles:
            self._find_triangles()

        logger.info(f"Scanning {len(self.triangles)} triangular paths on {self.exchange_name}")

        # Scanne chaque triangle
        for triangle in self.triangles:
            opp = self._scan_triangle(triangle)
            if opp:
                opportunities.append(opp)

        logger.info(f"Found {len(opportunities)} triangular arbitrage opportunities")
        return opportunities

    def _load_available_symbols(self):
        """Charge tous les symboles disponibles sur l'exchange"""
        try:
            exchange = self.exchange_manager.exchanges[self.exchange_name]
            if not exchange.markets:
                exchange.load_markets()

            self.available_symbols = set(exchange.markets.keys())
            logger.info(f"Loaded {len(self.available_symbols)} symbols from {self.exchange_name}")
        except Exception as e:
            logger.error(f"Error loading symbols: {e}")
            self.available_symbols = set()

    def _find_triangles(self):
        """
        Trouve toutes les combinaisons triangulaires possibles

        Un triangle valide:
        - A/B, B/C, A/C doivent tous exister
        - Example: BTC/USDT, ETH/BTC, ETH/USDT
        """
        triangles = []

        # Pour chaque devise de base
        for base in self.base_currencies:
            # Trouve toutes les paires avec cette base
            pairs_with_base = [
                s for s in self.available_symbols
                if s.endswith(f'/{base}')
            ]

            # Pour chaque paire de paires
            for pair1, pair2 in combinations(pairs_with_base, 2):
                # Extrait les devises
                curr1 = pair1.split('/')[0]  # Ex: BTC de BTC/USDT
                curr2 = pair2.split('/')[0]  # Ex: ETH de ETH/USDT

                # Vérifie si la paire intermédiaire existe
                intermediate = f"{curr2}/{curr1}"  # Ex: ETH/BTC
                reverse_intermediate = f"{curr1}/{curr2}"  # Ex: BTC/ETH

                if intermediate in self.available_symbols:
                    triangles.append({
                        'path': [pair1, intermediate, pair2],
                        'currencies': [base, curr1, curr2, base],
                        'direction': 'forward'
                    })
                elif reverse_intermediate in self.available_symbols:
                    triangles.append({
                        'path': [pair1, reverse_intermediate, pair2],
                        'currencies': [base, curr1, curr2, base],
                        'direction': 'reverse'
                    })

        self.triangles = triangles
        logger.info(f"Found {len(triangles)} possible triangular paths")

    def _scan_triangle(self, triangle: dict) -> Opportunity:
        """
        Scanne un triangle spécifique pour détecter une opportunité

        Args:
            triangle: Dict avec path et currencies

        Returns:
            Opportunity si trouvée, None sinon
        """
        try:
            path = triangle['path']
            currencies = triangle['currencies']

            # Récupère les tickers
            tickers = {}
            for symbol in path:
                ticker = self.exchange_manager.get_ticker(self.exchange_name, symbol)
                if not ticker:
                    return None
                tickers[symbol] = ticker

            # Vérifie le volume minimum
            if not self._check_volume(tickers):
                return None

            # Calcule le profit potentiel
            profit_data = self._calculate_triangular_profit(path, tickers, triangle['direction'])

            if profit_data['net_profit_pct'] > 0:
                # Crée l'opportunité
                opportunity = Opportunity(
                    opportunity_type=OpportunityType.TRIANGULAR_ARBITRAGE,
                    symbol=' → '.join(path),
                    strategy=self.get_name(),
                    profit_potential=profit_data['net_profit_pct'],
                    confidence=self._calculate_confidence(profit_data, tickers),
                    data={
                        'exchange': self.exchange_name,
                        'path': path,
                        'currencies': currencies,
                        'prices': profit_data['prices'],
                        'gross_profit_pct': profit_data['gross_profit_pct'],
                        'total_fees_pct': profit_data['total_fees_pct'],
                        'net_profit_pct': profit_data['net_profit_pct'],
                        'final_amount': profit_data['final_amount'],
                    },
                    metadata={
                        'direction': triangle['direction'],
                        'volumes': {s: t.get('quoteVolume', 0) for s, t in tickers.items()}
                    }
                )
                return opportunity

        except Exception as e:
            logger.debug(f"Error scanning triangle {triangle['path']}: {e}")

        return None

    def _calculate_triangular_profit(
        self,
        path: List[str],
        tickers: Dict[str, dict],
        direction: str
    ) -> Dict[str, float]:
        """
        Calcule le profit d'un arbitrage triangulaire

        Args:
            path: Liste des 3 symboles
            tickers: Tickers pour chaque symbole
            direction: 'forward' ou 'reverse'

        Returns:
            Dict avec profit brut, fees, et profit net
        """
        start_amount = 1000.0  # Simulation avec 1000 unités de base
        current_amount = start_amount

        prices = []
        total_fees_pct = 0.0

        # Simule les 3 trades
        for i, symbol in enumerate(path):
            ticker = tickers[symbol]

            # Détermine si on achète ou vend
            # Pour un triangle USDT → BTC → ETH → USDT:
            # Trade 1: Acheter BTC/USDT (ask)
            # Trade 2: Acheter ETH/BTC (ask)
            # Trade 3: Vendre ETH/USDT (bid)

            if i < 2:  # Premiers trades: achats
                price = ticker.get('ask', ticker.get('last', 0))
                current_amount = current_amount / price if price > 0 else 0
            else:  # Dernier trade: vente
                price = ticker.get('bid', ticker.get('last', 0))
                current_amount = current_amount * price

            prices.append(price)

            # Ajoute les fees de trading (taker fee ~0.1%)
            fee_pct = self.exchange_manager.get_trading_fee(self.exchange_name, symbol)
            total_fees_pct += fee_pct
            current_amount *= (1 - fee_pct / 100)

        # Calcule le profit
        gross_profit_pct = ((current_amount - start_amount) / start_amount) * 100
        net_profit_pct = gross_profit_pct - total_fees_pct

        return {
            'prices': prices,
            'gross_profit_pct': gross_profit_pct,
            'total_fees_pct': total_fees_pct,
            'net_profit_pct': net_profit_pct,
            'final_amount': current_amount,
            'start_amount': start_amount
        }

    def _check_volume(self, tickers: Dict[str, dict]) -> bool:
        """
        Vérifie que le volume 24h est suffisant sur toutes les paires

        Args:
            tickers: Dict des tickers

        Returns:
            True si volume OK
        """
        for ticker in tickers.values():
            volume_usd = ticker.get('quoteVolume', 0)
            if volume_usd < self.min_volume_24h:
                return False
        return True

    def _calculate_confidence(
        self,
        profit_data: dict,
        tickers: Dict[str, dict]
    ) -> float:
        """
        Calcule un score de confiance pour l'opportunité

        Returns:
            Score 0-100
        """
        confidence = 50  # Base

        # Bonus pour profit élevé
        net_profit = profit_data['net_profit_pct']
        if net_profit > 2:
            confidence += 20
        elif net_profit > 1:
            confidence += 15
        elif net_profit > 0.5:
            confidence += 10
        elif net_profit > 0.3:
            confidence += 5

        # Bonus pour volume élevé (plus liquide)
        avg_volume = sum(t.get('quoteVolume', 0) for t in tickers.values()) / len(tickers)
        if avg_volume > 5000000:  # >5M
            confidence += 15
        elif avg_volume > 1000000:  # >1M
            confidence += 10
        elif avg_volume > 500000:  # >500k
            confidence += 5

        # Pénalité si profit très faible (risque slippage)
        if net_profit < 0.5:
            confidence -= 10

        return max(0, min(100, confidence))
