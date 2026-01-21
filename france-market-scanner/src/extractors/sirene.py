"""SIRENE data extractor - French company registry from INSEE."""
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn

from src.core.database import DatabaseManager
from src.core.downloader import Downloader


class SireneExtractor:
    """Extract SIRENE data from INSEE/data.gouv.fr.

    SIRENE contains the official French company registry with:
    - Legal units (unités légales): ~12M companies
    - Establishments (établissements): ~30M locations

    Data is available as Parquet files, updated monthly.
    """

    # Direct Parquet file URLs (preferred - smaller and faster)
    PARQUET_BASE_URL = "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/"

    PARQUET_FILES = {
        "unites": "StockUniteLegale_utf8.parquet",
        "etablissements": "StockEtablissement_utf8.parquet",
    }

    # Column mappings from SIRENE to our schema
    UNITE_LEGALE_COLUMNS = {
        "siren": "siren",
        "statutDiffusionUniteLegale": "statut_diffusion",
        "dateCreationUniteLegale": "date_creation",
        "sigleUniteLegale": "sigle",
        "denominationUniteLegale": "denomination",
        "denominationUsuelle1UniteLegale": "denomination_usuelle_1",
        "denominationUsuelle2UniteLegale": "denomination_usuelle_2",
        "denominationUsuelle3UniteLegale": "denomination_usuelle_3",
        "prenom1UniteLegale": "prenom",
        "nomUniteLegale": "nom",
        "categorieJuridiqueUniteLegale": "categorie_juridique",
        "activitePrincipaleUniteLegale": "activite_principale",
        "nomenclatureActivitePrincipaleUniteLegale": "nomenclature_activite",
        "trancheEffectifsUniteLegale": "tranche_effectifs",
        "anneeEffectifsUniteLegale": "annee_effectifs",
        "caractereEmployeurUniteLegale": "caractere_employeur",
        "categorieEntreprise": "categorie_entreprise",
        "anneeCategorieEntreprise": "annee_categorie_entreprise",
        "economieSocialeSolidaireUniteLegale": "economie_sociale_solidaire",
        "societeMissionUniteLegale": "societe_mission",
        "etatAdministratifUniteLegale": "etat_administratif",
        "dateDernierTraitementUniteLegale": "date_derniere_mise_a_jour",
    }

    ETABLISSEMENT_COLUMNS = {
        "siret": "siret",
        "siren": "siren",
        "nic": "nic",
        "statutDiffusionEtablissement": "statut_diffusion",
        "dateCreationEtablissement": "date_creation",
        "denominationUsuelleEtablissement": "denomination_usuelle",
        "enseigne1Etablissement": "enseigne_1",
        "enseigne2Etablissement": "enseigne_2",
        "enseigne3Etablissement": "enseigne_3",
        "activitePrincipaleEtablissement": "activite_principale",
        "nomenclatureActivitePrincipaleEtablissement": "nomenclature_activite",
        "activitePrincipaleRegistreMetiersEtablissement": "activite_principale_registre_metiers",
        "etablissementSiege": "etablissement_siege",
        "trancheEffectifsEtablissement": "tranche_effectifs",
        "anneeEffectifsEtablissement": "annee_effectifs",
        "caractereEmployeurEtablissement": "caractere_employeur",
        "complementAdresseEtablissement": "complement_adresse",
        "numeroVoieEtablissement": "numero_voie",
        "indiceRepetitionEtablissement": "indice_repetition",
        "typeVoieEtablissement": "type_voie",
        "libelleVoieEtablissement": "libelle_voie",
        "codePostalEtablissement": "code_postal",
        "libelleCommuneEtablissement": "libelle_commune",
        "libelleCommuneEtrangerEtablissement": "libelle_commune_etranger",
        "codeCommuneEtablissement": "code_commune",
        "codeCedexEtablissement": "code_cedex",
        "libelleCedexEtablissement": "libelle_cedex",
        "codePaysEtrangerEtablissement": "code_pays_etranger",
        "libellePaysEtrangerEtablissement": "libelle_pays_etranger",
        "etatAdministratifEtablissement": "etat_administratif",
        "dateDernierTraitementEtablissement": "date_derniere_mise_a_jour",
    }

    def __init__(self, config: dict):
        self.config = config
        self.downloader = Downloader(
            timeout=config.get("downloads", {}).get("timeout_seconds", 600),
            retry_attempts=config.get("downloads", {}).get("retry_attempts", 3),
        )

    def download(
        self,
        output_dir: Path,
        file_type: str = "all",
    ) -> list[Path]:
        """Download SIRENE Parquet files.

        Args:
            output_dir: Directory to save files.
            file_type: "all", "unites", or "etablissements".

        Returns:
            List of downloaded file paths.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        files_to_download = []
        if file_type in ("all", "unites"):
            files_to_download.append(("unites", self.PARQUET_FILES["unites"]))
        if file_type in ("all", "etablissements"):
            files_to_download.append(("etablissements", self.PARQUET_FILES["etablissements"]))

        downloaded = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
        ) as progress:
            for name, filename in files_to_download:
                url = f"{self.PARQUET_BASE_URL}{filename}"
                dest = output_dir / filename

                task = progress.add_task(f"Downloading {name}...", total=None)

                def update_progress(downloaded_bytes: int, total_bytes: int):
                    progress.update(task, completed=downloaded_bytes, total=total_bytes)

                asyncio.run(self.downloader.download(url, dest, update_progress))
                downloaded.append(dest)
                logger.info(f"Downloaded: {dest}")

        return downloaded

    def load(
        self,
        db: DatabaseManager,
        source_dir: Path,
        file_type: str = "all",
    ) -> dict[str, int]:
        """Load SIRENE data into DuckDB.

        Args:
            db: Database manager.
            source_dir: Directory containing Parquet files.
            file_type: "all", "unites", or "etablissements".

        Returns:
            Dict with row counts per table.
        """
        source_dir = Path(source_dir)
        stats = {}

        if file_type in ("all", "unites"):
            parquet_file = source_dir / self.PARQUET_FILES["unites"]
            if parquet_file.exists():
                count = self._load_unites_legales(db, parquet_file)
                stats["sirene_unites_legales"] = count
            else:
                logger.warning(f"File not found: {parquet_file}")

        if file_type in ("all", "etablissements"):
            parquet_file = source_dir / self.PARQUET_FILES["etablissements"]
            if parquet_file.exists():
                count = self._load_etablissements(db, parquet_file)
                stats["sirene_etablissements"] = count
            else:
                logger.warning(f"File not found: {parquet_file}")

        return stats

    def _load_unites_legales(self, db: DatabaseManager, parquet_file: Path) -> int:
        """Load legal units from Parquet file."""
        logger.info(f"Loading legal units from: {parquet_file}")

        load_id = db.log_etl_start("sirene_unites_legales", "full", str(parquet_file))

        try:
            # Clear existing data
            db.execute("DELETE FROM sirene_unites_legales")

            # Load directly from Parquet with explicit column mapping
            # Note: File contains historical periods, we load all and filter at query time
            query = f"""
                INSERT INTO sirene_unites_legales (
                    siren, statut_diffusion, date_creation, sigle,
                    denomination, denomination_usuelle_1, denomination_usuelle_2, denomination_usuelle_3,
                    prenom, nom, categorie_juridique, activite_principale, nomenclature_activite,
                    tranche_effectifs, annee_effectifs, caractere_employeur,
                    categorie_entreprise, annee_categorie_entreprise,
                    economie_sociale_solidaire, societe_mission,
                    etat_administratif, date_derniere_mise_a_jour,
                    _loaded_at, _source_file
                )
                SELECT
                    siren,
                    statutDiffusionUniteLegale,
                    TRY_CAST(dateCreationUniteLegale AS DATE),
                    sigleUniteLegale,
                    denominationUniteLegale,
                    denominationUsuelle1UniteLegale,
                    denominationUsuelle2UniteLegale,
                    denominationUsuelle3UniteLegale,
                    prenom1UniteLegale,
                    nomUniteLegale,
                    categorieJuridiqueUniteLegale,
                    activitePrincipaleUniteLegale,
                    nomenclatureActivitePrincipaleUniteLegale,
                    trancheEffectifsUniteLegale,
                    TRY_CAST(anneeEffectifsUniteLegale AS INTEGER),
                    caractereEmployeurUniteLegale,
                    categorieEntreprise,
                    TRY_CAST(anneeCategorieEntreprise AS INTEGER),
                    economieSocialeSolidaireUniteLegale,
                    societeMissionUniteLegale,
                    etatAdministratifUniteLegale,
                    TRY_CAST(dateDernierTraitementUniteLegale AS TIMESTAMP),
                    CURRENT_TIMESTAMP,
                    '{parquet_file.name}'
                FROM read_parquet('{parquet_file}')
            """

            db.execute(query)

            # Get count
            count = db.fetchone("SELECT COUNT(*) FROM sirene_unites_legales")[0]
            logger.info(f"Loaded {count:,} legal units")

            db.log_etl_complete(load_id, "success", count, count)
            return count

        except Exception as e:
            logger.error(f"Error loading legal units: {e}")
            db.log_etl_complete(load_id, "failed", 0, 0, str(e))
            raise

    def _load_etablissements(self, db: DatabaseManager, parquet_file: Path) -> int:
        """Load establishments from Parquet file."""
        logger.info(f"Loading establishments from: {parquet_file}")

        load_id = db.log_etl_start("sirene_etablissements", "full", str(parquet_file))

        try:
            # Clear existing data
            db.execute("DELETE FROM sirene_etablissements")

            # Load with explicit column mapping
            # Note: File contains historical periods, we load all and filter at query time
            query = f"""
                INSERT INTO sirene_etablissements (
                    siret, siren, nic, statut_diffusion, date_creation,
                    denomination_usuelle, enseigne_1, enseigne_2, enseigne_3,
                    activite_principale, nomenclature_activite, activite_principale_registre_metiers,
                    etablissement_siege, tranche_effectifs, annee_effectifs, caractere_employeur,
                    complement_adresse, numero_voie, indice_repetition, type_voie, libelle_voie,
                    code_postal, libelle_commune, libelle_commune_etranger, code_commune,
                    code_cedex, libelle_cedex, code_pays_etranger, libelle_pays_etranger,
                    departement, region, etat_administratif, date_derniere_mise_a_jour,
                    _loaded_at, _source_file
                )
                SELECT
                    siret,
                    siren,
                    nic,
                    statutDiffusionEtablissement,
                    TRY_CAST(dateCreationEtablissement AS DATE),
                    denominationUsuelleEtablissement,
                    enseigne1Etablissement,
                    enseigne2Etablissement,
                    enseigne3Etablissement,
                    activitePrincipaleEtablissement,
                    nomenclatureActivitePrincipaleEtablissement,
                    activitePrincipaleRegistreMetiersEtablissement,
                    etablissementSiege,
                    trancheEffectifsEtablissement,
                    TRY_CAST(anneeEffectifsEtablissement AS INTEGER),
                    caractereEmployeurEtablissement,
                    complementAdresseEtablissement,
                    numeroVoieEtablissement,
                    indiceRepetitionEtablissement,
                    typeVoieEtablissement,
                    libelleVoieEtablissement,
                    codePostalEtablissement,
                    libelleCommuneEtablissement,
                    libelleCommuneEtrangerEtablissement,
                    codeCommuneEtablissement,
                    codeCedexEtablissement,
                    libelleCedexEtablissement,
                    codePaysEtrangerEtablissement,
                    libellePaysEtrangerEtablissement,
                    -- Derive department from postal code
                    CASE
                        WHEN codePostalEtablissement IS NOT NULL AND LENGTH(codePostalEtablissement) >= 2
                        THEN LEFT(codePostalEtablissement, 2)
                        ELSE NULL
                    END,
                    NULL,  -- region
                    etatAdministratifEtablissement,
                    TRY_CAST(dateDernierTraitementEtablissement AS TIMESTAMP),
                    CURRENT_TIMESTAMP,
                    '{parquet_file.name}'
                FROM read_parquet('{parquet_file}')
            """

            db.execute(query)

            # Get count
            count = db.fetchone("SELECT COUNT(*) FROM sirene_etablissements")[0]
            logger.info(f"Loaded {count:,} establishments")

            db.log_etl_complete(load_id, "success", count, count)
            return count

        except Exception as e:
            logger.error(f"Error loading establishments: {e}")
            db.log_etl_complete(load_id, "failed", 0, 0, str(e))
            raise


# Effectif (employee) code mapping
EFFECTIF_CODES = {
    "00": "0 salarié",
    "01": "1 ou 2 salariés",
    "02": "3 à 5 salariés",
    "03": "6 à 9 salariés",
    "11": "10 à 19 salariés",
    "12": "20 à 49 salariés",
    "21": "50 à 99 salariés",
    "22": "100 à 199 salariés",
    "31": "200 à 249 salariés",
    "32": "250 à 499 salariés",
    "41": "500 à 999 salariés",
    "42": "1000 à 1999 salariés",
    "51": "2000 à 4999 salariés",
    "52": "5000 à 9999 salariés",
    "53": "10000 salariés et plus",
    "NN": "Non renseigné",
}


def get_effectif_label(code: str) -> str:
    """Get human-readable label for effectif code."""
    return EFFECTIF_CODES.get(code, "Inconnu")
