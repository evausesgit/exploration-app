#!/usr/bin/env python3
"""
Synchronise les résultats du scan vers l'application web pour déploiement Vercel
"""

import shutil
from pathlib import Path
import sys

# Chemins
project_root = Path(__file__).parent.parent.parent
source_file = project_root / "companies-analysis" / "data" / "automation_opportunities.json"
dest_file = project_root / "web" / "public" / "data" / "automation_opportunities.json"

# Vérifier que le fichier source existe
if not source_file.exists():
    print(f"❌ Fichier source non trouvé: {source_file}")
    sys.exit(1)

# Créer le dossier de destination si nécessaire
dest_file.parent.mkdir(parents=True, exist_ok=True)

# Copier le fichier
try:
    shutil.copy2(source_file, dest_file)
    print(f"✅ Données synchronisées vers l'application web")
    print(f"   Source: {source_file}")
    print(f"   Destination: {dest_file}")
    print(f"\n💡 Commit et push pour déployer sur Vercel!")
except Exception as e:
    print(f"❌ Erreur lors de la synchronisation: {e}")
    sys.exit(1)
