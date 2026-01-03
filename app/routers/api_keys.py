from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import User, APIKey
from app.auth import get_current_user
from app.utils.api_keys import generate_api_key

router = APIRouter(prefix="/api/keys", tags=["API Keys"])


# Schemas
class APIKeyCreate(BaseModel):
    name: str  # Nom de la clé (ex: "Production Server", "Development")


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str  # Afficher seulement le prefix (ex: acp_live_abc123...)
    created_at: datetime
    last_used_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Response après création - contient la clé complète UNE SEULE FOIS"""
    id: int
    name: str
    api_key: str  # La clé complète - affichée UNE SEULE FOIS
    key_prefix: str
    created_at: datetime
    message: str = "⚠️ Save this API key now. You won't be able to see it again!"

    class Config:
        from_attributes = True


# Endpoints
@router.post("/", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crée une nouvelle clé API pour l'utilisateur Business.

    ⚠️ La clé complète est retournée UNE SEULE FOIS à la création.
    Elle ne pourra plus jamais être récupérée après.
    """
    # Vérifier que l'utilisateur est Business
    if current_user.current_plan != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys are only available for Business plan users. Upgrade to Business to unlock API access."
        )

    # Générer la clé
    full_key, key_prefix, key_hash = generate_api_key()

    # Créer l'entrée en BDD
    new_api_key = APIKey(
        user_id=current_user.id,
        name=key_data.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        is_active=True
    )

    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)

    # Retourner la clé complète (UNE SEULE FOIS)
    return APIKeyCreateResponse(
        id=new_api_key.id,
        name=new_api_key.name,
        api_key=full_key,  # 🔑 Clé complète affichée UNE SEULE FOIS
        key_prefix=key_prefix,
        created_at=new_api_key.created_at
    )


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Liste toutes les clés API de l'utilisateur connecté.

    Note: Les clés complètes ne sont jamais retournées, seulement les prefixes.
    """
    # Vérifier que l'utilisateur est Business
    if current_user.current_plan != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys are only available for Business plan users"
        )

    api_keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id
    ).order_by(APIKey.created_at.desc()).all()

    return api_keys


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Révoque (désactive) une clé API.

    La clé sera marquée comme inactive et ne pourra plus être utilisée.
    """
    # Vérifier que l'utilisateur est Business
    if current_user.current_plan != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys are only available for Business plan users"
        )

    # Trouver la clé
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Révoquer la clé (soft delete)
    api_key.is_active = False
    db.commit()

    return None


@router.delete("/{key_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key_permanently(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Supprime définitivement une clé API de la base de données.

    Cette action est irréversible.
    """
    # Vérifier que l'utilisateur est Business
    if current_user.current_plan != "business":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys are only available for Business plan users"
        )

    # Trouver la clé
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Supprimer définitivement
    db.delete(api_key)
    db.commit()

    return None
