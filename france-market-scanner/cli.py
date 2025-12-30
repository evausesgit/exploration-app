#!/usr/bin/env python3
"""France Market Scanner CLI - Bulk French company data collection."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.table import Table
from loguru import logger

from src.core.config import load_config, get_project_root
from src.core.database import DatabaseManager

console = Console()


def setup_logging(verbose: bool = False):
    """Configure logging."""
    logger.remove()
    level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    )


@click.group()
@click.option("--config", "-c", default=None, help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, config, verbose):
    """France Market Scanner - Bulk French company data collection.

    Collect and analyze French company data from public sources:
    - SIRENE (INSEE): Company registry
    - INPI: Annual accounts
    - BODACC: Legal announcements
    """
    ctx.ensure_object(dict)
    setup_logging(verbose)

    try:
        ctx.obj["config"] = load_config(config)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


# =============================================================================
# Database Commands
# =============================================================================

@cli.command("init-db")
@click.option("--force", is_flag=True, help="Drop existing tables")
@click.pass_context
def init_db(ctx, force):
    """Initialize the DuckDB database schema."""
    config = ctx.obj["config"]
    db_path = config["database"]["path"]

    if force:
        console.print("[yellow]Warning:[/yellow] Force mode - existing tables will be dropped")
        if not click.confirm("Continue?"):
            return

    with DatabaseManager(db_path) as db:
        db.init_schema(force=force)

    console.print(f"[green]Database initialized:[/green] {db_path}")


@cli.command("db-info")
@click.pass_context
def db_info(ctx):
    """Show database information and statistics."""
    config = ctx.obj["config"]
    db_path = config["database"]["path"]

    if not Path(db_path).exists():
        console.print(f"[red]Database not found:[/red] {db_path}")
        console.print("Run 'init-db' first to create the database.")
        return

    with DatabaseManager(db_path) as db:
        stats = db.get_stats()

    # Display stats
    table = Table(title="Database Statistics")
    table.add_column("Table", style="cyan")
    table.add_column("Rows", justify="right", style="green")

    for table_name, count in stats.items():
        if table_name != "last_loads":
            table.add_row(table_name, f"{count:,}")

    console.print(table)

    # Last loads
    if stats.get("last_loads"):
        console.print("\n[bold]Last successful loads:[/bold]")
        for source, date in stats["last_loads"].items():
            console.print(f"  {source}: {date}")


@cli.command("stats")
@click.pass_context
def stats(ctx):
    """Show quick statistics about loaded data."""
    config = ctx.obj["config"]
    db_path = config["database"]["path"]

    if not Path(db_path).exists():
        console.print(f"[red]Database not found:[/red] {db_path}")
        return

    with DatabaseManager(db_path) as db:
        # Companies by status
        try:
            result = db.fetchall("""
                SELECT
                    etat_administratif,
                    COUNT(*) as count
                FROM sirene_unites_legales
                GROUP BY etat_administratif
            """)
            console.print("\n[bold]Companies by status:[/bold]")
            for row in result:
                status = "Active" if row[0] == "A" else "Closed"
                console.print(f"  {status}: {row[1]:,}")
        except Exception:
            console.print("[yellow]No SIRENE data loaded yet[/yellow]")

        # Financial data
        try:
            result = db.fetchone("""
                SELECT
                    COUNT(DISTINCT siren) as companies,
                    COUNT(*) as accounts,
                    MIN(annee_cloture) as min_year,
                    MAX(annee_cloture) as max_year
                FROM inpi_compte_resultat
            """)
            if result and result[0] > 0:
                console.print(f"\n[bold]Financial data:[/bold]")
                console.print(f"  Companies with accounts: {result[0]:,}")
                console.print(f"  Total accounts: {result[1]:,}")
                console.print(f"  Years: {result[2]} - {result[3]}")
        except Exception:
            pass


# =============================================================================
# SIRENE Commands
# =============================================================================

@cli.group()
def sirene():
    """SIRENE data commands (INSEE company registry)."""
    pass


@sirene.command("download")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option(
    "--type", "file_type",
    type=click.Choice(["all", "unites", "etablissements"]),
    default="all",
    help="Which files to download"
)
@click.pass_context
def sirene_download(ctx, output, file_type):
    """Download SIRENE bulk files from data.gouv.fr."""
    from src.extractors.sirene import SireneExtractor

    config = ctx.obj["config"]
    output_dir = Path(output or config["downloads"]["directory"]) / "sirene"

    console.print(f"[cyan]Downloading SIRENE data to:[/cyan] {output_dir}")

    extractor = SireneExtractor(config)
    extractor.download(output_dir, file_type)

    console.print("[green]Download complete![/green]")


@sirene.command("load")
@click.option("--source", "-s", default=None, help="Source directory with Parquet files")
@click.option("--type", "file_type",
    type=click.Choice(["all", "unites", "etablissements"]),
    default="all",
    help="Which data to load"
)
@click.pass_context
def sirene_load(ctx, source, file_type):
    """Load SIRENE data into DuckDB."""
    from src.extractors.sirene import SireneExtractor

    config = ctx.obj["config"]
    source_dir = Path(source or config["downloads"]["directory"]) / "sirene"
    db_path = config["database"]["path"]

    if not source_dir.exists():
        console.print(f"[red]Source directory not found:[/red] {source_dir}")
        console.print("Run 'sirene download' first.")
        return

    console.print(f"[cyan]Loading SIRENE data from:[/cyan] {source_dir}")

    extractor = SireneExtractor(config)
    with DatabaseManager(db_path) as db:
        extractor.load(db, source_dir, file_type)

    console.print("[green]Load complete![/green]")


@sirene.command("sync")
@click.option("--output", "-o", default=None, help="Output directory")
@click.pass_context
def sirene_sync(ctx, output):
    """Download and load SIRENE data (combined operation)."""
    ctx.invoke(sirene_download, output=output, file_type="all")
    ctx.invoke(sirene_load, source=output, file_type="all")


# =============================================================================
# INPI Commands
# =============================================================================

@cli.group()
def inpi():
    """INPI data commands (annual accounts)."""
    pass


@inpi.command("download")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--year", "-y", type=int, help="Specific year to download")
@click.option("--years", help="Year range (e.g., '2020-2024')")
@click.option("--source", type=click.Choice(["mirror", "sftp"]), default="mirror",
              help="Data source (mirror recommended, sftp often unavailable)")
@click.option("--max-files", type=int, default=None, help="Max files per year (for testing)")
@click.pass_context
def inpi_download(ctx, output, year, years, source, max_files):
    """Download INPI annual accounts data.

    The mirror source (data.cquest.org) is recommended as the official SFTP
    is often unavailable. Mirror has data from 2017-2023.
    """
    from src.extractors.inpi import INPIExtractor

    config = ctx.obj["config"]
    output_dir = Path(output or config["downloads"]["directory"]) / "inpi"

    # Determine years to download
    if year:
        years_list = [year]
    elif years:
        start, end = map(int, years.split("-"))
        years_list = list(range(start, end + 1))
    else:
        years_list = config.get("inpi", {}).get("years_to_sync", [2023])

    console.print(f"[cyan]Downloading INPI data for years:[/cyan] {years_list}")
    console.print(f"[cyan]Output directory:[/cyan] {output_dir}")
    console.print(f"[cyan]Source:[/cyan] {source}")

    extractor = INPIExtractor(config)

    if source == "mirror":
        extractor.download_mirror(output_dir, years_list, max_files_per_year=max_files)
    else:
        extractor.download(output_dir, years_list)

    console.print("[green]Download complete![/green]")


@inpi.command("load")
@click.option("--source", "-s", default=None, help="Source directory")
@click.option("--year", "-y", type=int, help="Specific year to load")
@click.option("--format", "data_format", type=click.Choice(["xml", "json"]), default="xml",
              help="Data format (xml for mirror, json for sftp)")
@click.pass_context
def inpi_load(ctx, source, year, data_format):
    """Load INPI data into DuckDB.

    Use --format xml for data downloaded from the mirror (7z archives with XML).
    Use --format json for data downloaded from SFTP (zip archives with JSON).
    """
    from src.extractors.inpi import INPIExtractor

    config = ctx.obj["config"]
    source_dir = Path(source or config["downloads"]["directory"]) / "inpi"
    db_path = config["database"]["path"]

    if not source_dir.exists():
        console.print(f"[red]Source directory not found:[/red] {source_dir}")
        console.print("Run 'inpi download' first.")
        return

    console.print(f"[cyan]Loading INPI data from:[/cyan] {source_dir}")
    console.print(f"[cyan]Format:[/cyan] {data_format}")

    extractor = INPIExtractor(config)
    with DatabaseManager(db_path) as db:
        if data_format == "xml":
            stats = extractor.load_xml(db, source_dir, year)
        else:
            stats = extractor.load(db, source_dir, year)

    console.print(f"[green]Load complete![/green] Loaded: {stats}")


@inpi.command("sync")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--years", default="2020-2023", help="Year range (2017-2023 available)")
@click.option("--max-files", type=int, default=None, help="Max files per year (for testing)")
@click.pass_context
def inpi_sync(ctx, output, years, max_files):
    """Download and load INPI data (combined operation).

    Uses the data.cquest.org mirror by default (recommended).
    """
    ctx.invoke(inpi_download, output=output, years=years, source="mirror", max_files=max_files)
    ctx.invoke(inpi_load, source=output, data_format="xml")


# =============================================================================
# BODACC Commands
# =============================================================================

@cli.group()
def bodacc():
    """BODACC data commands (legal announcements)."""
    pass


@bodacc.command("download")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--year", "-y", type=int, help="Specific year")
@click.option("--days", "-d", type=int, default=30, help="Number of days to fetch (API mode)")
@click.option("--source", type=click.Choice(["api", "ftps"]), default="api",
              help="Data source (API for recent, FTPS for bulk)")
@click.pass_context
def bodacc_download(ctx, output, year, days, source):
    """Download BODACC announcements."""
    from src.extractors.bodacc import BODACCExtractor

    config = ctx.obj["config"]
    output_dir = Path(output or config["downloads"]["directory"]) / "bodacc"

    console.print(f"[cyan]Downloading BODACC data to:[/cyan] {output_dir}")

    extractor = BODACCExtractor(config)
    extractor.download(output_dir, year=year, days=days, source=source)

    console.print("[green]Download complete![/green]")


@bodacc.command("load")
@click.option("--source", "-s", default=None, help="Source directory")
@click.pass_context
def bodacc_load(ctx, source):
    """Load BODACC data into DuckDB."""
    from src.extractors.bodacc import BODACCExtractor

    config = ctx.obj["config"]
    source_dir = Path(source or config["downloads"]["directory"]) / "bodacc"
    db_path = config["database"]["path"]

    if not source_dir.exists():
        console.print(f"[red]Source directory not found:[/red] {source_dir}")
        console.print("Run 'bodacc download' first.")
        return

    console.print(f"[cyan]Loading BODACC data from:[/cyan] {source_dir}")

    extractor = BODACCExtractor(config)
    with DatabaseManager(db_path) as db:
        extractor.load(db, source_dir)

    console.print("[green]Load complete![/green]")


@bodacc.command("sync")
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--days", "-d", type=int, default=30, help="Number of days to fetch")
@click.pass_context
def bodacc_sync(ctx, output, days):
    """Download and load BODACC data (combined operation)."""
    ctx.invoke(bodacc_download, output=output, days=days)
    ctx.invoke(bodacc_load, source=output)


# =============================================================================
# Query Commands
# =============================================================================

@cli.command("search")
@click.option("--name", "-n", help="Search by company name")
@click.option("--siren", "-s", help="Search by SIREN")
@click.option("--naf", help="Filter by NAF/APE code")
@click.option("--departement", "-d", help="Filter by department")
@click.option("--limit", "-l", type=int, default=20, help="Max results")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "csv"]),
              default="table", help="Output format")
@click.pass_context
def search(ctx, name, siren, naf, departement, limit, output_format):
    """Search for companies."""
    import json

    config = ctx.obj["config"]
    db_path = config["database"]["path"]

    if not Path(db_path).exists():
        console.print(f"[red]Database not found:[/red] {db_path}")
        return

    # Build query
    conditions = ["ul.etat_administratif = 'A'"]
    params = []

    if name:
        conditions.append("ul.denomination ILIKE ?")
        params.append(f"%{name}%")
    if siren:
        conditions.append("ul.siren = ?")
        params.append(siren)
    if naf:
        conditions.append("ul.activite_principale = ?")
        params.append(naf)
    if departement:
        conditions.append("e.departement = ?")
        params.append(departement)

    where = " AND ".join(conditions)

    query = f"""
        SELECT
            ul.siren,
            ul.denomination,
            ul.activite_principale,
            ul.tranche_effectifs,
            e.code_postal,
            e.libelle_commune
        FROM sirene_unites_legales ul
        LEFT JOIN sirene_etablissements e
            ON ul.siren = e.siren AND e.etablissement_siege = 'true'
        WHERE {where}
        LIMIT ?
    """
    params.append(limit)

    with DatabaseManager(db_path) as db:
        results = db.fetchall(query, params)

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    if output_format == "json":
        data = [
            {
                "siren": r[0],
                "denomination": r[1],
                "naf": r[2],
                "effectifs": r[3],
                "code_postal": r[4],
                "commune": r[5],
            }
            for r in results
        ]
        console.print(json.dumps(data, indent=2, ensure_ascii=False))
    elif output_format == "csv":
        console.print("siren,denomination,naf,effectifs,code_postal,commune")
        for r in results:
            console.print(",".join(str(v or "") for v in r))
    else:
        table = Table(title=f"Search Results ({len(results)} companies)")
        table.add_column("SIREN", style="cyan")
        table.add_column("Denomination")
        table.add_column("NAF")
        table.add_column("Effectifs")
        table.add_column("CP")
        table.add_column("Commune")

        for r in results:
            table.add_row(*(str(v or "-") for v in r))

        console.print(table)


@cli.command("export")
@click.option("--query", "-q", required=True, help="SQL query to export")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--format", "output_format", type=click.Choice(["parquet", "csv", "json"]),
              default="parquet", help="Output format")
@click.pass_context
def export(ctx, query, output, output_format):
    """Export query results to file."""
    config = ctx.obj["config"]
    db_path = config["database"]["path"]
    output_path = Path(output)

    if not Path(db_path).exists():
        console.print(f"[red]Database not found:[/red] {db_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with DatabaseManager(db_path) as db:
        if output_format == "parquet":
            db.execute(f"COPY ({query}) TO '{output_path}' (FORMAT PARQUET)")
        elif output_format == "csv":
            db.execute(f"COPY ({query}) TO '{output_path}' (FORMAT CSV, HEADER)")
        else:
            db.execute(f"COPY ({query}) TO '{output_path}' (FORMAT JSON)")

    console.print(f"[green]Exported to:[/green] {output_path}")


if __name__ == "__main__":
    cli()
