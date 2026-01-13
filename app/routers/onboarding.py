from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserOnboarding
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

# Schemas
class SocialUrls(BaseModel):
    linkedin: Optional[str] = ''
    twitter: Optional[str] = ''
    instagram: Optional[str] = ''
    facebook: Optional[str] = ''
    tiktok: Optional[str] = ''
    youtube: Optional[str] = ''

class OnboardingData(BaseModel):
    discovery_source: str
    preferred_networks: List[str]
    social_urls: Optional[SocialUrls] = None
    style_option: Optional[str] = None  # 'personal', 'creator', 'predefined'
    creator_url: Optional[str] = None
    preferred_style: Optional[str] = None  # For predefined style
    fallback_style: Optional[str] = None  # Fallback for personal/creator
    consent_data_storage: bool

class OnboardingStatus(BaseModel):
    completed: bool
    discovery_source: Optional[str] = None
    preferred_networks: Optional[List[str]] = None
    social_urls: Optional[dict] = None
    style_option: Optional[str] = None
    creator_url: Optional[str] = None
    preferred_style: Optional[str] = None
    fallback_style: Optional[str] = None
    completed_at: Optional[datetime] = None

@router.post("/complete")
def complete_onboarding(
    data: OnboardingData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complete onboarding process and save user preferences
    """
    # Check if onboarding already exists
    onboarding = db.query(UserOnboarding).filter(
        UserOnboarding.user_id == current_user.id
    ).first()

    # Convert lists and dicts to JSON strings
    networks_json = json.dumps(data.preferred_networks)
    social_urls_json = json.dumps(data.social_urls.dict()) if data.social_urls else None

    if onboarding:
        # Update existing onboarding
        onboarding.discovery_source = data.discovery_source
        onboarding.preferred_networks = networks_json
        if social_urls_json and hasattr(onboarding, 'social_urls'):
            onboarding.social_urls = social_urls_json
        if hasattr(onboarding, 'style_option'):
            onboarding.style_option = data.style_option
        if hasattr(onboarding, 'creator_url'):
            onboarding.creator_url = data.creator_url
        onboarding.preferred_style = data.preferred_style
        if hasattr(onboarding, 'fallback_style'):
            onboarding.fallback_style = data.fallback_style
        onboarding.consent_data_storage = data.consent_data_storage
        onboarding.completed = True
        onboarding.completed_at = datetime.utcnow()
        onboarding.updated_at = datetime.utcnow()
    else:
        # Create new onboarding record
        onboarding = UserOnboarding(
            user_id=current_user.id,
            discovery_source=data.discovery_source,
            preferred_networks=networks_json,
            social_urls=social_urls_json,
            style_option=data.style_option,
            creator_url=data.creator_url,
            preferred_style=data.preferred_style,
            fallback_style=data.fallback_style,
            consent_data_storage=data.consent_data_storage,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.add(onboarding)

    try:
        db.commit()
        db.refresh(onboarding)

        # Si l'utilisateur a choisi "personal style", créer automatiquement les profils de style
        if hasattr(onboarding, 'style_option') and onboarding.style_option == 'personal':
            try:
                from app.routers.onboarding_analyzer import create_styles_from_onboarding
                create_styles_from_onboarding(current_user.id, db)
            except Exception as e:
                # Ne pas faire échouer l'onboarding si l'analyse échoue
                print(f"Warning: Could not create style profiles: {e}")

        return {
            "message": "Onboarding completed successfully",
            "completed": True
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving onboarding data: {str(e)}"
        )

@router.get("/status", response_model=OnboardingStatus)
def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user's onboarding status
    """
    onboarding = db.query(UserOnboarding).filter(
        UserOnboarding.user_id == current_user.id
    ).first()

    if not onboarding:
        return OnboardingStatus(
            completed=False,
            discovery_source=None,
            preferred_networks=None,
            social_urls=None,
            style_option=None,
            creator_url=None,
            preferred_style=None,
            fallback_style=None,
            completed_at=None
        )

    # Parse JSON fields
    networks = json.loads(onboarding.preferred_networks) if onboarding.preferred_networks else []
    social_urls = json.loads(onboarding.social_urls) if onboarding.social_urls else {}

    return OnboardingStatus(
        completed=onboarding.completed,
        discovery_source=onboarding.discovery_source,
        preferred_networks=networks,
        social_urls=social_urls,
        style_option=getattr(onboarding, 'style_option', None),
        creator_url=getattr(onboarding, 'creator_url', None),
        preferred_style=onboarding.preferred_style,
        fallback_style=getattr(onboarding, 'fallback_style', None),
        completed_at=onboarding.completed_at
    )

@router.post("/reset")
def reset_onboarding(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset onboarding status (allows user to redo onboarding)
    """
    onboarding = db.query(UserOnboarding).filter(
        UserOnboarding.user_id == current_user.id
    ).first()

    if onboarding:
        onboarding.completed = False
        onboarding.completed_at = None
        onboarding.updated_at = datetime.utcnow()
        db.commit()

    return {
        "message": "Onboarding reset successfully",
        "completed": False
    }
