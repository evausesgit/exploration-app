#!/usr/bin/env python3
"""Simple script to extract INPI data to Parquet files."""
import sys
sys.path.insert(0, '.')

from pathlib import Path
from src.extractors.inpi import INPIExtractor

def main():
    extractor = INPIExtractor()

    source_dir = Path("data/downloads/inpi")
    output_dir = Path("data/parquet")

    # Check if we have downloaded data
    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        print("Run download first")
        return

    # Extract all years to Parquet
    print(f"Extracting INPI data from {source_dir} to {output_dir}")
    stats = extractor.extract_to_parquet(source_dir, output_dir)

    print("\n=== DONE ===")
    for year, count in sorted(stats.items()):
        print(f"  {year}: {count:,} records")

    total = sum(stats.values())
    print(f"  TOTAL: {total:,} records")
    print(f"\nParquet files in: {output_dir}")

if __name__ == "__main__":
    main()
