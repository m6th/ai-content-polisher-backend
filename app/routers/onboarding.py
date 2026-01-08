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
class OnboardingData(BaseModel):
    discovery_source: str
    preferred_networks: List[str]
    preferred_style: str
    consent_data_storage: bool

class OnboardingStatus(BaseModel):
    completed: bool
    discovery_source: Optional[str] = None
    preferred_networks: Optional[List[str]] = None
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

    # Convert preferred_networks list to JSON string
    networks_json = json.dumps(data.preferred_networks)

    if onboarding:
        # Update existing onboarding
        onboarding.discovery_source = data.discovery_source
        onboarding.preferred_networks = networks_json
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

    # Parse preferred_networks JSON
    networks = json.loads(onboarding.preferred_networks) if onboarding.preferred_networks else []

    return OnboardingStatus(
        completed=onboarding.completed,
        discovery_source=onboarding.discovery_source,
        preferred_networks=networks,
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
