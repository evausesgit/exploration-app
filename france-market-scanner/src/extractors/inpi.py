"""INPI data extractor - Annual accounts from French IP office."""
import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Optional
from datetime import datetime
import httpx
from loguru import logger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn

from src.core.database import DatabaseManager


class INPIExtractor:
    """Extract annual accounts from INPI (Institut National de la Propriété Industrielle).

    INPI provides access to annual accounts (comptes annuels) deposited since 2017.
    Data includes:
    - Balance sheet (bilan)
    - Income statement (compte de résultat)

    Data sources:
    - SFTP: opendata-rncs.inpi.fr (often unavailable)
    - Mirror: data.cquest.org (recommended)
    """

    # SFTP configuration (often unavailable)
    SFTP_HOST = "opendata-rncs.inpi.fr"
    SFTP_PORT = 22
    BASE_PATH = "/public/IMR_Donnees_Saisies/tc/flux/"

    # Mirror configuration (recommended)
    MIRROR_BASE = "http://data.cquest.org/inpi_rncs/comptes"

    # Simplified bilan code mapping (numeric codes -> field names)
    # These are approximate mappings for simplified ("S") bilans
    SIMPLIFIED_CODES = {
        # Compte de résultat
        "210": "production_vendue_biens",
        "214": "production_vendue_services",
        "218": "chiffre_affaires_net",  # CA = 210 + 214
        "232": "total_produits_exploitation",
        "254": "charges_externes",
        "262": "impots_taxes",
        "264": "charges_personnel",
        "270": "resultat_exploitation",
        "290": "resultat_financier",
        "300": "resultat_courant",
        "310": "resultat_net",
        # Bilan actif
        "028": "immobilisations_incorporelles",
        "040": "immobilisations_corporelles",
        "044": "immobilisations_financieres",
        "050": "total_actif_immobilise",
        "060": "stocks",
        "068": "creances",
        "072": "disponibilites",
        "080": "total_actif_circulant",
        "110": "total_actif",
        # Bilan passif
        "120": "capital_social",
        "134": "reserves",
        "136": "resultat_exercice",
        "142": "capitaux_propres",
        "156": "dettes_financieres",
        "164": "dettes_fournisseurs",
        "172": "dettes_fiscales_sociales",
        "176": "autres_dettes",
        "180": "total_passif",
    }

    # Complete bilan code mapping (alphabetic codes -> field names)
    # These are the codes used in "C" (Complet) type bilans
    COMPLETE_CODES = {
        # Compte de résultat
        "FA": "production_vendue_biens",
        "FJ": "chiffre_affaires_net",  # Or use FL in some cases
        "FL": "chiffre_affaires_net",
        "FW": "charges_externes",
        "FX": "impots_taxes",
        "FY": "charges_personnel",
        "GG": "resultat_exploitation",
        "GV": "resultat_financier",
        "HI": "resultat_exceptionnel",
        "HN": "resultat_net",
        # Bilan actif
        "AB": "immobilisations_incorporelles",
        "AN": "immobilisations_corporelles",
        "CJ": "actif_circulant",
        "BJ": "actif_immobilise_net",
        "BT": "stocks",
        "BX": "creances",
        "CF": "disponibilites",
        "CO": "total_actif",
        # Bilan passif
        "DA": "capital_social",
        "DG": "reserves",
        "DI": "resultat_exercice",
        "DL": "capitaux_propres",
        "DU": "dettes_financieres",
        "DX": "dettes_fournisseurs",
        "EC": "dettes",
        "EE": "total_passif",
    }

    def __init__(self, config: dict):
        self.config = config
        self.username = config.get("inpi", {}).get("username")
        self.password = config.get("inpi", {}).get("password")

    def download(
        self,
        output_dir: Path,
        years: list[int],
    ) -> list[Path]:
        """Download INPI annual accounts data via SFTP.

        Args:
            output_dir: Directory to save files.
            years: List of years to download.

        Returns:
            List of downloaded file paths.
        """
        if not self.username or not self.password:
            logger.error("INPI credentials not configured")
            logger.info("Set INPI_USERNAME and INPI_PASSWORD in .env file")
            logger.info("Create a free account at https://data.inpi.fr")
            raise ValueError("INPI credentials required")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []

        logger.info(f"Connecting to INPI SFTP: {self.SFTP_HOST}")

        try:
            transport = paramiko.Transport((self.SFTP_HOST, self.SFTP_PORT))
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
            ) as progress:
                for year in years:
                    task = progress.add_task(f"Downloading {year}...", total=None)

                    year_files = self._download_year(sftp, year, output_dir)
                    downloaded.extend(year_files)

                    progress.update(task, completed=1, total=1)

            sftp.close()
            transport.close()

        except paramiko.AuthenticationException:
            logger.error("INPI authentication failed - check credentials")
            raise
        except Exception as e:
            logger.error(f"SFTP error: {e}")
            raise

        return downloaded

    def download_mirror(
        self,
        output_dir: Path,
        years: list[int],
        max_files_per_year: Optional[int] = None,
    ) -> list[Path]:
        """Download INPI data from data.cquest.org mirror.

        This is the recommended method as the official SFTP is often unavailable.

        Args:
            output_dir: Directory to save files.
            years: List of years to download (2017-2023 available).
            max_files_per_year: Limit files per year (for testing).

        Returns:
            List of downloaded file paths.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded = []

        logger.info(f"Downloading from mirror: {self.MIRROR_BASE}")

        for year in years:
            if year < 2017 or year > 2023:
                logger.warning(f"Year {year} not available on mirror (2017-2023 only)")
                continue

            year_dir = output_dir / str(year)
            year_dir.mkdir(exist_ok=True)

            # Get list of files for this year
            year_url = f"{self.MIRROR_BASE}/{year}/"
            try:
                response = httpx.get(year_url, timeout=30)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed to list files for {year}: {e}")
                continue

            # Parse file list from HTML
            import re
            files = re.findall(r'href="(bilans_saisis_\d+\.7z)"', response.text)

            if max_files_per_year:
                files = files[:max_files_per_year]

            logger.info(f"Year {year}: {len(files)} files to download")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
            ) as progress:
                task = progress.add_task(f"Downloading {year}...", total=len(files))

                for filename in files:
                    local_path = year_dir / filename

                    if local_path.exists():
                        progress.update(task, advance=1)
                        continue

                    file_url = f"{year_url}{filename}"
                    try:
                        with httpx.stream("GET", file_url, timeout=60) as r:
                            r.raise_for_status()
                            with open(local_path, "wb") as f:
                                for chunk in r.iter_bytes(chunk_size=8192):
                                    f.write(chunk)
                        downloaded.append(local_path)
                    except Exception as e:
                        logger.error(f"Failed to download {filename}: {e}")

                    progress.update(task, advance=1)

        logger.info(f"Downloaded {len(downloaded)} new files")
        return downloaded

    def load_xml(
        self,
        db: DatabaseManager,
        source_dir: Path,
        year: Optional[int] = None,
    ) -> dict[str, int]:
        """Load INPI XML data from 7z archives.

        Args:
            db: Database manager.
            source_dir: Directory containing downloaded 7z files.
            year: Specific year to load, or None for all.

        Returns:
            Dict with row counts per table.
        """
        source_dir = Path(source_dir)
        stats = {"comptes_annuels": 0, "bilans": 0, "comptes_resultat": 0}

        # Find year directories
        if year:
            year_dirs = [source_dir / str(year)]
        else:
            year_dirs = [d for d in source_dir.iterdir() if d.is_dir() and d.name.isdigit()]

        for year_dir in sorted(year_dirs):
            if not year_dir.exists():
                continue

            logger.info(f"Loading XML data for year: {year_dir.name}")

            # Find all 7z files
            archives = list(year_dir.glob("*.7z"))
            logger.info(f"Found {len(archives)} archives")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
            ) as progress:
                task = progress.add_task(f"Loading {year_dir.name}...", total=len(archives))

                for archive in archives:
                    try:
                        archive_stats = self._load_7z_archive(db, archive)
                        for key, value in archive_stats.items():
                            stats[key] += value
                    except Exception as e:
                        logger.error(f"Error loading {archive}: {e}")

                    progress.update(task, advance=1)

        logger.info(f"Loaded: {stats}")
        return stats

    def _load_7z_archive(
        self,
        db: DatabaseManager,
        archive_path: Path,
    ) -> dict[str, int]:
        """Extract and load a single 7z archive."""
        import tempfile

        stats = {"comptes_annuels": 0, "bilans": 0, "comptes_resultat": 0}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract 7z archive
            result = subprocess.run(
                ["7z", "x", str(archive_path), f"-o{tmpdir}", "-y"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"7z extraction failed: {result.stderr}")
                return stats

            # Find and process XML files
            tmppath = Path(tmpdir)
            for xml_file in tmppath.rglob("*.xml"):
                try:
                    file_stats = self._process_xml_file(db, xml_file)
                    for key, value in file_stats.items():
                        stats[key] += value
                except Exception as e:
                    logger.debug(f"Error processing {xml_file.name}: {e}")

        return stats

    def _process_xml_file(
        self,
        db: DatabaseManager,
        xml_path: Path,
    ) -> dict[str, int]:
        """Process a single XML bilan file."""
        stats = {"comptes_annuels": 0, "bilans": 0, "comptes_resultat": 0}

        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Handle namespace
        ns = {"inpi": "fr:inpi:odrncs:bilansSaisisXML"}

        for bilan in root.findall(".//inpi:bilan", ns):
            identite = bilan.find("inpi:identite", ns)
            if identite is None:
                continue

            siren = self._get_xml_text(identite, "inpi:siren", ns)
            if not siren or len(siren) != 9:
                continue

            date_cloture_raw = self._get_xml_text(identite, "inpi:date_cloture_exercice", ns)
            if not date_cloture_raw or date_cloture_raw == "00000000":
                continue

            # Parse date (YYYYMMDD format)
            try:
                date_cloture = f"{date_cloture_raw[:4]}-{date_cloture_raw[4:6]}-{date_cloture_raw[6:8]}"
                annee = int(date_cloture_raw[:4])
            except (ValueError, IndexError):
                continue

            # Determine bilan type (S=Simplified, C=Complete, K=Consolidated)
            bilan_type = self._get_xml_text(identite, "inpi:code_type_bilan", ns) or "C"

            # Generate unique ID
            compte_id = f"{siren}_{date_cloture}_{xml_path.stem[:30]}"

            # Extract liasse codes
            detail = bilan.find("inpi:detail", ns)
            liasse_data = {}
            if detail is not None:
                for page in detail.findall("inpi:page", ns):
                    for liasse in page.findall("inpi:liasse", ns):
                        code = liasse.get("code", "")
                        m1 = liasse.get("m1")  # Current year value
                        # Also check m3 (net value) for some fields
                        if not m1:
                            m1 = liasse.get("m3")
                        if code and m1:
                            try:
                                # Values are stored as fixed-width strings like "000000000247800"
                                # Handle negative values (prefix with -)
                                m1_str = str(m1)
                                if m1_str.startswith("-"):
                                    value = -int(m1_str[1:]) / 100
                                else:
                                    value = int(m1_str) / 100  # Convert centimes to euros
                                liasse_data[code] = value
                            except (ValueError, TypeError):
                                pass

            # Insert compte annuel
            try:
                # Format date_depot from YYYYMMDD to YYYY-MM-DD
                date_depot_raw = self._get_xml_text(identite, "inpi:date_depot", ns)
                date_depot = None
                if date_depot_raw and len(date_depot_raw) == 8:
                    date_depot = f"{date_depot_raw[:4]}-{date_depot_raw[4:6]}-{date_depot_raw[6:8]}"

                # Parse duree_exercice as int
                duree_raw = self._get_xml_text(identite, "inpi:duree_exercice_n", ns)
                duree = int(duree_raw) if duree_raw and duree_raw.isdigit() else None

                db.execute("""
                    INSERT OR REPLACE INTO inpi_comptes_annuels (
                        id, siren, date_cloture, duree_exercice, annee_cloture,
                        code_greffe, num_depot, date_depot, type_comptes,
                        confidentialite, _source_file
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    compte_id,
                    siren,
                    date_cloture,
                    duree,
                    annee,
                    self._get_xml_text(identite, "inpi:code_greffe", ns),
                    self._get_xml_text(identite, "inpi:num_depot", ns),
                    date_depot,
                    bilan_type,
                    self._get_xml_text(identite, "inpi:code_confidentialite", ns),
                    xml_path.name,
                ])
                stats["comptes_annuels"] += 1
            except Exception as e:
                logger.debug(f"Error inserting compte annuel: {e}")
                return stats

            # Insert bilan data - use appropriate code mapping based on type
            if liasse_data:
                try:
                    result = db.fetchone("SELECT COALESCE(MAX(id), 0) + 1 FROM inpi_bilan")
                    bilan_id = result[0]

                    # Get values using both simplified and complete codes
                    def get_val(*codes):
                        for c in codes:
                            if c in liasse_data:
                                return liasse_data[c]
                        return None

                    db.execute("""
                        INSERT INTO inpi_bilan (
                            id, compte_annuel_id, siren, annee_cloture,
                            immobilisations_incorporelles, immobilisations_corporelles,
                            immobilisations_financieres, actif_immobilise_net,
                            stocks, creances_clients, disponibilites, actif_circulant,
                            total_actif, capital_social, reserves, resultat_exercice,
                            capitaux_propres, dettes, total_passif
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        bilan_id,
                        compte_id,
                        siren,
                        annee,
                        get_val("028", "AB"),  # immobilisations_incorporelles
                        get_val("040", "AN"),  # immobilisations_corporelles
                        get_val("044", "CU"),  # immobilisations_financieres
                        get_val("050", "BJ"),  # actif_immobilise_net
                        get_val("060", "BT"),  # stocks
                        get_val("068", "BX"),  # creances_clients
                        get_val("072", "CF"),  # disponibilites
                        get_val("080", "CJ"),  # actif_circulant
                        get_val("110", "CO"),  # total_actif
                        get_val("120", "DA"),  # capital_social
                        get_val("134", "DG"),  # reserves
                        get_val("136", "DI"),  # resultat_exercice
                        get_val("142", "DL"),  # capitaux_propres
                        get_val("156", "EC"),  # dettes
                        get_val("180", "EE"),  # total_passif
                    ])
                    stats["bilans"] += 1
                except Exception as e:
                    logger.debug(f"Error inserting bilan: {e}")

            # Insert compte de résultat - check for both simplified and complete codes
            has_cr_data = any(liasse_data.get(code) for code in ["218", "264", "310", "FJ", "FL", "FY", "HN"])
            if has_cr_data:
                try:
                    result = db.fetchone("SELECT COALESCE(MAX(id), 0) + 1 FROM inpi_compte_resultat")
                    cr_id = result[0]

                    def get_val(*codes):
                        for c in codes:
                            if c in liasse_data:
                                return liasse_data[c]
                        return None

                    db.execute("""
                        INSERT INTO inpi_compte_resultat (
                            id, compte_annuel_id, siren, annee_cloture,
                            chiffre_affaires, charges_personnel, resultat_exploitation,
                            resultat_financier, resultat_exceptionnel, resultat_net
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        cr_id,
                        compte_id,
                        siren,
                        annee,
                        get_val("218", "FJ", "FL"),  # chiffre_affaires
                        get_val("264", "FY"),  # charges_personnel
                        get_val("270", "GG"),  # resultat_exploitation
                        get_val("290", "GV"),  # resultat_financier
                        get_val("HI"),  # resultat_exceptionnel
                        get_val("310", "HN"),  # resultat_net
                    ])
                    stats["comptes_resultat"] += 1
                except Exception as e:
                    logger.debug(f"Error inserting compte resultat: {e}")

        return stats

    def _get_xml_text(self, element, path: str, ns: dict) -> Optional[str]:
        """Get text content from XML element."""
        el = element.find(path, ns)
        if el is not None and el.text:
            return el.text.strip()
        return None

    def _download_year(
        self,
        sftp,
        year: int,
        output_dir: Path,
    ) -> list[Path]:
        """Download all files for a specific year."""
        downloaded = []
        year_path = f"{self.BASE_PATH}{year}/"

        try:
            files = sftp.listdir(year_path)
        except FileNotFoundError:
            logger.warning(f"No data found for year {year}")
            return []

        # Filter for bilans files (contains annual accounts)
        bilan_files = [f for f in files if "bilans" in f.lower() or "comptes" in f.lower()]

        if not bilan_files:
            # Try to list all zip files
            bilan_files = [f for f in files if f.endswith(".zip")]

        logger.info(f"Found {len(bilan_files)} files for year {year}")

        year_dir = output_dir / str(year)
        year_dir.mkdir(exist_ok=True)

        for filename in bilan_files:
            remote_path = f"{year_path}{filename}"
            local_path = year_dir / filename

            if local_path.exists():
                logger.debug(f"Skipping existing file: {filename}")
                continue

            logger.info(f"Downloading: {filename}")
            sftp.get(remote_path, str(local_path))
            downloaded.append(local_path)

        return downloaded

    def load(
        self,
        db: DatabaseManager,
        source_dir: Path,
        year: Optional[int] = None,
    ) -> dict[str, int]:
        """Load INPI data into DuckDB.

        Args:
            db: Database manager.
            source_dir: Directory containing downloaded files.
            year: Specific year to load, or None for all.

        Returns:
            Dict with row counts per table.
        """
        source_dir = Path(source_dir)
        stats = {"comptes_annuels": 0, "bilans": 0, "comptes_resultat": 0}

        # Find year directories or use specific year
        if year:
            year_dirs = [source_dir / str(year)]
        else:
            year_dirs = [d for d in source_dir.iterdir() if d.is_dir() and d.name.isdigit()]

        for year_dir in sorted(year_dirs):
            if not year_dir.exists():
                logger.warning(f"Year directory not found: {year_dir}")
                continue

            logger.info(f"Loading data for year: {year_dir.name}")
            year_stats = self._load_year(db, year_dir)

            for key, value in year_stats.items():
                stats[key] += value

        return stats

    def _load_year(self, db: DatabaseManager, year_dir: Path) -> dict[str, int]:
        """Load all files for a specific year."""
        stats = {"comptes_annuels": 0, "bilans": 0, "comptes_resultat": 0}

        zip_files = list(year_dir.glob("*.zip"))
        json_files = list(year_dir.glob("*.json"))

        # Process ZIP files
        for zip_file in zip_files:
            try:
                with zipfile.ZipFile(zip_file, "r") as zf:
                    for name in zf.namelist():
                        if name.endswith(".json"):
                            with zf.open(name) as f:
                                data = json.load(f)
                                file_stats = self._process_json_data(db, data, zip_file.name)
                                for key, value in file_stats.items():
                                    stats[key] += value
            except Exception as e:
                logger.error(f"Error processing {zip_file}: {e}")

        # Process JSON files directly
        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    file_stats = self._process_json_data(db, data, json_file.name)
                    for key, value in file_stats.items():
                        stats[key] += value
            except Exception as e:
                logger.error(f"Error processing {json_file}: {e}")

        return stats

    def _process_json_data(
        self,
        db: DatabaseManager,
        data: dict | list,
        source_file: str,
    ) -> dict[str, int]:
        """Process JSON data and insert into database."""
        stats = {"comptes_annuels": 0, "bilans": 0, "comptes_resultat": 0}

        # Handle different JSON structures
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            if "bilans" in data:
                records = data["bilans"]
            elif "comptes" in data:
                records = data["comptes"]
            else:
                records = [data]
        else:
            return stats

        for record in records:
            try:
                record_stats = self._insert_compte_annuel(db, record, source_file)
                for key, value in record_stats.items():
                    stats[key] += value
            except Exception as e:
                logger.debug(f"Error inserting record: {e}")

        return stats

    def _insert_compte_annuel(
        self,
        db: DatabaseManager,
        record: dict,
        source_file: str,
    ) -> dict[str, int]:
        """Insert a single annual account record."""
        stats = {"comptes_annuels": 0, "bilans": 0, "comptes_resultat": 0}

        # Extract SIREN
        siren = record.get("siren") or record.get("identifiant", {}).get("siren")
        if not siren:
            return stats

        # Generate unique ID
        date_cloture = record.get("dateCloture") or record.get("date_cloture")
        compte_id = f"{siren}_{date_cloture}_{source_file[:20]}"

        # Extract year
        annee = None
        if date_cloture:
            try:
                annee = int(date_cloture[:4])
            except (ValueError, TypeError):
                pass

        # Insert compte annuel metadata
        try:
            db.execute("""
                INSERT OR REPLACE INTO inpi_comptes_annuels (
                    id, siren, date_cloture, duree_exercice, annee_cloture,
                    code_greffe, num_depot, date_depot, type_comptes,
                    confidentialite, _source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                compte_id,
                siren,
                date_cloture,
                record.get("dureeExercice"),
                annee,
                record.get("codeGreffe"),
                record.get("numDepot"),
                record.get("dateDepot"),
                record.get("typeComptes"),
                record.get("confidentialite", "N"),
                source_file,
            ])
            stats["comptes_annuels"] += 1
        except Exception as e:
            logger.debug(f"Error inserting compte annuel: {e}")

        # Insert bilan
        bilan = record.get("bilan") or record.get("bilanActif")
        if bilan:
            try:
                self._insert_bilan(db, compte_id, siren, annee, bilan)
                stats["bilans"] += 1
            except Exception as e:
                logger.debug(f"Error inserting bilan: {e}")

        # Insert compte de résultat
        cr = record.get("compteResultat") or record.get("compte_resultat")
        if cr:
            try:
                self._insert_compte_resultat(db, compte_id, siren, annee, cr)
                stats["comptes_resultat"] += 1
            except Exception as e:
                logger.debug(f"Error inserting compte resultat: {e}")

        return stats

    def _insert_bilan(
        self,
        db: DatabaseManager,
        compte_id: str,
        siren: str,
        annee: int,
        bilan: dict,
    ):
        """Insert balance sheet data."""
        # Get next ID
        result = db.fetchone("SELECT COALESCE(MAX(id), 0) + 1 FROM inpi_bilan")
        bilan_id = result[0]

        db.execute("""
            INSERT INTO inpi_bilan (
                id, compte_annuel_id, siren, annee_cloture,
                immobilisations_incorporelles, immobilisations_corporelles,
                immobilisations_financieres, actif_immobilise_net,
                stocks, creances_clients, disponibilites, actif_circulant,
                total_actif, capital_social, reserves, resultat_exercice,
                capitaux_propres, dettes, total_passif
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            bilan_id,
            compte_id,
            siren,
            annee,
            self._get_decimal(bilan, "immobilisationsIncorporelles", "AI"),
            self._get_decimal(bilan, "immobilisationsCorporelles", "AJ"),
            self._get_decimal(bilan, "immobilisationsFinancieres", "AK"),
            self._get_decimal(bilan, "actifImmobiliseNet", "BJ"),
            self._get_decimal(bilan, "stocks", "BL"),
            self._get_decimal(bilan, "creancesClients", "BX"),
            self._get_decimal(bilan, "disponibilites", "CF"),
            self._get_decimal(bilan, "actifCirculant", "CJ"),
            self._get_decimal(bilan, "totalActif", "CO"),
            self._get_decimal(bilan, "capitalSocial", "DA"),
            self._get_decimal(bilan, "reserves", "DB"),
            self._get_decimal(bilan, "resultatExercice", "DI"),
            self._get_decimal(bilan, "capitauxPropres", "DL"),
            self._get_decimal(bilan, "dettes", "EC"),
            self._get_decimal(bilan, "totalPassif", "EE"),
        ])

    def _insert_compte_resultat(
        self,
        db: DatabaseManager,
        compte_id: str,
        siren: str,
        annee: int,
        cr: dict,
    ):
        """Insert income statement data."""
        # Get next ID
        result = db.fetchone("SELECT COALESCE(MAX(id), 0) + 1 FROM inpi_compte_resultat")
        cr_id = result[0]

        db.execute("""
            INSERT INTO inpi_compte_resultat (
                id, compte_annuel_id, siren, annee_cloture,
                chiffre_affaires, charges_personnel, resultat_exploitation,
                resultat_financier, resultat_exceptionnel, resultat_net
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            cr_id,
            compte_id,
            siren,
            annee,
            self._get_decimal(cr, "chiffreAffaires", "FL"),
            self._get_decimal(cr, "chargesPersonnel", "FY"),
            self._get_decimal(cr, "resultatExploitation", "GG"),
            self._get_decimal(cr, "resultatFinancier", "GV"),
            self._get_decimal(cr, "resultatExceptionnel", "HI"),
            self._get_decimal(cr, "resultatNet", "HN"),
        ])

    def _get_decimal(self, data: dict, *keys) -> Optional[float]:
        """Extract decimal value from dict using multiple possible keys."""
        for key in keys:
            if key in data:
                value = data[key]
                if value is not None:
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        pass
        return None
