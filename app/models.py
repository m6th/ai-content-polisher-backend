from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class Platform(str, enum.Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    MULTI_FORMAT = "multi_format"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # Nullable pour Google OAuth
    google_id = Column(String, unique=True, nullable=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    current_plan = Column(String, default="free")  # free, standard, premium, agency
    plan_started_at = Column(DateTime, default=datetime.utcnow)
    credits_remaining = Column(Integer, default=10)
    last_credit_renewal = Column(DateTime, default=datetime.utcnow)  # Dernière date de renouvellement des crédits
    email_verified = Column(Integer, default=0)  # 0 = non vérifié, 1 = vérifié
    verification_code = Column(String, nullable=True)  # Code à 6 chiffres
    verification_code_expires = Column(DateTime, nullable=True)  # Expiration du code
    is_admin = Column(Integer, default=0)  # 0 = utilisateur normal, 1 = admin

    # Stripe fields
    stripe_customer_id = Column(String, nullable=True, unique=True)  # ID client Stripe
    stripe_subscription_id = Column(String, nullable=True)  # ID abonnement Stripe
    subscription_status = Column(String, default="inactive")  # active, canceled, past_due, etc.
    subscription_end_date = Column(DateTime, nullable=True)  # Date de fin d'abonnement

    content_requests = relationship("ContentRequest", back_populates="user")
    usage_analytics = relationship("UsageAnalytics", back_populates="user")

class ContentRequest(Base):
    __tablename__ = "content_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    platform = Column(String, nullable=False)
    tone = Column(String)  # casual, professional, engaging, etc.
    language = Column(String, default="fr")  # fr, en, es
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="content_requests")
    generated_contents = relationship("GeneratedContent", back_populates="request")

class GeneratedContent(Base):
    __tablename__ = "generated_contents"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("content_requests.id"), nullable=False)
    polished_text = Column(Text, nullable=False)
    format_name = Column(String, nullable=True)  # linkedin, instagram, tiktok, etc.
    variant_number = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    request = relationship("ContentRequest", back_populates="generated_contents")

class UsageAnalytics(Base):
    __tablename__ = "usage_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tokens_used = Column(Integer)
    request_date = Column(DateTime, default=datetime.utcnow)
    platform = Column(Enum(Platform))
    
    user = relationship("User", back_populates="usage_analytics")