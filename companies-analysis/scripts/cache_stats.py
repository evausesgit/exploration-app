#!/usr/bin/env python3
"""
Affiche les statistiques du cache Pappers
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.pappers_cache import PappersCache
from pathlib import Path

cache = PappersCache()
stats = cache.get_stats()

print("=" * 60)
print("📊 STATISTIQUES DU CACHE PAPPERS")
print("=" * 60)
print(f"\n💾 Emplacement : {stats['cache_path']}")

cache_path = Path(stats['cache_path'])
if cache_path.exists():
    size_bytes = cache_path.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024

    if size_mb >= 1:
        print(f"📦 Taille      : {size_mb:.2f} MB")
    else:
        print(f"📦 Taille      : {size_kb:.1f} KB")

print(f"\n🏢 Entreprises cachées : {stats['entreprises']}")
print(f"🔍 Recherches cachées  : {stats['recherches']}")

total_cached = stats['entreprises'] + stats['recherches']
print(f"\n💰 Économies estimées  : ~{total_cached} crédits API")

print("\n" + "=" * 60)
print("ℹ️  Le cache est valide 30 jours pour les entreprises")
print("ℹ️  Le cache est valide 7 jours pour les recherches")
print("=" * 60)
