import os
from fastapi import HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
print(f"GOOGLE_CLIENT_ID chargé: {GOOGLE_CLIENT_ID[:20] if GOOGLE_CLIENT_ID else 'NON DÉFINI'}...")

async def verify_google_token(token: str):
    """
    Vérifie le JWT Google et retourne les infos utilisateur
    """
    try:
        print(f"Vérification token avec CLIENT_ID: {GOOGLE_CLIENT_ID[:30] if GOOGLE_CLIENT_ID else 'NONE'}...")

        if not GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID non configuré sur le serveur")

        # Vérifie le JWT directement avec la bibliothèque Google
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        print(f"Token vérifié avec succès pour: {idinfo.get('email')}")

        # Vérifie que le token vient bien de Google
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        return {
            "email": idinfo.get("email"),
            "name": idinfo.get("name"),
            "google_id": idinfo.get("sub")
        }

    except ValueError as e:
        print(f"ERREUR ValueError: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Token invalide: {str(e)}")
    except Exception as e:
        print(f"ERREUR Exception: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=401, detail=f"Erreur validation token: {str(e)}")