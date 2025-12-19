from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from app.database import get_db
from app.auth import get_current_user
from app.models import User, UsageAnalytics, ContentRequest, GeneratedContent
from app.plan_config import get_plan_config, get_plan_credits
from typing import Dict, List

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/stats")
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Récupère les statistiques globales de l'utilisateur (Pro/Business: statistiques détaillées)"""

    # Check if user has advanced analytics
    plan_config = get_plan_config(current_user.current_plan)
    analytics_enabled = plan_config.get('features', {}).get('analytics', False)

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

    # Récupère les crédits max depuis la configuration
    max_credits = get_plan_credits(current_user.current_plan)
    usage_rate = (credits_used_this_month / max_credits * 100) if max_credits > 0 else 0

    base_stats = {
        "total_requests": total_requests,
        "credits_used_this_month": credits_used_this_month,
        "credits_remaining": current_user.credits_remaining,
        "usage_rate": round(usage_rate, 1),
        "current_plan": current_user.current_plan,
        "max_credits_per_month": max_credits,
        "analytics_enabled": analytics_enabled
    }

    # Pro/Business get additional detailed stats
    if analytics_enabled:
        # Total generated contents
        total_generated = db.query(func.count(GeneratedContent.id)).join(
            ContentRequest
        ).filter(
            ContentRequest.user_id == current_user.id
        ).scalar() or 0

        # Total tokens used
        total_tokens = db.query(func.sum(UsageAnalytics.tokens_used)).filter(
            UsageAnalytics.user_id == current_user.id
        ).scalar() or 0

        # Average variants per request
        avg_variants = total_generated / total_requests if total_requests > 0 else 0

        # Most used tone
        most_used_tone = db.query(
            ContentRequest.tone,
            func.count(ContentRequest.id).label('count')
        ).filter(
            ContentRequest.user_id == current_user.id
        ).group_by(
            ContentRequest.tone
        ).order_by(func.count(ContentRequest.id).desc()).first()

        base_stats.update({
            "total_generated_contents": total_generated,
            "total_tokens_used": int(total_tokens) if total_tokens else 0,
            "avg_variants_per_request": round(avg_variants, 1),
            "most_used_tone": most_used_tone.tone if most_used_tone else None
        })

    return base_stats

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

@router.get("/format-analytics")
def get_format_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Analyse détaillée par format (Pro/Business uniquement)"""

    # Check if user has analytics feature
    plan_config = get_plan_config(current_user.current_plan)
    analytics_enabled = plan_config.get('features', {}).get('analytics', False)

    if not analytics_enabled:
        raise HTTPException(
            status_code=403,
            detail="Les analytics détaillés sont réservés aux plans Pro et Business"
        )

    # Get format distribution with detailed stats
    format_stats = db.query(
        GeneratedContent.format_name,
        func.count(GeneratedContent.id).label('total_generated'),
        func.avg(func.length(GeneratedContent.polished_text)).label('avg_length'),
        func.min(GeneratedContent.created_at).label('first_used'),
        func.max(GeneratedContent.created_at).label('last_used')
    ).join(
        ContentRequest
    ).filter(
        ContentRequest.user_id == current_user.id,
        GeneratedContent.format_name.isnot(None)
    ).group_by(
        GeneratedContent.format_name
    ).all()

    # Format names mapping
    format_labels = {
        'linkedin': 'LinkedIn',
        'instagram': 'Instagram',
        'tiktok': 'TikTok',
        'twitter': 'Twitter',
        'email': 'Email',
        'persuasive': 'Persuasif'
    }

    formats_data = []
    for fmt in format_stats:
        formats_data.append({
            "format": format_labels.get(fmt.format_name, fmt.format_name),
            "format_key": fmt.format_name,
            "total_generated": fmt.total_generated,
            "avg_length": round(fmt.avg_length) if fmt.avg_length else 0,
            "first_used": fmt.first_used.isoformat() if fmt.first_used else None,
            "last_used": fmt.last_used.isoformat() if fmt.last_used else None
        })

    # Sort by most used
    formats_data.sort(key=lambda x: x['total_generated'], reverse=True)

    # Get tone performance by format
    tone_format_stats = db.query(
        ContentRequest.tone,
        GeneratedContent.format_name,
        func.count(GeneratedContent.id).label('count')
    ).join(
        GeneratedContent
    ).filter(
        ContentRequest.user_id == current_user.id,
        GeneratedContent.format_name.isnot(None)
    ).group_by(
        ContentRequest.tone,
        GeneratedContent.format_name
    ).all()

    tone_distribution = {}
    for stat in tone_format_stats:
        tone = stat.tone or 'N/A'
        if tone not in tone_distribution:
            tone_distribution[tone] = {}
        tone_distribution[tone][stat.format_name] = stat.count

    return {
        "formats": formats_data,
        "tone_by_format": tone_distribution,
        "total_formats_used": len(formats_data)
    }

@router.get("/performance-summary")
def get_performance_summary(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Résumé des performances (Pro/Business uniquement)"""

    # Check if user has analytics feature
    plan_config = get_plan_config(current_user.current_plan)
    analytics_enabled = plan_config.get('features', {}).get('analytics', False)

    if not analytics_enabled:
        raise HTTPException(
            status_code=403,
            detail="Les analytics de performance sont réservés aux plans Pro et Business"
        )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get activity by day of week
    day_of_week_stats = db.query(
        extract('dow', ContentRequest.created_at).label('day_of_week'),
        func.count(ContentRequest.id).label('count')
    ).filter(
        ContentRequest.user_id == current_user.id,
        ContentRequest.created_at >= start_date
    ).group_by(
        extract('dow', ContentRequest.created_at)
    ).all()

    # Map day numbers to names
    day_names = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
    activity_by_day = {day_names[int(stat.day_of_week)]: stat.count for stat in day_of_week_stats}

    # Get activity by hour of day
    hour_stats = db.query(
        extract('hour', ContentRequest.created_at).label('hour'),
        func.count(ContentRequest.id).label('count')
    ).filter(
        ContentRequest.user_id == current_user.id,
        ContentRequest.created_at >= start_date
    ).group_by(
        extract('hour', ContentRequest.created_at)
    ).all()

    activity_by_hour = {int(stat.hour): stat.count for stat in hour_stats}

    # Get content efficiency (avg chars per content)
    avg_content_length = db.query(
        func.avg(func.length(GeneratedContent.polished_text))
    ).join(
        ContentRequest
    ).filter(
        ContentRequest.user_id == current_user.id,
        ContentRequest.created_at >= start_date
    ).scalar() or 0

    return {
        "period_days": days,
        "activity_by_day_of_week": activity_by_day,
        "activity_by_hour": activity_by_hour,
        "avg_content_length": round(avg_content_length),
        "summary": {
            "most_active_day": max(activity_by_day.items(), key=lambda x: x[1])[0] if activity_by_day else None,
            "most_active_hour": max(activity_by_hour.items(), key=lambda x: x[1])[0] if activity_by_hour else None
        }
    }
