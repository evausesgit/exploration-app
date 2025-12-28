"""
Point d'entrée principal du Crypto Opportunity Scanner

Usage:
    python main.py --scan             # Lance un scan unique
    python main.py --watch            # Scan continu
    python main.py --dashboard        # Lance le dashboard
"""

import os
import sys


import argparse
import yaml
import time
import sys
from pathlib import Path
from loguru import logger

from src.strategies.arbitrage import CryptoArbitrageScanner
from src.data.storage import OpportunityStorage


def load_config(config_path: str = "config/config.yaml") -> dict:
    """
    Charge la configuration depuis le fichier YAML

    Args:
        config_path: Chemin vers le fichier de config

    Returns:
        Dict de configuration
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found, using defaults")
        return {}


def setup_logging(config: dict):
    """Configure le système de logging"""
    log_level = config.get('logging', {}).get('level', 'INFO')
    log_file = config.get('logging', {}).get('file', 'logs/scanner.log')

    # Crée le dossier logs
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Configure loguru
    logger.remove()  # Retire le handler par défaut

    # Console
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )

    # Fichier
    logger.add(
        log_file,
        level=log_level,
        rotation="10 MB",
        retention="1 week",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
    )


def run_single_scan(config: dict):
    """
    Lance un scan unique

    Args:
        config: Configuration
    """
    logger.info("=" * 60)
    logger.info("Starting Single Scan")
    logger.info("=" * 60)

    # Initialise le storage
    db_path = config.get('database', {}).get('path', 'data/opportunities.db')
    storage = OpportunityStorage(db_path)

    # Configure le scanner
    scanner_config = {
        'exchanges': config.get('exchanges', ['binance', 'kraken', 'coinbase']),
        'symbols': config.get('symbols', ['BTC/USDT', 'ETH/USDT']),
        **config.get('scanner', {})
    }

    # Lance le scanner d'arbitrage
    scanner = CryptoArbitrageScanner(scanner_config)
    opportunities = scanner.run_scan()

    # Sauvegarde
    if opportunities:
        storage.save_batch(opportunities)
        logger.success(f"Found and saved {len(opportunities)} opportunities")

        # Affiche les meilleures
        best = sorted(opportunities, key=lambda x: x.profit_potential, reverse=True)[:5]
        logger.info("\nTop 5 Opportunities:")
        for i, opp in enumerate(best, 1):
            logger.info(
                f"{i}. {opp.symbol}: {opp.profit_potential:.2f}% "
                f"({opp.data.get('buy_exchange')} → {opp.data.get('sell_exchange')})"
            )
    else:
        logger.info("No opportunities found")

    logger.info("=" * 60)


def run_continuous_scan(config: dict):
    """
    Lance un scan continu

    Args:
        config: Configuration
    """
    logger.info("=" * 60)
    logger.info("Starting Continuous Scanning")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    # Initialise le storage
    db_path = config.get('database', {}).get('path', 'data/opportunities.db')
    storage = OpportunityStorage(db_path)

    # Configure le scanner
    scanner_config = {
        'exchanges': config.get('exchanges', ['binance', 'kraken', 'coinbase']),
        'symbols': config.get('symbols', ['BTC/USDT', 'ETH/USDT']),
        **config.get('scanner', {})
    }

    scanner = CryptoArbitrageScanner(scanner_config)

    # Intervalle entre scans
    scan_interval = config.get('scanner', {}).get('scan_interval', 60)

    scan_count = 0

    try:
        while True:
            scan_count += 1
            logger.info(f"\n--- Scan #{scan_count} ---")

            # Lance le scan
            opportunities = scanner.run_scan()

            # Sauvegarde
            if opportunities:
                storage.save_batch(opportunities)
                best = max(opportunities, key=lambda x: x.profit_potential)
                logger.success(
                    f"Found {len(opportunities)} opportunities. "
                    f"Best: {best.symbol} {best.profit_potential:.2f}%"
                )
            else:
                logger.info("No opportunities found")

            # Attends avant le prochain scan
            logger.info(f"Next scan in {scan_interval}s...")
            time.sleep(scan_interval)

    except KeyboardInterrupt:
        logger.info("\nStopping scanner...")
        logger.info(f"Total scans completed: {scan_count}")


def run_dashboard():
    """Lance le dashboard Streamlit"""
    import subprocess

    logger.info("Starting dashboard...")
    logger.info("Dashboard will open in your browser at http://localhost:8501")

    subprocess.run([
        "streamlit", "run",
        "src/visualization/dashboard.py",
        "--server.headless", "true"
    ])


def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Crypto Opportunity Scanner")

    parser.add_argument(
        '--scan',
        action='store_true',
        help='Run a single scan'
    )

    parser.add_argument(
        '--watch',
        action='store_true',
        help='Run continuous scanning'
    )

    parser.add_argument(
        '--dashboard',
        action='store_true',
        help='Launch the visualization dashboard'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to config file (default: config/config.yaml)'
    )

    args = parser.parse_args()

    # Charge la config
    config = load_config(args.config)

    # Setup logging
    setup_logging(config)

    # Execute la commande
    if args.dashboard:
        run_dashboard()
    elif args.watch:
        run_continuous_scan(config)
    elif args.scan:
        run_single_scan(config)
    else:
        logger.info("No action specified. Use --scan, --watch, or --dashboard")
        logger.info("Run 'python main.py --help' for more information")


if __name__ == "__main__":
    main()
