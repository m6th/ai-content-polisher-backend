import secrets
import hashlib
from datetime import datetime

def generate_api_key() -> tuple[str, str, str]:
    """
    Génère une nouvelle clé API avec le format: acp_live_<32_caractères_aléatoires>

    Returns:
        tuple: (full_key, key_prefix, key_hash)
            - full_key: La clé complète à afficher une seule fois à l'utilisateur
            - key_prefix: Les 20 premiers caractères pour l'identification
            - key_hash: Le hash SHA256 de la clé complète pour stockage sécurisé
    """
    # Générer 32 caractères aléatoires sécurisés
    random_part = secrets.token_urlsafe(24)  # Génère ~32 caractères en base64url

    # Format: acp_live_<random>
    full_key = f"acp_live_{random_part}"

    # Prefix: premiers 20 caractères pour identification (acp_live_abc123...)
    key_prefix = full_key[:20]

    # Hash SHA256 de la clé complète pour stockage sécurisé
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    return full_key, key_prefix, key_hash


def hash_api_key(api_key: str) -> str:
    """
    Hash une clé API avec SHA256

    Args:
        api_key: La clé API complète

    Returns:
        str: Le hash SHA256 de la clé
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_api_key_format(api_key: str) -> bool:
    """
    Valide le format d'une clé API

    Args:
        api_key: La clé à valider

    Returns:
        bool: True si le format est valide
    """
    if not api_key:
        return False

    # Doit commencer par "acp_live_"
    if not api_key.startswith("acp_live_"):
        return False

    # Doit avoir une longueur raisonnable (au moins 20 caractères)
    if len(api_key) < 20:
        return False

    return True


def get_key_prefix(api_key: str) -> str:
    """
    Extrait le prefix d'une clé API (premiers 20 caractères)

    Args:
        api_key: La clé API complète

    Returns:
        str: Le prefix de la clé
    """
    return api_key[:20] if len(api_key) >= 20 else api_key
