from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from app.models import SubscriptionTier, Platform

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    plan: Optional[str] = "free"  # free, standard, premium, agency

class UserResponse(UserBase):
    id: int
    created_at: datetime
    subscription_tier: SubscriptionTier
    current_plan: str
    credits_remaining: int
    email_verified: int
    is_admin: int

    class Config:
        from_attributes = True

# Content Request Schemas
class ContentRequestBase(BaseModel):
    original_text: str
    platform: Optional[str] = "multi_format"  # Optionnel avec valeur par défaut
    tone: Optional[str] = "professional"
    language: Optional[str] = "fr"

class ContentRequestCreate(ContentRequestBase):
    use_pro_trial: Optional[bool] = False  # Utiliser le crédit d'essai Pro gratuit
    formats: Optional[List[str]] = None  # Liste des formats à générer (None = tous les formats)

class ContentRequestResponse(ContentRequestBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Generated Content Schemas
class GeneratedContentResponse(BaseModel):
    id: int
    request_id: int
    polished_text: str
    variant_number: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Usage Analytics Schemas
class UsageAnalyticsResponse(BaseModel):
    id: int
    user_id: int
    tokens_used: Optional[int]
    request_date: datetime
    platform: Optional[Platform]
    
    class Config:
        from_attributes = True