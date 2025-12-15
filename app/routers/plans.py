from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models import User
from app.plan_config import get_plan_config, PLAN_CONFIG

router = APIRouter(prefix="/plans", tags=["plans"])

@router.get("/my-restrictions")
def get_my_plan_restrictions(current_user: User = Depends(get_current_user)):
    """Récupère les restrictions du plan de l'utilisateur actuel"""
    plan_config = get_plan_config(current_user.current_plan)

    return {
        "plan": current_user.current_plan,
        "platforms": plan_config['platforms'],
        "tones": plan_config['tones'],
        "languages": plan_config['languages'],
        "features": plan_config['features'],
        "credits": plan_config['credits']
    }

@router.get("/all")
def get_all_plans():
    """Récupère la configuration de tous les plans (pour affichage public)"""
    return PLAN_CONFIG
