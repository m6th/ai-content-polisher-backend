from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from app import crud, schemas, auth
from app.database import get_db
from app.auth_google import verify_google_token
from app.email_service import send_verification_email
from app.plan_config import get_plan_credits, PLAN_MAPPING
from pydantic import BaseModel
from app import models

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email déjà enregistré")

    # Valider la force du mot de passe
    is_valid, error_message = crud.validate_password_strength(user.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # Créer l'utilisateur avec le code de vérification
    new_user = crud.create_user(db=db, user=user)

    # Envoyer l'email de vérification
    send_verification_email(new_user.email, new_user.verification_code, new_user.name)

    return new_user

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user = Depends(auth.get_current_user)):
    return current_user

class GoogleAuthRequest(BaseModel):
    token: str
    plan: str = "free"  # free, starter, pro, business

@router.post("/auth/google")
async def google_auth(auth_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authentification via Google OAuth"""
    try:
        print(f"Token reçu: {auth_data.token[:50]}...")

        google_user = await verify_google_token(auth_data.token)

        # Cherche l'utilisateur par google_id ou email
        user = db.query(models.User).filter(
            (models.User.google_id == google_user["google_id"]) |
            (models.User.email == google_user["email"])
        ).first()

        if not user:
            # IMPORTANT: Toujours créer avec le plan "free" lors de l'inscription
            # Les plans payants seront activés uniquement après paiement via Stripe
            plan = 'free'
            credits = get_plan_credits(plan)

            # Crée un nouveau compte
            user = models.User(
                email=google_user["email"],
                name=google_user["name"],
                google_id=google_user["google_id"],
                password_hash=None,
                current_plan=plan,
                credits_remaining=credits,
                email_verified=1  # Google OAuth = email déjà vérifié
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif not user.google_id:
            # Lie le compte existant à Google
            user.google_id = google_user["google_id"]
            db.commit()
        
        # Génère un token JWT
        access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class VerifyEmailRequest(BaseModel):
    email: str
    code: str

@router.post("/verify-email")
def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Vérifie le code de vérification email"""
    user = crud.get_user_by_email(db, email=request.email)

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    if user.email_verified == 1:
        return {"message": "Email déjà vérifié", "verified": True}

    if not user.verification_code or not user.verification_code_expires:
        raise HTTPException(status_code=400, detail="Aucun code de vérification actif")

    # Vérifier si le code a expiré
    if datetime.utcnow() > user.verification_code_expires:
        raise HTTPException(status_code=400, detail="Code expiré. Demandez un nouveau code.")

    # Vérifier le code
    if user.verification_code != request.code:
        raise HTTPException(status_code=400, detail="Code invalide")

    # Marquer l'email comme vérifié
    user.email_verified = 1
    user.verification_code = None
    user.verification_code_expires = None
    db.commit()

    return {"message": "Email vérifié avec succès !", "verified": True}

@router.post("/resend-verification")
def resend_verification(email: str, db: Session = Depends(get_db)):
    """Renvoie un code de vérification"""
    user = crud.get_user_by_email(db, email=email)

    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    if user.email_verified == 1:
        return {"message": "Email déjà vérifié"}

    # Générer un nouveau code
    verification_code = crud.generate_verification_code()
    verification_expires = datetime.utcnow() + timedelta(minutes=15)

    user.verification_code = verification_code
    user.verification_code_expires = verification_expires
    db.commit()

    # Envoyer l'email
    send_verification_email(user.email, verification_code, user.name)

    return {"message": "Code renvoyé avec succès"}

class ChangePlanRequest(BaseModel):
    plan: str  # free, standard, premium, agency

@router.post("/change-plan")
def change_plan(
    plan_request: ChangePlanRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Change le plan de l'utilisateur et met à jour ses crédits"""

    # Configuration des crédits par plan
    plan_credits = {
        'free': 10,
        'standard': 100,
        'premium': 300,
        'agency': 1000
    }

    plan_name = plan_request.plan.lower()

    if plan_name not in plan_credits:
        raise HTTPException(status_code=400, detail="Plan invalide")

    # Met à jour le plan et les crédits
    current_user.current_plan = plan_name
    current_user.credits_remaining = plan_credits[plan_name]
    current_user.plan_started_at = datetime.utcnow()

    db.commit()
    db.refresh(current_user)

    return {
        "message": f"Plan changé avec succès vers {plan_name}",
        "plan": plan_name,
        "credits": current_user.credits_remaining
    }

class UpdateProfileRequest(BaseModel):
    name: str

@router.put("/profile")
def update_profile(
    profile_request: UpdateProfileRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    if not profile_request.name or len(profile_request.name.strip()) == 0:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    current_user.name = profile_request.name.strip()
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated successfully",
        "name": current_user.name
    }

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.put("/change-password")
def change_password(
    password_request: ChangePasswordRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    # Verify current password
    if not current_user.password_hash:
        raise HTTPException(status_code=400, detail="Cannot change password for Google OAuth accounts")

    if not auth.verify_password(password_request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Validate new password
    if len(password_request.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    # Update password
    current_user.password_hash = auth.get_password_hash(password_request.new_password)
    db.commit()

    return {"message": "Password changed successfully"}

class ChangeEmailRequest(BaseModel):
    new_email: str
    password: str

@router.put("/change-email")
def change_email(
    email_request: ChangeEmailRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Change user email"""
    # Verify password
    if not current_user.password_hash:
        raise HTTPException(status_code=400, detail="Cannot change email for Google OAuth accounts")

    if not auth.verify_password(email_request.password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    # Check if email is already used
    existing_user = crud.get_user_by_email(db, email=email_request.new_email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Update email and reset verification
    current_user.email = email_request.new_email
    current_user.email_verified = 0

    # Generate verification code
    verification_code = crud.generate_verification_code()
    verification_expires = datetime.utcnow() + timedelta(minutes=15)
    current_user.verification_code = verification_code
    current_user.verification_code_expires = verification_expires

    db.commit()

    # Send verification email
    send_verification_email(current_user.email, verification_code, current_user.name)

    return {
        "message": "Email changed successfully. Please verify your new email.",
        "email": current_user.email
    }