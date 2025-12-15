from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.database import get_db
from app.auth import get_current_user
from app.models import User, UsageAnalytics, ContentRequest
from typing import Dict, List

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/stats")
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Récupère les statistiques globales de l'utilisateur"""
    
    # Total de requêtes
    total_requests = db.query(func.count(ContentRequest.id)).filter(
        ContentRequest.user_id == current_user.id
    ).scalar() or 0
    
    # Crédits utilisés ce mois
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    credits_used_this_month = db.query(func.count(ContentRequest.id)).filter(
        ContentRequest.user_id == current_user.id,
        ContentRequest.created_at >= first_day_of_month
    ).scalar() or 0
    
    # Calcul du taux d'utilisation
    plan_credits = {
        'free': 10,
        'standard': 100,
        'premium': 300,
        'agency': 1000
    }
    max_credits = plan_credits.get(current_user.current_plan, 10)
    usage_rate = (credits_used_this_month / max_credits * 100) if max_credits > 0 else 0
    
    return {
        "total_requests": total_requests,
        "credits_used_this_month": credits_used_this_month,
        "credits_remaining": current_user.credits_remaining,
        "usage_rate": round(usage_rate, 1),
        "current_plan": current_user.current_plan,
        "max_credits_per_month": max_credits
    }

@router.get("/daily-usage")
def get_daily_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Récupère l'utilisation quotidienne des 7 derniers jours"""
    
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Requêtes par jour
    daily_data = db.query(
        func.date(ContentRequest.created_at).label('date'),
        func.count(ContentRequest.id).label('count')
    ).filter(
        ContentRequest.user_id == current_user.id,
        ContentRequest.created_at >= seven_days_ago
    ).group_by(
        func.date(ContentRequest.created_at)
    ).all()
    
    # Créer un dictionnaire pour tous les 7 derniers jours
    result = []
    for i in range(7):
        date = (datetime.utcnow() - timedelta(days=6-i)).date()
        count = 0
        
        for data in daily_data:
            if data.date == date:
                count = data.count
                break
        
        result.append({
            "date": date.strftime("%d/%m"),
            "count": count
        })
    
    return result

@router.get("/platform-usage")
def get_platform_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict]:
    """Récupère la répartition par plateforme"""
    
    platform_data = db.query(
        ContentRequest.platform,
        func.count(ContentRequest.id).label('count')
    ).filter(
        ContentRequest.user_id == current_user.id
    ).group_by(
        ContentRequest.platform
    ).all()
    
    # Noms conviviaux pour les plateformes
    platform_names = {
        'linkedin': 'LinkedIn',
        'instagram': 'Instagram',
        'tiktok': 'TikTok',
        'facebook': 'Facebook',
        'twitter': 'Twitter',
        'multi_format': 'Multi-format'
    }
    
    result = []
    for platform, count in platform_data:
        result.append({
            "name": platform_names.get(platform, platform),
            "value": count
        })
    
    return result

@router.get("/recent-activity")
def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 10
) -> List[Dict]:
    """Récupère les activités récentes de l'utilisateur"""
    
    recent_requests = db.query(ContentRequest).filter(
        ContentRequest.user_id == current_user.id
    ).order_by(
        ContentRequest.created_at.desc()
    ).limit(limit).all()
    
    result = []
    for request in recent_requests:
        result.append({
            "id": request.id,
            "platform": request.platform,
            "tone": request.tone,
            "preview": request.original_text[:100] + "..." if len(request.original_text) > 100 else request.original_text,
            "created_at": request.created_at.isoformat()
        })
    
    return result
