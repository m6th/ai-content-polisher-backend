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
    preferred_style: str
    consent_data_storage: bool

class OnboardingStatus(BaseModel):
    completed: bool
    discovery_source: Optional[str] = None
    preferred_networks: Optional[List[str]] = None
    social_urls: Optional[dict] = None
    preferred_style: Optional[str] = None
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
        onboarding.preferred_style = data.preferred_style
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
            preferred_style=data.preferred_style,
            consent_data_storage=data.consent_data_storage,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.add(onboarding)

    try:
        db.commit()
        db.refresh(onboarding)
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
            preferred_style=None,
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
        preferred_style=onboarding.preferred_style,
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
