from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import json

from app.database import get_db
from app.models import User, UserStyleProfile, UserOnboarding
from app.auth import get_current_user

router = APIRouter(prefix="/styles", tags=["Style Profiles"])

# Pydantic schemas
class StyleProfileCreate(BaseModel):
    style_type: str  # 'personal' or 'creator'
    source_url: str
    style_name: Optional[str] = None  # Auto-généré si non fourni

class StyleProfileResponse(BaseModel):
    id: int
    style_name: str
    style_type: str
    platform: Optional[str]
    source_url: str
    status: str
    error_message: Optional[str]
    last_analyzed_at: Optional[datetime]
    created_at: datetime

class AvailableTone(BaseModel):
    id: str  # 'professional', 'casual', 'custom_123', etc.
    name: str  # 'Professionnel', 'Mon style LinkedIn', etc.
    type: str  # 'predefined' or 'custom'
    status: Optional[str] = None  # Pour custom: 'pending', 'analyzing', 'ready', 'failed'
    platform: Optional[str] = None  # Pour custom personal: 'linkedin', 'instagram', etc.

# Tons prédéfinis (4 tons optimisés pour la conversion)
PREDEFINED_TONES = [
    {"id": "professional", "name": "Professionnel", "type": "predefined"},
    {"id": "storytelling", "name": "Storytelling", "type": "predefined"},
    {"id": "engaging", "name": "Engageant", "type": "predefined"},
    {"id": "educational", "name": "Éducatif", "type": "predefined"},
]

@router.get("/available-tones", response_model=List[AvailableTone])
def get_available_tones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retourne tous les tons disponibles pour l'utilisateur :
    - Tons prédéfinis (4 styles optimisés)
    - Styles personnels de l'utilisateur (provenant de ses réseaux sociaux)
    """
    # Commencer avec les tons prédéfinis
    tones = PREDEFINED_TONES.copy()

    # Récupérer les profils de style custom de l'utilisateur
    custom_profiles = db.query(UserStyleProfile).filter(
        UserStyleProfile.user_id == current_user.id
    ).all()

    # Ajouter les styles custom
    for profile in custom_profiles:
        tones.append({
            "id": f"custom_{profile.id}",
            "name": profile.style_name,
            "type": "custom",
            "status": profile.status,
            "platform": profile.platform
        })

    return tones

@router.get("/my-profiles", response_model=List[StyleProfileResponse])
def get_my_style_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère tous les profils de style de l'utilisateur"""
    profiles = db.query(UserStyleProfile).filter(
        UserStyleProfile.user_id == current_user.id
    ).order_by(UserStyleProfile.created_at.desc()).all()

    return profiles

@router.post("/create", response_model=StyleProfileResponse)
def create_style_profile(
    data: StyleProfileCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée un nouveau profil de style personnalisé.
    Lance l'analyse en arrière-plan.
    """
    # Détecter la plateforme depuis l'URL
    platform = detect_platform_from_url(data.source_url)

    # Générer le nom du style si non fourni
    if not data.style_name:
        if data.style_type == 'personal':
            platform_names = {
                'linkedin': 'LinkedIn',
                'instagram': 'Instagram',
                'facebook': 'Facebook',
                'twitter': 'Twitter',
                'tiktok': 'TikTok',
                'youtube': 'YouTube'
            }
            data.style_name = f"Mon style {platform_names.get(platform, platform.title())}"
        else:
            data.style_name = "Style d'un créateur"

    # Vérifier si un profil similaire existe déjà
    existing = db.query(UserStyleProfile).filter(
        UserStyleProfile.user_id == current_user.id,
        UserStyleProfile.source_url == data.source_url
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Un profil existe déjà pour cette URL")

    # Créer le profil
    profile = UserStyleProfile(
        user_id=current_user.id,
        style_name=data.style_name,
        style_type=data.style_type,
        platform=platform,
        source_url=data.source_url,
        status="pending"
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Lancer l'analyse en arrière-plan
    background_tasks.add_task(analyze_style_profile, profile.id, db)

    return profile

@router.delete("/{profile_id}")
def delete_style_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprime un profil de style"""
    profile = db.query(UserStyleProfile).filter(
        UserStyleProfile.id == profile_id,
        UserStyleProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")

    db.delete(profile)
    db.commit()

    return {"message": "Profil supprimé avec succès"}

@router.post("/{profile_id}/reanalyze")
def reanalyze_style_profile(
    profile_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Relance l'analyse d'un profil de style"""
    profile = db.query(UserStyleProfile).filter(
        UserStyleProfile.id == profile_id,
        UserStyleProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")

    profile.status = "pending"
    profile.error_message = None
    db.commit()

    background_tasks.add_task(analyze_style_profile, profile_id, db)

    return {"message": "Analyse relancée"}

# Helper functions
def detect_platform_from_url(url: str) -> str:
    """Détecte la plateforme depuis l'URL"""
    url_lower = url.lower()

    if 'linkedin.com' in url_lower:
        return 'linkedin'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'facebook.com' in url_lower:
        return 'facebook'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'youtube.com' in url_lower:
        return 'youtube'
    else:
        return 'unknown'

def analyze_style_profile(profile_id: int, db: Session):
    """
    Analyse un profil de style en arrière-plan.
    Scrape les posts et analyse le style d'écriture avec l'IA.
    """
    from app.scraper_service import analyze_style_from_url
    from app.database import SessionLocal

    # Créer une nouvelle session DB pour le thread background
    db_session = SessionLocal()

    try:
        # Récupérer le profil
        profile = db_session.query(UserStyleProfile).filter(
            UserStyleProfile.id == profile_id
        ).first()

        if not profile:
            print(f"❌ Profile {profile_id} not found")
            return

        # Marquer comme "analyzing"
        profile.status = "analyzing"
        db_session.commit()

        print(f"🔄 Starting analysis for profile {profile_id} ({profile.platform})")

        # Lancer le scraping et l'analyse
        result = analyze_style_from_url(
            source_url=profile.source_url,
            platform=profile.platform,
            style_type=profile.style_type,
            max_posts=10
        )

        # Mettre à jour le profil avec les résultats
        profile.status = result['status']
        profile.style_analysis = result.get('style_analysis')
        profile.sample_posts = result.get('sample_posts')
        profile.error_message = result.get('error_message')
        profile.last_analyzed_at = datetime.utcnow()

        db_session.commit()
        print(f"✅ Analysis completed for profile {profile_id}: {profile.status}")

    except Exception as e:
        print(f"❌ Error analyzing profile {profile_id}: {e}")
        try:
            profile = db_session.query(UserStyleProfile).filter(
                UserStyleProfile.id == profile_id
            ).first()
            if profile:
                profile.status = "failed"
                profile.error_message = f"Erreur inattendue: {str(e)}"
                profile.last_analyzed_at = datetime.utcnow()
                db_session.commit()
        except:
            pass
    finally:
        db_session.close()
