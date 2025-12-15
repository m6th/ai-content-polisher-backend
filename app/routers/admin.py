from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from app.database import get_db
from app.models import User, ContentRequest, UsageAnalytics, GeneratedContent
from app.auth import get_current_user
from app.plan_config import get_plan_credits, PLAN_CONFIG
from datetime import datetime, timedelta
from typing import List, Dict

router = APIRouter(prefix="/admin", tags=["admin"])

def verify_admin(current_user: User = Depends(get_current_user)):
    """Vérifie que l'utilisateur actuel est un admin"""
    if current_user.is_admin != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs"
        )
    return current_user

@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Statistiques globales de la plateforme"""

    # Nombre total d'utilisateurs
    total_users = db.query(func.count(User.id)).scalar()

    # Utilisateurs par plan
    users_by_plan = db.query(
        User.current_plan,
        func.count(User.id).label('count')
    ).group_by(User.current_plan).all()

    # Total de requêtes
    total_requests = db.query(func.count(ContentRequest.id)).scalar()

    # Requêtes ce mois
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    requests_this_month = db.query(func.count(ContentRequest.id)).filter(
        extract('month', ContentRequest.created_at) == current_month,
        extract('year', ContentRequest.created_at) == current_year
    ).scalar()

    # Utilisateurs actifs (au moins une requête dans les 30 derniers jours)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(func.count(func.distinct(ContentRequest.user_id))).filter(
        ContentRequest.created_at >= thirty_days_ago
    ).scalar()

    # Revenus potentiels (basé sur les plans)
    plan_prices = {plan: config['price'] for plan, config in PLAN_CONFIG.items()}
    monthly_revenue = sum(
        plan_prices.get(plan, 0) * count
        for plan, count in users_by_plan
    )

    return {
        "total_users": total_users,
        "total_requests": total_requests,
        "requests_this_month": requests_this_month,
        "active_users": active_users,
        "monthly_revenue": monthly_revenue,
        "users_by_plan": [{"plan": plan, "count": count} for plan, count in users_by_plan]
    }

@router.get("/users")
def get_all_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Liste de tous les utilisateurs avec pagination"""

    users = db.query(User).order_by(desc(User.created_at)).offset(skip).limit(limit).all()

    # Ajouter le nombre de requêtes pour chaque utilisateur
    users_data = []
    for user in users:
        request_count = db.query(func.count(ContentRequest.id)).filter(
            ContentRequest.user_id == user.id
        ).scalar()

        users_data.append({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "current_plan": user.current_plan,
            "credits_remaining": user.credits_remaining,
            "email_verified": user.email_verified,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "total_requests": request_count
        })

    return users_data

@router.get("/users/{user_id}")
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Détails complets d'un utilisateur spécifique"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Statistiques de l'utilisateur
    total_requests = db.query(func.count(ContentRequest.id)).filter(
        ContentRequest.user_id == user_id
    ).scalar()

    # Dernières requêtes
    recent_requests = db.query(ContentRequest).filter(
        ContentRequest.user_id == user_id
    ).order_by(desc(ContentRequest.created_at)).limit(10).all()

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "current_plan": user.current_plan,
            "credits_remaining": user.credits_remaining,
            "email_verified": user.email_verified,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "plan_started_at": user.plan_started_at
        },
        "stats": {
            "total_requests": total_requests
        },
        "recent_requests": [
            {
                "id": req.id,
                "platform": req.platform,
                "tone": req.tone,
                "created_at": req.created_at,
                "original_text": req.original_text[:100] + "..." if len(req.original_text) > 100 else req.original_text
            }
            for req in recent_requests
        ]
    }

@router.put("/users/{user_id}/credits")
def update_user_credits(
    user_id: int,
    credits: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Modifier les crédits d'un utilisateur"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    user.credits_remaining = credits
    db.commit()

    return {"message": "Crédits mis à jour", "new_credits": credits}

@router.put("/users/{user_id}/plan")
def update_user_plan(
    user_id: int,
    plan: str,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Modifier le plan d'un utilisateur"""

    valid_plans = list(PLAN_CONFIG.keys())
    if plan not in valid_plans:
        raise HTTPException(status_code=400, detail="Plan invalide")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    user.current_plan = plan
    user.plan_started_at = datetime.utcnow()

    # Mettre à jour les crédits selon le plan
    user.credits_remaining = get_plan_credits(plan)

    db.commit()

    return {"message": "Plan mis à jour", "new_plan": plan, "new_credits": user.credits_remaining}

@router.put("/users/{user_id}/admin")
def toggle_admin_status(
    user_id: int,
    is_admin: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Modifier le statut admin d'un utilisateur"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    user.is_admin = 1 if is_admin else 0
    db.commit()

    return {"message": "Statut admin mis à jour", "is_admin": user.is_admin}

@router.get("/requests/recent")
def get_recent_requests(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Liste des requêtes récentes de tous les utilisateurs"""

    requests = db.query(
        ContentRequest,
        User.email,
        User.name,
        User.current_plan
    ).join(User).order_by(desc(ContentRequest.created_at)).limit(limit).all()

    return [
        {
            "id": req.id,
            "user_email": email,
            "user_name": name,
            "user_plan": plan,
            "platform": req.platform,
            "tone": req.tone,
            "language": req.language,
            "created_at": req.created_at,
            "original_text": req.original_text[:100] + "..." if len(req.original_text) > 100 else req.original_text
        }
        for req, email, name, plan in requests
    ]

@router.get("/analytics/usage-trends")
def get_usage_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Tendances d'utilisation sur les derniers jours"""

    start_date = datetime.utcnow() - timedelta(days=days)

    # Requêtes par jour
    daily_requests = db.query(
        func.date(ContentRequest.created_at).label('date'),
        func.count(ContentRequest.id).label('count')
    ).filter(
        ContentRequest.created_at >= start_date
    ).group_by(func.date(ContentRequest.created_at)).order_by('date').all()

    return [
        {
            "date": date.strftime('%Y-%m-%d'),
            "requests": count
        }
        for date, count in daily_requests
    ]

@router.get("/analytics/platform-distribution")
def get_platform_distribution(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Distribution des requêtes par plateforme"""

    platforms = db.query(
        ContentRequest.platform,
        func.count(ContentRequest.id).label('count')
    ).group_by(ContentRequest.platform).all()

    return [
        {"platform": platform, "count": count}
        for platform, count in platforms
    ]

@router.post("/users/{user_id}/renew-credits")
def force_renew_credits(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Force le renouvellement des crédits pour un utilisateur"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Récupérer le nombre de crédits pour le plan de l'utilisateur
    plan_credits = get_plan_credits(user.current_plan)

    # Renouveler les crédits
    user.credits_remaining = plan_credits
    user.last_credit_renewal = datetime.utcnow()

    db.commit()

    return {
        "message": "Crédits renouvelés avec succès",
        "user_email": user.email,
        "plan": user.current_plan,
        "new_credits": plan_credits,
        "last_renewal": user.last_credit_renewal
    }

@router.post("/renew-all-credits")
def renew_all_credits(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Renouvelle les crédits pour tous les utilisateurs dont le renouvellement est dû (>30 jours)"""

    # Date limite : il y a 30 jours
    renewal_cutoff = datetime.utcnow() - timedelta(days=30)

    # Récupérer tous les utilisateurs dont le dernier renouvellement est ancien
    users_to_renew = db.query(User).filter(
        User.last_credit_renewal <= renewal_cutoff
    ).all()

    renewed_users = []
    for user in users_to_renew:
        # Récupérer le nombre de crédits pour le plan de l'utilisateur
        plan_credits = get_plan_credits(user.current_plan)

        # Renouveler les crédits
        user.credits_remaining = plan_credits
        user.last_credit_renewal = datetime.utcnow()

        renewed_users.append({
            "email": user.email,
            "plan": user.current_plan,
            "credits": plan_credits
        })

    db.commit()

    return {
        "message": f"{len(renewed_users)} utilisateur(s) renouvelé(s)",
        "renewed_users": renewed_users
    }

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    """Supprimer un utilisateur (avec toutes ses données)"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Ne pas permettre de supprimer un autre admin
    if user.is_admin == 1 and user.id != admin.id:
        raise HTTPException(status_code=403, detail="Impossible de supprimer un autre administrateur")

    # Supprimer toutes les données associées
    db.query(UsageAnalytics).filter(UsageAnalytics.user_id == user_id).delete()

    # Supprimer les contenus générés via les requêtes
    request_ids = [req.id for req in db.query(ContentRequest.id).filter(ContentRequest.user_id == user_id).all()]
    if request_ids:
        db.query(GeneratedContent).filter(GeneratedContent.request_id.in_(request_ids)).delete(synchronize_session=False)

    db.query(ContentRequest).filter(ContentRequest.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    return {"message": "Utilisateur supprimé avec succès"}
