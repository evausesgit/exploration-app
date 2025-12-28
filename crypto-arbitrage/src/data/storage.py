"""
Stockage des opportunités détectées
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from loguru import logger

from src.core.opportunity import Opportunity, OpportunityType


class OpportunityStorage:
    """
    Stocke les opportunités dans une base SQLite

    Permet:
    - Sauvegarde des opportunités
    - Requêtes historiques
    - Analyses de patterns
    """

    def __init__(self, db_path: str = "data/opportunities.db"):
        """
        Initialise le stockage

        Args:
            db_path: Chemin vers la base SQLite
        """
        self.db_path = db_path

        # Crée le dossier si nécessaire
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialise la DB
        self._init_db()

        logger.info(f"OpportunityStorage initialized: {db_path}")

    def _init_db(self):
        """Crée les tables si elles n'existent pas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                opportunity_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                profit_potential REAL NOT NULL,
                confidence REAL NOT NULL,
                data TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
        ''')

        # Index pour requêtes rapides
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON opportunities(timestamp DESC)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_symbol
            ON opportunities(symbol)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_profit
            ON opportunities(profit_potential DESC)
        ''')

        conn.commit()
        conn.close()

    def save(self, opportunity: Opportunity):
        """
        Sauvegarde une opportunité

        Args:
            opportunity: Opportunité à sauvegarder
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO opportunities
            (timestamp, opportunity_type, symbol, strategy, profit_potential, confidence, data, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            opportunity.timestamp.isoformat(),
            opportunity.opportunity_type.value,
            opportunity.symbol,
            opportunity.strategy,
            opportunity.profit_potential,
            opportunity.confidence,
            json.dumps(opportunity.data),
            json.dumps(opportunity.metadata)
        ))

        conn.commit()
        conn.close()

    def save_batch(self, opportunities: List[Opportunity]):
        """
        Sauvegarde plusieurs opportunités en batch

        Args:
            opportunities: Liste d'opportunités
        """
        if not opportunities:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = [
            (
                opp.timestamp.isoformat(),
                opp.opportunity_type.value,
                opp.symbol,
                opp.strategy,
                opp.profit_potential,
                opp.confidence,
                json.dumps(opp.data),
                json.dumps(opp.metadata)
            )
            for opp in opportunities
        ]

        cursor.executemany('''
            INSERT INTO opportunities
            (timestamp, opportunity_type, symbol, strategy, profit_potential, confidence, data, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

        conn.commit()
        conn.close()

        logger.info(f"Saved {len(opportunities)} opportunities to database")

    def get_recent(self, limit: int = 100) -> List[dict]:
        """
        Récupère les opportunités récentes

        Args:
            limit: Nombre max d'opportunités

        Returns:
            Liste de dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM opportunities
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_by_symbol(self, symbol: str, limit: int = 50) -> List[dict]:
        """
        Récupère les opportunités pour un symbole

        Args:
            symbol: Symbole (ex: 'BTC/USDT')
            limit: Nombre max

        Returns:
            Liste de dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM opportunities
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (symbol, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_best_opportunities(
        self,
        min_profit: float = 1.0,
        min_confidence: float = 60,
        limit: int = 50
    ) -> List[dict]:
        """
        Récupère les meilleures opportunités

        Args:
            min_profit: Profit minimum en %
            min_confidence: Confiance minimum
            limit: Nombre max

        Returns:
            Liste de dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM opportunities
            WHERE profit_potential >= ?
            AND confidence >= ?
            ORDER BY profit_potential DESC, confidence DESC
            LIMIT ?
        ''', (min_profit, min_confidence, limit))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_statistics(self) -> dict:
        """
        Calcule des statistiques sur les opportunités

        Returns:
            Dict de statistiques
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total
        cursor.execute('SELECT COUNT(*) FROM opportunities')
        total = cursor.fetchone()[0]

        # Profit moyen
        cursor.execute('SELECT AVG(profit_potential) FROM opportunities')
        avg_profit = cursor.fetchone()[0] or 0

        # Par symbole
        cursor.execute('''
            SELECT symbol, COUNT(*) as count
            FROM opportunities
            GROUP BY symbol
            ORDER BY count DESC
            LIMIT 10
        ''')
        top_symbols = cursor.fetchall()

        # Par stratégie
        cursor.execute('''
            SELECT strategy, COUNT(*) as count
            FROM opportunities
            GROUP BY strategy
        ''')
        by_strategy = cursor.fetchall()

        conn.close()

        return {
            'total_opportunities': total,
            'average_profit': avg_profit,
            'top_symbols': [{'symbol': s[0], 'count': s[1]} for s in top_symbols],
            'by_strategy': [{'strategy': s[0], 'count': s[1]} for s in by_strategy]
        }
