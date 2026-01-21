"""INPI data extractor - Annual accounts from French IP office.

Outputs Parquet files directly - no database needed.
"""
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import tempfile
import httpx
import csv
import re
from loguru import logger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn


def _process_archive_worker(archive_path: str) -> list[dict]:
    """Worker function to process a single 7z archive (runs in separate process)."""
    archive_path = Path(archive_path)
    records = []

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["7z", "x", str(archive_path), f"-o{tmpdir}", "-y"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return records

        tmppath = Path(tmpdir)
        for xml_file in tmppath.rglob("*.xml"):
            try:
                record = _parse_xml_file(xml_file)
                if record:
                    records.append(record)
            except Exception:
                pass

    return records


def _parse_xml_file(xml_path: Path) -> Optional[dict]:
    """Parse a single XML bilan file and return structured data."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    ns = {"inpi": "fr:inpi:odrncs:bilansSaisisXML"}

    for bilan in root.findall(".//inpi:bilan", ns):
        identite = bilan.find("inpi:identite", ns)
        if identite is None:
            continue

        siren_el = identite.find("inpi:siren", ns)
        siren = siren_el.text.strip() if siren_el is not None and siren_el.text else None
        if not siren or len(siren) != 9:
            continue

        date_el = identite.find("inpi:date_cloture_exercice", ns)
        date_cloture_raw = date_el.text.strip() if date_el is not None and date_el.text else None
        if not date_cloture_raw or date_cloture_raw == "00000000":
            continue

        try:
            date_cloture = f"{date_cloture_raw[:4]}-{date_cloture_raw[4:6]}-{date_cloture_raw[6:8]}"
            annee = int(date_cloture_raw[:4])
        except (ValueError, IndexError):
            continue

        # Get bilan type
        type_el = identite.find("inpi:code_type_bilan", ns)
        bilan_type = type_el.text.strip() if type_el is not None and type_el.text else "C"

        # Format date_depot
        depot_el = identite.find("inpi:date_depot", ns)
        date_depot_raw = depot_el.text.strip() if depot_el is not None and depot_el.text else None
        date_depot = None
        if date_depot_raw and len(date_depot_raw) == 8:
            date_depot = f"{date_depot_raw[:4]}-{date_depot_raw[4:6]}-{date_depot_raw[6:8]}"

        # Parse duree
        duree_el = identite.find("inpi:duree_exercice_n", ns)
        duree_raw = duree_el.text.strip() if duree_el is not None and duree_el.text else None
        duree = int(duree_raw) if duree_raw and duree_raw.isdigit() else None

        # Helper to get element text
        def get_text(parent, path):
            el = parent.find(path, ns)
            return el.text.strip() if el is not None and el.text else None

        # Extract liasse codes
        detail = bilan.find("inpi:detail", ns)
        liasse_data = {}
        if detail is not None:
            for page in detail.findall("inpi:page", ns):
                for liasse in page.findall("inpi:liasse", ns):
                    code = liasse.get("code", "")
                    m1 = liasse.get("m1") or liasse.get("m3")
                    if code and m1:
                        try:
                            m1_str = str(m1)
                            if m1_str.startswith("-"):
                                value = -int(m1_str[1:]) / 100
                            else:
                                value = int(m1_str) / 100
                            liasse_data[code] = value
                        except (ValueError, TypeError):
                            pass

        # Helper to get value from multiple possible codes
        def get_val(*codes):
            for c in codes:
                if c in liasse_data:
                    return liasse_data[c]
            return None

        # Return flat record with all data
        return {
            "siren": siren,
            "date_cloture": date_cloture,
            "annee_cloture": annee,
            "duree_exercice": duree,
            "type_comptes": bilan_type,
            "date_depot": date_depot,
            "code_greffe": get_text(identite, "inpi:code_greffe"),
            "confidentialite": get_text(identite, "inpi:code_confidentialite"),
            # Bilan - Actif
            "immobilisations_incorporelles": get_val("028", "AB"),
            "immobilisations_corporelles": get_val("040", "AN"),
            "immobilisations_financieres": get_val("044", "CU"),
            "actif_immobilise_net": get_val("050", "BJ"),
            "stocks": get_val("060", "BT"),
            "creances_clients": get_val("068", "BX"),
            "disponibilites": get_val("072", "CF"),
            "actif_circulant": get_val("080", "CJ"),
            "total_actif": get_val("110", "CO"),
            # Bilan - Passif
            "capital_social": get_val("120", "DA"),
            "reserves": get_val("134", "DG"),
            "resultat_exercice": get_val("136", "DI"),
            "capitaux_propres": get_val("142", "DL"),
            "dettes": get_val("156", "EC"),
            "total_passif": get_val("180", "EE"),
            # Compte de résultat
            "chiffre_affaires": get_val("218", "FJ", "FL"),
            "charges_personnel": get_val("264", "FY"),
            "resultat_exploitation": get_val("270", "GG"),
            "resultat_financier": get_val("290", "GV"),
            "resultat_exceptionnel": get_val("HI"),
            "resultat_net": get_val("310", "HN"),
        }

    return None


class INPIExtractor:
    """Extract annual accounts from INPI and output to Parquet files."""

    MIRROR_BASE = "http://data.cquest.org/inpi_rncs/comptes"

    def __init__(self, config: dict = None):
        self.config = config or {}

    def download_mirror(
        self,
        output_dir: Path,
        years: list[int],
        max_files_per_year: Optional[int] = None,
    ) -> list[Path]:
        """Download INPI data from data.cquest.org mirror."""
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

            year_url = f"{self.MIRROR_BASE}/{year}/"
            try:
                response = httpx.get(year_url, timeout=30)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Failed to list files for {year}: {e}")
                continue

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

    def extract_to_parquet(
        self,
        source_dir: Path,
        output_dir: Path,
        year: Optional[int] = None,
        workers: Optional[int] = None,
    ) -> dict[str, int]:
        """Extract INPI XML data to Parquet files.

        Args:
            source_dir: Directory containing downloaded 7z files.
            output_dir: Directory for output Parquet files.
            year: Specific year to process, or None for all.
            workers: Number of parallel workers (default: CPU count).

        Returns:
            Dict with record counts per year.
        """
        import time

        source_dir = Path(source_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if workers is None:
            workers = multiprocessing.cpu_count()

        stats = {}

        # Find year directories
        if year:
            year_dirs = [source_dir / str(year)]
        else:
            year_dirs = [d for d in source_dir.iterdir() if d.is_dir() and d.name.isdigit()]

        for year_dir in sorted(year_dirs):
            if not year_dir.exists():
                continue

            year_name = year_dir.name
            logger.info(f"Processing year: {year_name}")

            # Find all 7z files
            archives = list(year_dir.glob("*.7z"))
            logger.info(f"Found {len(archives)} archives, using {workers} workers")

            # Process archives in parallel
            archive_paths = [str(a) for a in archives]
            all_records = []

            start_time = time.time()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total} archives"),
            ) as progress:
                task = progress.add_task(f"Extracting {year_name}...", total=len(archives))

                with ProcessPoolExecutor(max_workers=workers) as executor:
                    futures = {executor.submit(_process_archive_worker, path): path for path in archive_paths}

                    for future in as_completed(futures):
                        try:
                            records = future.result()
                            all_records.extend(records)
                        except Exception as e:
                            logger.debug(f"Worker error: {e}")
                        progress.update(task, advance=1)

            extract_time = time.time() - start_time
            logger.info(f"Extracted {len(all_records):,} records in {extract_time:.1f}s")

            # Write to Parquet
            if all_records:
                parquet_path = output_dir / f"inpi_comptes_{year_name}.parquet"
                logger.info(f"Writing to {parquet_path}...")

                write_start = time.time()
                self._write_parquet(all_records, parquet_path)
                write_time = time.time() - write_start

                logger.info(f"Written {len(all_records):,} records in {write_time:.1f}s")
                stats[year_name] = len(all_records)

        return stats

    def _write_parquet(self, records: list[dict], output_path: Path):
        """Write records to Parquet file using pyarrow."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq

            table = pa.Table.from_pylist(records)
            pq.write_table(table, output_path, compression='snappy')
        except ImportError:
            # Fallback to pandas if pyarrow not available
            import pandas as pd
            df = pd.DataFrame(records)
            df.to_parquet(output_path, compression='snappy', index=False)
