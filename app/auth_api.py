from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import User, APIKey
from app.utils.api_keys import hash_api_key, validate_api_key_format, get_key_prefix

security = HTTPBearer()


async def get_current_user_from_api_key(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Authentifie un utilisateur via sa clé API

    Args:
        authorization: Header Authorization avec format "Bearer acp_live_xxxxx"
        db: Session de base de données

    Returns:
        User: L'utilisateur authentifié

    Raises:
        HTTPException: Si la clé est invalide, inactive, ou l'utilisateur n'est pas Business
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Use: Authorization: Bearer acp_live_xxxxx"
        )

    # Extraire le token du header "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use: Authorization: Bearer acp_live_xxxxx"
        )

    api_key = authorization.replace("Bearer ", "").strip()

    # Valider le format
    if not validate_api_key_format(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )

    # Obtenir le prefix de la clé
    key_prefix = get_key_prefix(api_key)

    # Hasher la clé complète
    key_hash = hash_api_key(api_key)

    # Rechercher la clé dans la BDD par prefix (index)
    db_api_key = db.query(APIKey).filter(
        APIKey.key_prefix == key_prefix
    ).first()

    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Vérifier le hash complet
    if db_api_key.key_hash != key_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Vérifier que la clé est active
    if not db_api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked"
        )

    # Charger l'utilisateur
    user = db.query(User).filter(User.id == db_api_key.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Vérifier que l'utilisateur est Business
    if user.current_plan != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API access is only available for Business plan users"
        )

    # Mettre à jour last_used_at (asynchrone, ne pas bloquer)
    db_api_key.last_used_at = datetime.utcnow()
    db.commit()

    return user


async def require_business_plan(
    current_user: User = Depends(get_current_user_from_api_key)
) -> User:
    """
    Vérifie que l'utilisateur a un plan Business (redondant mais explicite)

    Args:
        current_user: L'utilisateur déjà authentifié

    Returns:
        User: L'utilisateur si Business

    Raises:
        HTTPException: Si l'utilisateur n'est pas Business
    """
    if current_user.current_plan != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires a Business plan"
        )
    return current_user
