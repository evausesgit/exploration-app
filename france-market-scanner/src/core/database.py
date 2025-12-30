"""DuckDB database manager with schema initialization."""
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
import duckdb
from loguru import logger


class DatabaseManager:
    """Manage DuckDB connection and schema operations."""

    def __init__(
        self,
        db_path: str | Path = "data/france_companies.duckdb",
        memory_limit: str = "4GB",
        threads: int = 4,
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_limit = memory_limit
        self.threads = threads
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = duckdb.connect(str(self.db_path))
            self._conn.execute(f"SET memory_limit = '{self.memory_limit}'")
            self._conn.execute(f"SET threads = {self.threads}")
            # Optimize for large bulk inserts
            self._conn.execute("SET preserve_insertion_order = false")
            logger.info(f"Connected to DuckDB: {self.db_path}")
        return self._conn

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def init_schema(self, force: bool = False) -> None:
        """Initialize database schema.

        Args:
            force: If True, drop existing tables before creating.
        """
        if force:
            logger.warning("Force mode: dropping existing tables")
            self._drop_tables()

        self._create_sirene_tables()
        self._create_inpi_tables()
        self._create_bodacc_tables()
        self._create_etl_tables()
        self._create_views()

        logger.info("Database schema initialized successfully")

    def _drop_tables(self) -> None:
        """Drop all existing tables."""
        tables = [
            "v_company_overview",  # Views first
            "bodacc_annonces",
            "inpi_compte_resultat",
            "inpi_bilan",
            "inpi_comptes_annuels",
            "sirene_etablissements",
            "sirene_unites_legales",
            "etl_loads",
            "etl_downloads",
        ]
        for table in tables:
            try:
                self.conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                self.conn.execute(f"DROP VIEW IF EXISTS {table} CASCADE")
            except Exception:
                pass

    def _create_sirene_tables(self) -> None:
        """Create SIRENE tables for legal units and establishments."""
        # Legal units (entreprises) - ~12M rows
        # Note: No PRIMARY KEY because file contains historical periods (duplicates)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sirene_unites_legales (
                siren VARCHAR(9) NOT NULL,

                -- Identification
                statut_diffusion VARCHAR(1),
                date_creation DATE,
                sigle VARCHAR(20),

                -- Denomination
                denomination VARCHAR(200),
                denomination_usuelle_1 VARCHAR(70),
                denomination_usuelle_2 VARCHAR(70),
                denomination_usuelle_3 VARCHAR(70),

                -- Physical person (if applicable)
                prenom VARCHAR(50),
                nom VARCHAR(100),

                -- Legal form
                categorie_juridique VARCHAR(4),

                -- Activity
                activite_principale VARCHAR(6),
                nomenclature_activite VARCHAR(8),

                -- Size
                tranche_effectifs VARCHAR(2),
                annee_effectifs INTEGER,
                caractere_employeur VARCHAR(1),

                -- Category
                categorie_entreprise VARCHAR(10),
                annee_categorie_entreprise INTEGER,

                -- Economy
                economie_sociale_solidaire VARCHAR(1),
                societe_mission VARCHAR(1),

                -- Status
                etat_administratif VARCHAR(1),
                date_cessation DATE,

                -- Timestamps
                date_derniere_mise_a_jour TIMESTAMP,

                -- ETL metadata
                _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                _source_file VARCHAR(200)
            )
        """)
        logger.debug("Created table: sirene_unites_legales")

        # Establishments (établissements) - ~30M rows
        # Note: No PRIMARY KEY because file contains historical periods (duplicates)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sirene_etablissements (
                siret VARCHAR(14) NOT NULL,
                siren VARCHAR(9) NOT NULL,
                nic VARCHAR(5) NOT NULL,

                -- Identification
                statut_diffusion VARCHAR(1),
                date_creation DATE,

                -- Denomination
                denomination_usuelle VARCHAR(100),
                enseigne_1 VARCHAR(50),
                enseigne_2 VARCHAR(50),
                enseigne_3 VARCHAR(50),

                -- Activity
                activite_principale VARCHAR(6),
                nomenclature_activite VARCHAR(8),
                activite_principale_registre_metiers VARCHAR(6),

                -- Type
                etablissement_siege VARCHAR(5),

                -- Size
                tranche_effectifs VARCHAR(2),
                annee_effectifs INTEGER,
                caractere_employeur VARCHAR(1),

                -- Address
                complement_adresse VARCHAR(200),
                numero_voie VARCHAR(10),
                indice_repetition VARCHAR(5),
                type_voie VARCHAR(10),
                libelle_voie VARCHAR(200),
                code_postal VARCHAR(5),
                libelle_commune VARCHAR(100),
                libelle_commune_etranger VARCHAR(100),
                code_commune VARCHAR(5),
                code_cedex VARCHAR(10),
                libelle_cedex VARCHAR(100),
                code_pays_etranger VARCHAR(5),
                libelle_pays_etranger VARCHAR(100),

                -- Geo (derived)
                departement VARCHAR(3),
                region VARCHAR(3),

                -- Status
                etat_administratif VARCHAR(1),
                date_cessation DATE,

                -- Timestamps
                date_derniere_mise_a_jour TIMESTAMP,

                -- ETL metadata
                _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                _source_file VARCHAR(200)
            )
        """)
        logger.debug("Created table: sirene_etablissements")

    def _create_inpi_tables(self) -> None:
        """Create INPI tables for annual accounts."""
        # Annual accounts metadata
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS inpi_comptes_annuels (
                id VARCHAR(100) PRIMARY KEY,
                siren VARCHAR(9) NOT NULL,

                -- Exercise period
                date_cloture DATE,
                duree_exercice INTEGER,
                annee_cloture INTEGER,

                -- Document info
                code_greffe VARCHAR(10),
                num_depot VARCHAR(50),
                date_depot DATE,

                -- Type and confidentiality
                type_comptes VARCHAR(50),
                confidentialite VARCHAR(1),

                -- ETL metadata
                _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                _source_file VARCHAR(200)
            )
        """)
        logger.debug("Created table: inpi_comptes_annuels")

        # Balance sheet (Bilan)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS inpi_bilan (
                id BIGINT PRIMARY KEY,
                compte_annuel_id VARCHAR(100) NOT NULL,
                siren VARCHAR(9) NOT NULL,
                annee_cloture INTEGER,

                -- ACTIF (Assets)
                immobilisations_incorporelles DECIMAL(15,2),
                immobilisations_corporelles DECIMAL(15,2),
                immobilisations_financieres DECIMAL(15,2),
                actif_immobilise_brut DECIMAL(15,2),
                actif_immobilise_net DECIMAL(15,2),

                stocks DECIMAL(15,2),
                creances_clients DECIMAL(15,2),
                autres_creances DECIMAL(15,2),
                valeurs_mobilieres_placement DECIMAL(15,2),
                disponibilites DECIMAL(15,2),
                actif_circulant DECIMAL(15,2),

                charges_constatees_avance DECIMAL(15,2),
                total_actif DECIMAL(15,2),

                -- PASSIF (Liabilities)
                capital_social DECIMAL(15,2),
                primes_emission DECIMAL(15,2),
                reserves DECIMAL(15,2),
                report_a_nouveau DECIMAL(15,2),
                resultat_exercice DECIMAL(15,2),
                subventions_investissement DECIMAL(15,2),
                provisions_reglementees DECIMAL(15,2),
                capitaux_propres DECIMAL(15,2),

                provisions_risques_charges DECIMAL(15,2),

                emprunts_dettes_financieres DECIMAL(15,2),
                avances_acomptes_recus DECIMAL(15,2),
                dettes_fournisseurs DECIMAL(15,2),
                dettes_fiscales_sociales DECIMAL(15,2),
                autres_dettes DECIMAL(15,2),
                dettes DECIMAL(15,2),

                produits_constates_avance DECIMAL(15,2),
                total_passif DECIMAL(15,2),

                -- ETL metadata
                _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.debug("Created table: inpi_bilan")

        # Income statement (Compte de résultat)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS inpi_compte_resultat (
                id BIGINT PRIMARY KEY,
                compte_annuel_id VARCHAR(100) NOT NULL,
                siren VARCHAR(9) NOT NULL,
                annee_cloture INTEGER,

                -- PRODUITS (Revenue)
                ventes_marchandises DECIMAL(15,2),
                production_vendue_biens DECIMAL(15,2),
                production_vendue_services DECIMAL(15,2),
                chiffre_affaires DECIMAL(15,2),

                production_stockee DECIMAL(15,2),
                production_immobilisee DECIMAL(15,2),
                subventions_exploitation DECIMAL(15,2),
                reprises_provisions DECIMAL(15,2),
                autres_produits DECIMAL(15,2),
                total_produits_exploitation DECIMAL(15,2),

                -- CHARGES (Expenses)
                achats_marchandises DECIMAL(15,2),
                variation_stock_marchandises DECIMAL(15,2),
                achats_matieres_premieres DECIMAL(15,2),
                variation_stock_matieres DECIMAL(15,2),
                autres_achats_charges_externes DECIMAL(15,2),
                impots_taxes DECIMAL(15,2),
                salaires_traitements DECIMAL(15,2),
                charges_sociales DECIMAL(15,2),
                charges_personnel DECIMAL(15,2),
                dotations_amortissements DECIMAL(15,2),
                dotations_provisions DECIMAL(15,2),
                autres_charges DECIMAL(15,2),
                total_charges_exploitation DECIMAL(15,2),

                -- RESULTS
                resultat_exploitation DECIMAL(15,2),

                -- Financial
                produits_financiers DECIMAL(15,2),
                charges_financieres DECIMAL(15,2),
                resultat_financier DECIMAL(15,2),

                resultat_courant_avant_impot DECIMAL(15,2),

                -- Exceptional
                produits_exceptionnels DECIMAL(15,2),
                charges_exceptionnelles DECIMAL(15,2),
                resultat_exceptionnel DECIMAL(15,2),

                -- Taxes and final result
                participation_salaries DECIMAL(15,2),
                impot_benefice DECIMAL(15,2),
                resultat_net DECIMAL(15,2),

                -- ETL metadata
                _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.debug("Created table: inpi_compte_resultat")

    def _create_bodacc_tables(self) -> None:
        """Create BODACC tables for legal announcements."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bodacc_annonces (
                id VARCHAR(100) PRIMARY KEY,

                -- Identification
                siren VARCHAR(9),
                numero_annonce VARCHAR(50),

                -- Publication
                date_parution DATE,
                numero_parution VARCHAR(50),
                type_bulletin VARCHAR(1),

                -- Classification
                famille VARCHAR(100),
                nature VARCHAR(200),

                -- Company info
                denomination VARCHAR(300),
                forme_juridique VARCHAR(100),
                administration VARCHAR(500),

                -- Address
                adresse VARCHAR(500),
                code_postal VARCHAR(10),
                ville VARCHAR(100),

                -- Activity
                activite VARCHAR(500),

                -- Event-specific data (JSON for flexibility)
                details JSON,

                -- For collective procedures
                type_procedure VARCHAR(100),
                date_jugement DATE,
                tribunal VARCHAR(200),

                -- For account deposits (BODACC C)
                date_cloture_exercice DATE,
                type_depot VARCHAR(100),

                -- Raw content
                contenu_annonce TEXT,

                -- ETL metadata
                _loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                _source_file VARCHAR(200)
            )
        """)
        logger.debug("Created table: bodacc_annonces")

    def _create_etl_tables(self) -> None:
        """Create ETL tracking tables."""
        # Track data loads
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_loads (
                id INTEGER PRIMARY KEY,
                source VARCHAR(50) NOT NULL,
                load_type VARCHAR(20) NOT NULL,
                started_at TIMESTAMP NOT NULL,
                completed_at TIMESTAMP,
                status VARCHAR(20) DEFAULT 'running',
                rows_processed INTEGER DEFAULT 0,
                rows_inserted INTEGER DEFAULT 0,
                rows_updated INTEGER DEFAULT 0,
                error_message VARCHAR(2000),
                source_file VARCHAR(500)
            )
        """)
        # Create sequence for etl_loads.id
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_etl_loads START 1
        """)
        logger.debug("Created table: etl_loads")

        # Track source file downloads
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_downloads (
                id INTEGER PRIMARY KEY,
                source VARCHAR(50) NOT NULL,
                url VARCHAR(1000) NOT NULL,
                filename VARCHAR(300) NOT NULL,
                downloaded_at TIMESTAMP NOT NULL,
                file_size_bytes BIGINT,
                checksum VARCHAR(64),
                status VARCHAR(20) DEFAULT 'pending'
            )
        """)
        # Create sequence for etl_downloads.id
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_etl_downloads START 1
        """)
        logger.debug("Created table: etl_downloads")

    def _create_views(self) -> None:
        """Create analytical views."""
        # Company overview combining SIRENE + latest financials
        self.conn.execute("""
            CREATE OR REPLACE VIEW v_company_overview AS
            SELECT
                ul.siren,
                ul.denomination,
                ul.sigle,
                ul.activite_principale AS naf_code,
                ul.categorie_juridique,
                ul.tranche_effectifs,
                ul.caractere_employeur,
                ul.etat_administratif,
                ul.date_creation,
                ul.date_cessation,

                -- Siege info
                e.siret AS siret_siege,
                e.code_postal,
                e.libelle_commune AS commune,
                e.departement,

                -- Latest financials
                cr.chiffre_affaires,
                cr.resultat_net,
                cr.resultat_exploitation,
                cr.charges_personnel,
                cr.annee_cloture AS annee_financiere,

                b.total_actif,
                b.capitaux_propres,
                b.dettes,
                b.disponibilites

            FROM sirene_unites_legales ul
            LEFT JOIN sirene_etablissements e
                ON ul.siren = e.siren AND e.etablissement_siege = 'true'
            LEFT JOIN (
                SELECT DISTINCT ON (siren) *
                FROM inpi_compte_resultat
                ORDER BY siren, annee_cloture DESC
            ) cr ON ul.siren = cr.siren
            LEFT JOIN (
                SELECT DISTINCT ON (siren) *
                FROM inpi_bilan
                ORDER BY siren, annee_cloture DESC
            ) b ON ul.siren = b.siren
        """)
        logger.debug("Created view: v_company_overview")

    def _create_indexes(self) -> None:
        """Create indexes for query performance."""
        indexes = [
            # SIRENE indexes
            ("idx_ul_activite", "sirene_unites_legales", "activite_principale"),
            ("idx_ul_categorie", "sirene_unites_legales", "categorie_juridique"),
            ("idx_ul_effectifs", "sirene_unites_legales", "tranche_effectifs"),
            ("idx_ul_etat", "sirene_unites_legales", "etat_administratif"),
            ("idx_ul_date_creation", "sirene_unites_legales", "date_creation"),

            ("idx_etab_siren", "sirene_etablissements", "siren"),
            ("idx_etab_departement", "sirene_etablissements", "departement"),
            ("idx_etab_code_postal", "sirene_etablissements", "code_postal"),
            ("idx_etab_commune", "sirene_etablissements", "code_commune"),
            ("idx_etab_activite", "sirene_etablissements", "activite_principale"),

            # INPI indexes
            ("idx_comptes_siren", "inpi_comptes_annuels", "siren"),
            ("idx_comptes_annee", "inpi_comptes_annuels", "annee_cloture"),
            ("idx_bilan_siren", "inpi_bilan", "siren"),
            ("idx_bilan_annee", "inpi_bilan", "annee_cloture"),
            ("idx_cr_siren", "inpi_compte_resultat", "siren"),
            ("idx_cr_annee", "inpi_compte_resultat", "annee_cloture"),

            # BODACC indexes
            ("idx_bodacc_siren", "bodacc_annonces", "siren"),
            ("idx_bodacc_date", "bodacc_annonces", "date_parution"),
            ("idx_bodacc_type", "bodacc_annonces", "type_bulletin"),
            ("idx_bodacc_famille", "bodacc_annonces", "famille"),
        ]

        for idx_name, table, column in indexes:
            try:
                self.conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
            except Exception as e:
                logger.warning(f"Could not create index {idx_name}: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        stats = {}

        tables = [
            "sirene_unites_legales",
            "sirene_etablissements",
            "inpi_comptes_annuels",
            "inpi_bilan",
            "inpi_compte_resultat",
            "bodacc_annonces",
        ]

        for table in tables:
            try:
                result = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                stats[table] = result[0] if result else 0
            except Exception:
                stats[table] = 0

        # Get last ETL load dates
        try:
            result = self.conn.execute("""
                SELECT source, MAX(completed_at) as last_load
                FROM etl_loads
                WHERE status = 'success'
                GROUP BY source
            """).fetchall()
            stats["last_loads"] = {row[0]: row[1] for row in result}
        except Exception:
            stats["last_loads"] = {}

        return stats

    def log_etl_start(self, source: str, load_type: str, source_file: str = None) -> int:
        """Log start of ETL process and return load ID."""
        result = self.conn.execute("""
            INSERT INTO etl_loads (id, source, load_type, started_at, source_file)
            VALUES (nextval('seq_etl_loads'), ?, ?, ?, ?)
            RETURNING id
        """, [source, load_type, datetime.now(), source_file]).fetchone()
        return result[0]

    def log_etl_complete(
        self,
        load_id: int,
        status: str = "success",
        rows_processed: int = 0,
        rows_inserted: int = 0,
        error_message: str = None
    ) -> None:
        """Log completion of ETL process."""
        self.conn.execute("""
            UPDATE etl_loads
            SET completed_at = ?,
                status = ?,
                rows_processed = ?,
                rows_inserted = ?,
                error_message = ?
            WHERE id = ?
        """, [datetime.now(), status, rows_processed, rows_inserted, error_message, load_id])

    def execute(self, query: str, params: list = None) -> duckdb.DuckDBPyConnection:
        """Execute a query."""
        if params:
            return self.conn.execute(query, params)
        return self.conn.execute(query)

    def fetchall(self, query: str, params: list = None) -> list:
        """Execute query and fetch all results."""
        return self.execute(query, params).fetchall()

    def fetchone(self, query: str, params: list = None) -> tuple:
        """Execute query and fetch one result."""
        return self.execute(query, params).fetchone()
