from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class SubscriptionTier(str, enum.Enum):
    free = "free"
    basic = "basic"
    pro = "pro"
    enterprise = "enterprise"

class Platform(str, enum.Enum):
    linkedin = "linkedin"
    instagram = "instagram"
    tiktok = "tiktok"
    facebook = "facebook"
    twitter = "twitter"
    multi_format = "multi_format"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # Nullable pour Google OAuth
    google_id = Column(String, unique=True, nullable=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.free)
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

    # Pro trial tracking
    has_used_pro_trial = Column(Boolean, default=False, nullable=False)  # A-t-il utilisé son essai Pro gratuit
    pro_trial_activated_at = Column(DateTime, nullable=True)  # Quand l'essai a été activé

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

class ScheduledContent(Base):
    __tablename__ = "scheduled_contents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_request_id = Column(Integer, ForeignKey("content_requests.id"), nullable=True)
    generated_content_id = Column(Integer, ForeignKey("generated_contents.id"), nullable=True)
    scheduled_date = Column(DateTime, nullable=False)
    platform = Column(String, nullable=False)  # linkedin, instagram, etc.
    status = Column(String, default="scheduled")  # scheduled, published, cancelled
    title = Column(String, nullable=True)  # Optional title for the calendar entry
    notes = Column(Text, nullable=True)  # Optional notes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Reminder tracking
    reminder_24h_sent = Column(Boolean, default=False, nullable=False)
    reminder_1h_sent = Column(Boolean, default=False, nullable=False)
    reminder_24h_sent_at = Column(DateTime, nullable=True)
    reminder_1h_sent_at = Column(DateTime, nullable=True)

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan = Column(String, nullable=False)  # pro, business
    max_members = Column(Integer, default=2)  # 2 for Pro, 5 for Business
    team_credits = Column(Integer, default=0)  # Shared team credits pool
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="member")  # owner, admin, member
    status = Column(String, default="active")  # active, pending, removed
    joined_at = Column(DateTime, default=datetime.utcnow)

class TeamInvitation(Base):
    __tablename__ = "team_invitations"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    email = Column(String, nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    status = Column(String, default="pending")  # pending, accepted, expired
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # Nom donné par l'utilisateur (ex: "Production Server")
    key_prefix = Column(String(20), unique=True, nullable=False, index=True)  # ex: acp_live_abc123
    key_hash = Column(String(255), nullable=False)  # Hash SHA256 de la clé complète
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)  # Dernière utilisation de cette clé
    is_active = Column(Boolean, default=True, nullable=False)  # Clé active ou révoquée

    user = relationship("User")

class UserOnboarding(Base):
    __tablename__ = "user_onboarding"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    completed = Column(Boolean, default=False, nullable=False)
    discovery_source = Column(String, nullable=True)  # Comment ils nous ont trouvé
    preferred_networks = Column(Text, nullable=True)  # JSON array des réseaux préférés
    social_urls = Column(Text, nullable=True)  # JSON object avec les URLs des réseaux sociaux
    style_option = Column(String, nullable=True)  # 'personal', 'creator', 'predefined'
    creator_url = Column(String, nullable=True)  # URL du créateur à imiter
    preferred_style = Column(String, nullable=True)  # Style d'écriture préféré (pour predefined)
    fallback_style = Column(String, nullable=True)  # Style de secours (pour personal/creator)
    consent_data_storage = Column(Boolean, default=False, nullable=False)  # Consentement RGPD
    completed_at = Column(DateTime, nullable=True)  # Quand l'onboarding a été complété
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")

class UserStyleProfile(Base):
    __tablename__ = "user_style_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    style_name = Column(String, nullable=False)  # "Mon style LinkedIn", "Style de [Creator]", etc.
    style_type = Column(String, nullable=False)  # 'personal' or 'creator'
    platform = Column(String, nullable=True)  # 'linkedin', 'instagram', 'facebook' (pour personal)
    source_url = Column(String, nullable=False)  # URL du compte analysé
    style_analysis = Column(Text, nullable=True)  # Analyse détaillée du style par l'IA
    sample_posts = Column(Text, nullable=True)  # JSON array des posts d'exemple
    status = Column(String, default="pending", nullable=False)  # 'pending', 'analyzing', 'ready', 'failed'
    error_message = Column(Text, nullable=True)  # Message d'erreur si l'analyse a échoué
    last_analyzed_at = Column(DateTime, nullable=True)  # Dernière analyse
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")