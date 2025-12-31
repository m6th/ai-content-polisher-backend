from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models
from app.database import get_db
from app.routers import auth
from datetime import datetime

router = APIRouter(prefix="/trial", tags=["trial"])


@router.post("/activate-pro-trial")
def activate_pro_trial(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activer l'essai Pro gratuit (1 crédit)

    - Disponible uniquement pour Free/Starter qui n'ont jamais utilisé l'essai
    - Marque l'utilisateur comme ayant utilisé son essai
    - N'ajoute PAS de crédit (le crédit sera géré côté frontend comme un mode spécial)
    """

    # Vérifier si l'utilisateur est Free ou Starter
    if current_user.current_plan not in ['free', 'starter']:
        raise HTTPException(
            status_code=403,
            detail="L'essai Pro est réservé aux utilisateurs Free et Starter"
        )

    # Vérifier si l'essai a déjà été utilisé
    if current_user.has_used_pro_trial:
        raise HTTPException(
            status_code=403,
            detail="Vous avez déjà utilisé votre essai Pro gratuit"
        )

    # Activer l'essai
    current_user.has_used_pro_trial = True
    current_user.pro_trial_activated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Essai Pro activé ! Vous pouvez maintenant générer 1 contenu avec les fonctionnalités Pro.",
        "trial_activated_at": current_user.pro_trial_activated_at.isoformat()
    }


@router.get("/status")
def get_trial_status(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupérer le statut de l'essai Pro de l'utilisateur
    """

    return {
        "can_use_trial": current_user.current_plan in ['free', 'starter'] and not current_user.has_used_pro_trial,
        "has_used_trial": current_user.has_used_pro_trial,
        "trial_activated_at": current_user.pro_trial_activated_at.isoformat() if current_user.pro_trial_activated_at else None,
        "current_plan": current_user.current_plan
    }
