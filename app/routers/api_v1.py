from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import User, ContentRequest, GeneratedContent, UsageAnalytics, Platform
from app.auth_api import get_current_user_from_api_key
from app.ai_service import polish_content_multi_format
from app.plan_config import PLAN_LIMITS

router = APIRouter(prefix="/api/v1", tags=["API v1"])


# Schemas
class ContentGenerateRequest(BaseModel):
    text: str
    platform: str  # linkedin, instagram, tiktok, facebook, twitter, multi_format
    tone: Optional[str] = "professional"  # casual, professional, engaging
    language: Optional[str] = "fr"  # fr, en, es


class GeneratedContentResponse(BaseModel):
    id: int
    polished_text: str
    format_name: Optional[str]
    variant_number: int
    created_at: datetime

    class Config:
        from_attributes = True


class ContentGenerateResponse(BaseModel):
    request_id: int
    original_text: str
    platform: str
    variants: List[GeneratedContentResponse]
    credits_used: int
    credits_remaining: int


class ContentHistoryItem(BaseModel):
    id: int
    original_text: str
    platform: str
    created_at: datetime
    variants_count: int

    class Config:
        from_attributes = True


# Endpoints
@router.post("/generate", response_model=ContentGenerateResponse)
async def generate_content(
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_user_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Génère du contenu poli pour une plateforme spécifique.

    Authentification: Nécessite une clé API Business (Authorization: Bearer acp_live_xxxxx)

    Args:
        text: Le texte original à polir
        platform: La plateforme cible (linkedin, instagram, tiktok, facebook, twitter, multi_format)
        tone: Le ton souhaité (casual, professional, engaging) - optionnel, défaut: professional
        language: La langue (fr, en, es) - optionnel, défaut: fr

    Returns:
        Le contenu généré avec ses variantes, et le nombre de crédits restants
    """
    # Vérifier les crédits
    plan_config = PLAN_LIMITS.get(current_user.current_plan, PLAN_LIMITS["free"])

    if current_user.credits_remaining < 1:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient credits. You have {current_user.credits_remaining} credits remaining."
        )

    # Valider la plateforme
    valid_platforms = ["linkedin", "instagram", "tiktok", "facebook", "twitter", "multi_format"]
    if request.platform not in valid_platforms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}"
        )

    # Créer la requête de contenu
    content_request = ContentRequest(
        user_id=current_user.id,
        original_text=request.text,
        platform=request.platform,
        tone=request.tone,
        language=request.language
    )
    db.add(content_request)
    db.commit()
    db.refresh(content_request)

    # Générer le contenu avec l'AI
    try:
        formats_dict, tokens_used = polish_content_multi_format(
            original_text=request.text,
            tone=request.tone or "professional",
            language=request.language or "fr",
            user_plan=current_user.current_plan
        )

        # Convertir les formats en variantes
        # Pour l'API, on prend le format correspondant à la plateforme demandée
        variants = []
        if request.platform == "multi_format":
            # Si multi_format, on retourne tous les formats
            for format_name, format_content in formats_dict.items():
                if isinstance(format_content, list):
                    # Plusieurs variantes (Pro/Business)
                    for idx, variant_text in enumerate(format_content, 1):
                        variants.append({
                            "text": variant_text,
                            "format": format_name
                        })
                else:
                    # Une seule variante (Free)
                    variants.append({
                        "text": format_content,
                        "format": format_name
                    })
        else:
            # Si plateforme spécifique, on retourne uniquement ce format
            platform_content = formats_dict.get(request.platform)
            if platform_content:
                if isinstance(platform_content, list):
                    for idx, variant_text in enumerate(platform_content, 1):
                        variants.append({
                            "text": variant_text,
                            "format": request.platform
                        })
                else:
                    variants.append({
                        "text": platform_content,
                        "format": request.platform
                    })

        # Sauvegarder les variantes générées
        generated_variants = []
        for idx, variant in enumerate(variants, 1):
            gen_content = GeneratedContent(
                request_id=content_request.id,
                polished_text=variant["text"],
                format_name=variant.get("format"),
                variant_number=idx
            )
            db.add(gen_content)
            generated_variants.append(gen_content)

        # Déduire un crédit
        current_user.credits_remaining -= 1

        # Sauvegarder les analytics
        analytics = UsageAnalytics(
            user_id=current_user.id,
            tokens_used=tokens_used,
            platform=Platform(request.platform) if request.platform != "multi_format" else None
        )
        db.add(analytics)

        db.commit()

        # Rafraîchir pour obtenir les IDs
        for variant in generated_variants:
            db.refresh(variant)

        return ContentGenerateResponse(
            request_id=content_request.id,
            original_text=request.text,
            platform=request.platform,
            variants=[GeneratedContentResponse.from_orm(v) for v in generated_variants],
            credits_used=1,
            credits_remaining=current_user.credits_remaining
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating content: {str(e)}"
        )


@router.get("/content", response_model=List[ContentHistoryItem])
async def get_content_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Récupère l'historique des contenus générés.

    Authentification: Nécessite une clé API Business

    Args:
        limit: Nombre maximum de résultats (défaut: 50, max: 100)
        offset: Nombre de résultats à sauter (pagination)

    Returns:
        Liste de l'historique des contenus générés
    """
    # Limiter le limit à 100
    if limit > 100:
        limit = 100

    # Récupérer les requêtes de contenu
    requests = db.query(ContentRequest).filter(
        ContentRequest.user_id == current_user.id
    ).order_by(
        ContentRequest.created_at.desc()
    ).limit(limit).offset(offset).all()

    # Compter les variantes pour chaque requête
    results = []
    for req in requests:
        variants_count = db.query(GeneratedContent).filter(
            GeneratedContent.request_id == req.id
        ).count()

        results.append(ContentHistoryItem(
            id=req.id,
            original_text=req.original_text,
            platform=req.platform,
            created_at=req.created_at,
            variants_count=variants_count
        ))

    return results


@router.get("/content/{request_id}", response_model=ContentGenerateResponse)
async def get_content_by_id(
    request_id: int,
    current_user: User = Depends(get_current_user_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Récupère un contenu généré spécifique par son ID.

    Authentification: Nécessite une clé API Business

    Args:
        request_id: L'ID de la requête de contenu

    Returns:
        Le contenu généré avec toutes ses variantes
    """
    # Récupérer la requête
    content_req = db.query(ContentRequest).filter(
        ContentRequest.id == request_id,
        ContentRequest.user_id == current_user.id
    ).first()

    if not content_req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )

    # Récupérer les variantes
    variants = db.query(GeneratedContent).filter(
        GeneratedContent.request_id == request_id
    ).order_by(GeneratedContent.variant_number).all()

    return ContentGenerateResponse(
        request_id=content_req.id,
        original_text=content_req.original_text,
        platform=content_req.platform,
        variants=[GeneratedContentResponse.from_orm(v) for v in variants],
        credits_used=1,
        credits_remaining=current_user.credits_remaining
    )
