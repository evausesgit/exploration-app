"""BODACC data extractor - Legal announcements from French official gazette."""
import asyncio
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import httpx
from loguru import logger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.core.database import DatabaseManager


class BODACCExtractor:
    """Extract legal announcements from BODACC.

    BODACC (Bulletin Officiel des Annonces Civiles et Commerciales) contains:
    - Type A: Sales, creations, insolvency procedures
    - Type B: Modifications, deregistrations
    - Type C: Annual account deposits

    Data is available via OpenDataSoft API (free, no auth required).
    """

    # OpenDataSoft API
    API_BASE = "https://bodacc-datadila.opendatasoft.com/api/v2"
    DATASET = "annonces-commerciales"

    def __init__(self, config: dict):
        self.config = config
        self.page_size = config.get("bodacc", {}).get("page_size", 100)

    def download(
        self,
        output_dir: Path,
        year: Optional[int] = None,
        days: int = 30,
        source: str = "api",
    ) -> list[Path]:
        """Download BODACC announcements.

        Args:
            output_dir: Directory to save files.
            year: Specific year (for bulk historical).
            days: Number of recent days to fetch (API mode).
            source: "api" for OpenDataSoft API, "ftps" for bulk historical.

        Returns:
            List of downloaded file paths.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if source == "ftps":
            logger.warning("FTPS mode not yet implemented - contact DILA for access")
            return []

        # API mode - fetch recent announcements
        return asyncio.run(self._download_api(output_dir, year, days))

    async def _download_api(
        self,
        output_dir: Path,
        year: Optional[int],
        days: int,
    ) -> list[Path]:
        """Download via OpenDataSoft API with date windowing.

        Splits large date ranges into 30-day windows to avoid API limit of 10K records.
        """
        downloaded = []

        # Build date windows
        windows = self._build_date_windows(year, days)
        total_windows = len(windows)

        if total_windows > 1:
            logger.info(f"Splitting request into {total_windows} date windows")
        else:
            start, end = windows[0]
            logger.info(f"Fetching BODACC announcements: {start} to {end}")

        all_records = []

        async with httpx.AsyncClient(timeout=60) as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed} records"),
            ) as progress:
                task = progress.add_task("Fetching announcements...", total=None)

                for i, (start_date, end_date) in enumerate(windows):
                    if total_windows > 1:
                        logger.info(f"Window {i+1}/{total_windows}: {start_date} to {end_date}")

                    records = await self._fetch_window(
                        client, start_date, end_date, progress, task
                    )
                    all_records.extend(records)

        logger.info(f"Fetched {len(all_records)} announcements total")

        # Save to JSON file
        if all_records:
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"bodacc_{date_str}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_records, f, ensure_ascii=False, indent=2)

            downloaded.append(output_file)
            logger.info(f"Saved to: {output_file}")

        return downloaded

    def load(
        self,
        db: DatabaseManager,
        source_dir: Path,
    ) -> dict[str, int]:
        """Load BODACC data into DuckDB.

        Args:
            db: Database manager.
            source_dir: Directory containing JSON files.

        Returns:
            Dict with row counts.
        """
        source_dir = Path(source_dir)
        stats = {"bodacc_annonces": 0}

        json_files = list(source_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files to load")

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    records = json.load(f)

                count = self._load_records(db, records, json_file.name)
                stats["bodacc_annonces"] += count
                logger.info(f"Loaded {count} records from {json_file.name}")

            except Exception as e:
                logger.error(f"Error loading {json_file}: {e}")

        return stats

    def _load_records(
        self,
        db: DatabaseManager,
        records: list,
        source_file: str,
    ) -> int:
        """Load announcement records into database."""
        count = 0

        for record in records:
            try:
                # Extract fields from OpenDataSoft record format
                fields = record.get("record", {}).get("fields", {})
                if not fields:
                    fields = record.get("fields", {})
                if not fields:
                    fields = record

                annonce_id = fields.get("id") or record.get("record", {}).get("id")
                if not annonce_id:
                    continue

                # Extract SIREN from various possible fields
                siren = self._extract_siren(fields)

                # Parse date
                date_parution = fields.get("dateparution")

                # Determine bulletin type from id or content
                type_bulletin = self._get_bulletin_type(annonce_id, fields)

                # Build details JSON for type-specific data
                details = {
                    k: v for k, v in fields.items()
                    if k not in [
                        "id", "dateparution", "numerodepartement",
                        "nomgreffeorigine", "tribunal"
                    ]
                }

                db.execute("""
                    INSERT OR REPLACE INTO bodacc_annonces (
                        id, siren, numero_annonce, date_parution, numero_parution,
                        type_bulletin, famille, nature, denomination, forme_juridique,
                        adresse, code_postal, ville, activite, details,
                        type_procedure, date_jugement, tribunal,
                        date_cloture_exercice, contenu_annonce,
                        _source_file
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    annonce_id,
                    siren,
                    fields.get("numeroannonce"),
                    date_parution,
                    fields.get("numeroparution"),
                    type_bulletin,
                    fields.get("familleavis"),
                    fields.get("typeavis"),
                    fields.get("denomination") or fields.get("raisonSociale"),
                    fields.get("formejuridique"),
                    fields.get("adresse"),
                    fields.get("codepostal"),
                    fields.get("ville") or fields.get("nomCommune"),
                    fields.get("activite") or fields.get("descriptif"),
                    json.dumps(details, ensure_ascii=False) if details else None,
                    fields.get("typeprocedure"),
                    fields.get("datejugement"),
                    fields.get("tribunal") or fields.get("nomgreffeorigine"),
                    fields.get("datecloture"),
                    fields.get("contenu") or fields.get("texte"),
                    source_file,
                ])
                count += 1

            except Exception as e:
                logger.debug(f"Error inserting record: {e}")

        return count

    def _extract_siren(self, fields: dict) -> Optional[str]:
        """Extract SIREN from various possible field names."""
        # Try direct SIREN field
        siren = fields.get("siren") or fields.get("numeroImmatriculation")

        if not siren:
            # Try to extract from RCS number
            rcs = fields.get("registre") or fields.get("numeroRcs")
            if rcs:
                # RCS format: "123 456 789 RCS Paris"
                match = re.search(r"(\d{3})\s*(\d{3})\s*(\d{3})", str(rcs))
                if match:
                    siren = "".join(match.groups())

        # Validate SIREN format
        if siren:
            siren = re.sub(r"\D", "", str(siren))
            if len(siren) == 9 and siren.isdigit():
                return siren

        return None

    def _get_bulletin_type(self, annonce_id: str, fields: dict) -> str:
        """Determine bulletin type (A, B, or C)."""
        # Try to extract from ID
        if annonce_id:
            id_upper = str(annonce_id).upper()
            if "BODA" in id_upper:
                return "A"
            elif "BODB" in id_upper:
                return "B"
            elif "BODC" in id_upper:
                return "C"

        # Try to infer from content
        famille = (fields.get("familleavis") or "").lower()
        if "vente" in famille or "creation" in famille or "collectif" in famille:
            return "A"
        elif "modification" in famille or "radiation" in famille:
            return "B"
        elif "depot" in famille or "compte" in famille:
            return "C"

        return "A"  # Default

    def _build_date_windows(self, year: Optional[int], days: int) -> list[tuple[str, str]]:
        """Split date range into windows to avoid API limit of 10K records.

        Uses 7-day windows for recent data (BODACC has ~2-3K announcements/day).
        Uses 14-day windows for yearly data.

        Args:
            year: Specific year to fetch (uses 14-day windows).
            days: Number of recent days to fetch (uses 7-day windows).

        Returns:
            List of (start_date, end_date) tuples as ISO strings.
        """
        windows = []
        window_size = 7  # 7 days should stay well under 10K limit

        if year:
            # Full year: ~26 two-week windows
            window_size = 14
            start = datetime(year, 1, 1)
            end = datetime(year, 12, 31)
            current = start

            while current < end:
                window_end = min(current + timedelta(days=window_size - 1), end)
                windows.append((
                    current.strftime("%Y-%m-%d"),
                    window_end.strftime("%Y-%m-%d")
                ))
                current = window_end + timedelta(days=1)
        else:
            # Recent days: 7-day windows working backwards
            current_end = datetime.now()
            remaining = days

            while remaining > 0:
                window_days = min(window_size, remaining)
                window_start = current_end - timedelta(days=window_days)

                windows.append((
                    window_start.strftime("%Y-%m-%d"),
                    current_end.strftime("%Y-%m-%d")
                ))

                current_end = window_start
                remaining -= window_days

        return windows

    async def _fetch_window(
        self,
        client: httpx.AsyncClient,
        start_date: str,
        end_date: str,
        progress,
        task,
    ) -> list:
        """Fetch all records for a single date window.

        Args:
            client: HTTP client.
            start_date: Start date (ISO format).
            end_date: End date (ISO format).
            progress: Rich progress bar.
            task: Progress task ID.

        Returns:
            List of announcement records.
        """
        where = f"dateparution >= '{start_date}' AND dateparution <= '{end_date}'"
        records = []
        offset = 0
        max_offset = 9900  # OpenDataSoft API limit

        while offset < max_offset:
            url = f"{self.API_BASE}/catalog/datasets/{self.DATASET}/records"
            params = {
                "where": where,
                "limit": self.page_size,
                "offset": offset,
                "order_by": "dateparution DESC",
            }

            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400 and offset > 0:
                    logger.warning(f"API limit reached at offset {offset}")
                    break
                raise

            data = response.json()
            batch = data.get("records", [])

            if not batch:
                break

            records.extend(batch)
            offset += len(batch)
            progress.update(task, completed=progress.tasks[task].completed + len(batch))

            # Check if we've fetched all records for this window
            total = data.get("total_count", 0)
            if offset >= total:
                break

        return records
