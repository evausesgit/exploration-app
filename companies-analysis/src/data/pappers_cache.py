"""
Cache SQLite pour les données Pappers API

Stocke toutes les réponses de l'API pour éviter de redemander des données déjà payées
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from loguru import logger


class PappersCache:
    """
    Cache SQLite pour les données d'entreprises Pappers

    Stocke les réponses complètes de l'API avec timestamp pour éviter
    de consommer inutilement les crédits API
    """

    def __init__(self, cache_dir: str = "data", cache_ttl_days: int = 30):
        """
        Initialise le cache

        Args:
            cache_dir: Répertoire où stocker la base SQLite
            cache_ttl_days: Durée de validité du cache en jours (défaut: 30)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.db_path = self.cache_dir / "pappers_cache.db"
        self.cache_ttl = timedelta(days=cache_ttl_days)

        self._init_db()
        logger.info(f"PappersCache initialized at {self.db_path}")

    def _init_db(self):
        """Crée les tables si elles n'existent pas"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entreprises (
                    siren TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS recherches (
                    query TEXT,
                    departement TEXT,
                    data TEXT NOT NULL,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (query, departement)
                )
            """)

            # Index pour les recherches par date
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entreprises_date
                ON entreprises(fetched_at)
            """)

            conn.commit()

    def get_entreprise(self, siren: str) -> Optional[Dict]:
        """
        Récupère une entreprise du cache

        Args:
            siren: Numéro SIREN

        Returns:
            Données de l'entreprise si en cache et valide, None sinon
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT data, fetched_at
                FROM entreprises
                WHERE siren = ?
            """, (siren,))

            row = cursor.fetchone()

            if row:
                data_json, fetched_at = row
                fetched_date = datetime.fromisoformat(fetched_at)

                # Vérifier si le cache est encore valide
                if datetime.now() - fetched_date < self.cache_ttl:
                    logger.debug(f"Cache HIT for SIREN {siren}")
                    return json.loads(data_json)
                else:
                    logger.debug(f"Cache EXPIRED for SIREN {siren}")
                    # Supprimer l'entrée expirée
                    conn.execute("DELETE FROM entreprises WHERE siren = ?", (siren,))
                    conn.commit()
            else:
                logger.debug(f"Cache MISS for SIREN {siren}")

            return None

    def set_entreprise(self, siren: str, data: Dict):
        """
        Stocke une entreprise dans le cache

        Args:
            siren: Numéro SIREN
            data: Données complètes de l'entreprise
        """
        data_json = json.dumps(data, ensure_ascii=False)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO entreprises (siren, data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (siren, data_json))
            conn.commit()

        logger.debug(f"Cached data for SIREN {siren}")

    def get_recherche(self, query: str, departement: Optional[str] = None) -> Optional[Dict]:
        """
        Récupère les résultats d'une recherche du cache

        Args:
            query: Terme de recherche
            departement: Département (optionnel)

        Returns:
            Résultats de recherche si en cache et valides, None sinon
        """
        dept = departement or ""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT data, fetched_at
                FROM recherches
                WHERE query = ? AND departement = ?
            """, (query, dept))

            row = cursor.fetchone()

            if row:
                data_json, fetched_at = row
                fetched_date = datetime.fromisoformat(fetched_at)

                # Cache de recherche plus court (7 jours)
                if datetime.now() - fetched_date < timedelta(days=7):
                    logger.debug(f"Cache HIT for recherche '{query}'")
                    return json.loads(data_json)
                else:
                    logger.debug(f"Cache EXPIRED for recherche '{query}'")
                    conn.execute("""
                        DELETE FROM recherches
                        WHERE query = ? AND departement = ?
                    """, (query, dept))
                    conn.commit()
            else:
                logger.debug(f"Cache MISS for recherche '{query}'")

            return None

    def set_recherche(self, query: str, data: Dict, departement: Optional[str] = None):
        """
        Stocke les résultats d'une recherche dans le cache

        Args:
            query: Terme de recherche
            data: Résultats de la recherche
            departement: Département (optionnel)
        """
        dept = departement or ""
        data_json = json.dumps(data, ensure_ascii=False)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO recherches (query, departement, data, fetched_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (query, dept, data_json))
            conn.commit()

        logger.debug(f"Cached recherche '{query}'")

    def get_stats(self) -> Dict:
        """
        Récupère les statistiques du cache

        Returns:
            Dict avec nombre d'entreprises et de recherches cachées
        """
        with sqlite3.connect(self.db_path) as conn:
            entreprises_count = conn.execute(
                "SELECT COUNT(*) FROM entreprises"
            ).fetchone()[0]

            recherches_count = conn.execute(
                "SELECT COUNT(*) FROM recherches"
            ).fetchone()[0]

            return {
                'entreprises': entreprises_count,
                'recherches': recherches_count,
                'cache_path': str(self.db_path)
            }

    def clear_expired(self):
        """Supprime les entrées expirées du cache"""
        expiration_date = (datetime.now() - self.cache_ttl).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            deleted_entreprises = conn.execute("""
                DELETE FROM entreprises
                WHERE fetched_at < ?
            """, (expiration_date,)).rowcount

            recherche_expiration = (datetime.now() - timedelta(days=7)).isoformat()
            deleted_recherches = conn.execute("""
                DELETE FROM recherches
                WHERE fetched_at < ?
            """, (recherche_expiration,)).rowcount

            conn.commit()

        logger.info(
            f"Cleared {deleted_entreprises} expired entreprises, "
            f"{deleted_recherches} expired recherches"
        )

    def clear_all(self):
        """Vide complètement le cache (ATTENTION: perte de données)"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM entreprises")
            conn.execute("DELETE FROM recherches")
            conn.commit()

        logger.warning("Cache cleared completely")
