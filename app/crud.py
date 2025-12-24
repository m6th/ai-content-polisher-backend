from sqlalchemy.orm import Session
from app import models, schemas
from app.plan_config import get_plan_credits, PLAN_MAPPING
from passlib.context import CryptContext
import random
import re
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_verification_code() -> str:
    """Génère un code de vérification à 6 chiffres"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valide la force du mot de passe - Minimum requis: MOYEN
    Retourne (is_valid, error_message)

    Critères minimum (MOYEN):
    - Au moins 8 caractères
    - Au moins 1 lettre minuscule
    - Au moins 1 chiffre
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"

    has_lowercase = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'[0-9]', password))

    if not has_lowercase:
        return False, "Le mot de passe doit contenir au moins une lettre minuscule"

    if not has_digit:
        return False, "Le mot de passe doit contenir au moins 1 chiffre"

    return True, ""

# User CRUD
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Encode le mot de passe en UTF-8 et tronque à 72 bytes
    password_bytes = user.password.encode('utf-8')[:72]
    hashed_password = pwd_context.hash(password_bytes.decode('utf-8'))

    # IMPORTANT: Toujours créer avec le plan "free" lors de l'inscription
    # Les plans payants seront activés uniquement après paiement via Stripe
    plan = 'free'
    credits = get_plan_credits(plan)

    # Générer le code de vérification
    verification_code = generate_verification_code()
    verification_expires = datetime.utcnow() + timedelta(minutes=15)

    db_user = models.User(
        email=user.email,
        name=user.name,
        password_hash=hashed_password,
        current_plan=plan,
        credits_remaining=credits,
        email_verified=0,
        verification_code=verification_code,
        verification_code_expires=verification_expires
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# Content Request CRUD
def create_content_request(db: Session, request: schemas.ContentRequestCreate, user_id: int):
    db_request = models.ContentRequest(
        user_id=user_id,
        original_text=request.original_text,
        platform=request.platform,
        tone=request.tone
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def create_generated_content(db: Session, request_id: int, polished_text: str, variant_number: int = 1, format_name: str = None):
    db_content = models.GeneratedContent(
        request_id=request_id,
        polished_text=polished_text,
        format_name=format_name,
        variant_number=variant_number
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content

def get_user_requests(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return db.query(models.ContentRequest).filter(
        models.ContentRequest.user_id == user_id
    ).offset(skip).limit(limit).all()

def create_usage_analytics(db: Session, user_id: int, tokens_used: int, platform: str):
    db_analytics = models.UsageAnalytics(
        user_id=user_id,
        tokens_used=tokens_used,
        platform=platform
    )
    db.add(db_analytics)
    db.commit()
    db.refresh(db_analytics)
    return db_analytics

def decrease_user_credits(db: Session, user_id: int, amount: int = 1):
    user = get_user(db, user_id)
    if user and user.credits_remaining >= amount:
        user.credits_remaining -= amount
        db.commit()
        db.refresh(user)
        return True
    return False