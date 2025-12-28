"""
Script de test pour vérifier la connexion à l'API Pappers
"""

import os
import sys

# Ajoute le répertoire parent au path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from src.data.pappers_client import PappersClient, PappersAPIError


def test_connection():
    """Teste la connexion à l'API Pappers"""

    print("=" * 60)
    print("TEST DE CONNEXION - API PAPPERS")
    print("=" * 60)
    print()

    # Charge .env
    load_dotenv()

    # Vérifie la clé API
    api_key = os.getenv('PAPPERS_API_KEY')

    if not api_key:
        print("❌ ERREUR: Clé API Pappers manquante")
        print()
        print("Actions à faire :")
        print("1. Créez un compte sur https://www.pappers.fr/api")
        print("2. Récupérez votre clé API")
        print("3. Ajoutez-la dans le fichier .env :")
        print("   PAPPERS_API_KEY=votre_cle_ici")
        return False

    print(f"✅ Clé API trouvée : {api_key[:10]}...{api_key[-4:]}")
    print()

    # Teste la connexion
    try:
        print("Initialisation du client...")
        client = PappersClient(api_key=api_key)
        print("✅ Client initialisé")
        print()

        # Test avec une entreprise connue (Total Energies)
        test_siren = "552032534"
        print(f"Test de récupération de données pour SIREN {test_siren}...")

        data = client.get_entreprise(test_siren)

        print("✅ Données récupérées avec succès !")
        print()

        # Affiche quelques infos
        print("-" * 60)
        print("INFORMATIONS RÉCUPÉRÉES :")
        print("-" * 60)
        print(f"Dénomination : {data.get('nom_entreprise', 'N/A')}")
        print(f"SIREN        : {data.get('siren', 'N/A')}")
        print(f"Forme        : {data.get('forme_juridique', 'N/A')}")
        print(f"Ville        : {data.get('siege', {}).get('ville', 'N/A')}")

        # Vérifie les finances
        finances = data.get('finances', [])
        if finances:
            print(f"\nDonnées financières disponibles : {len(finances)} exercices")
            dernier = finances[0]
            print(f"Dernier exercice : {dernier.get('date_cloture_exercice', 'N/A')}")

            ca = dernier.get('chiffre_affaires')
            if ca:
                print(f"Chiffre d'affaires : {ca:,.0f} €")

        # Vérifie les dirigeants
        dirigeants = data.get('representants', [])
        if dirigeants:
            print(f"\nDirigeants trouvés : {len(dirigeants)}")

        print()
        print("=" * 60)
        print("✅ CONNEXION RÉUSSIE - API FONCTIONNELLE")
        print("=" * 60)
        print()
        print("Vous pouvez maintenant utiliser l'application !")
        print("Lancez : python analyze_companies.py")
        print()

        return True

    except PappersAPIError as e:
        print()
        print("❌ ERREUR API PAPPERS")
        print(f"Message : {e}")
        print()

        if "Clé API invalide" in str(e):
            print("Actions à faire :")
            print("1. Vérifiez que votre clé est correcte")
            print("2. Vérifiez qu'elle est active sur pappers.fr")
            print("3. Vérifiez qu'elle n'a pas expiré")

        return False

    except Exception as e:
        print()
        print("❌ ERREUR INATTENDUE")
        print(f"Message : {e}")
        print()
        print("Vérifiez :")
        print("- Votre connexion internet")
        print("- Les dépendances installées (pip install -r requirements.txt)")

        return False


if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
