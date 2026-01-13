"""
Service pour analyser automatiquement les styles depuis l'onboarding
"""
from sqlalchemy.orm import Session
from app.models import UserOnboarding, UserStyleProfile, User
from app.routers.style_profiles import detect_platform_from_url, analyze_style_profile
import json


def create_styles_from_onboarding(user_id: int, db: Session):
    """
    Crée automatiquement des profils de style basés sur les données d'onboarding.
    Appelé après la complétion de l'onboarding si l'utilisateur a choisi 'personal' style.
    """
    # Récupérer les données d'onboarding
    onboarding = db.query(UserOnboarding).filter(
        UserOnboarding.user_id == user_id
    ).first()

    if not onboarding:
        print(f"⚠️  No onboarding found for user {user_id}")
        return

    # Vérifier si l'utilisateur a choisi le style personnel
    if not hasattr(onboarding, 'style_option') or onboarding.style_option != 'personal':
        print(f"ℹ️  User {user_id} didn't choose personal style")
        return

    # Vérifier s'il a fourni des URLs
    if not onboarding.social_urls:
        print(f"⚠️  No social URLs for user {user_id}")
        return

    try:
        social_urls = json.loads(onboarding.social_urls)
    except:
        print(f"❌ Error parsing social URLs for user {user_id}")
        return

    # Pour chaque URL fournie, créer un profil de style
    created_count = 0
    for platform_key, url in social_urls.items():
        if not url or not url.strip():
            continue

        # Détecter la plateforme
        platform = detect_platform_from_url(url)

        # Nom du style
        platform_names = {
            'linkedin': 'LinkedIn',
            'instagram': 'Instagram',
            'facebook': 'Facebook',
            'twitter': 'Twitter',
            'tiktok': 'TikTok',
            'youtube': 'YouTube'
        }
        style_name = f"Mon style {platform_names.get(platform, platform.title())}"

        # Vérifier si un profil existe déjà pour cette URL
        existing = db.query(UserStyleProfile).filter(
            UserStyleProfile.user_id == user_id,
            UserStyleProfile.source_url == url
        ).first()

        if existing:
            print(f"ℹ️  Profile already exists for {url}")
            continue

        # Créer le profil
        profile = UserStyleProfile(
            user_id=user_id,
            style_name=style_name,
            style_type='personal',
            platform=platform,
            source_url=url,
            status='pending'
        )

        db.add(profile)
        db.flush()  # Pour obtenir l'ID

        print(f"✅ Created style profile {profile.id} for {platform}")

        # Lancer l'analyse en background (dans un thread séparé pour ne pas bloquer)
        import threading
        thread = threading.Thread(
            target=analyze_style_profile,
            args=(profile.id, db)
        )
        thread.daemon = True
        thread.start()

        created_count += 1

    if created_count > 0:
        db.commit()
        print(f"✅ Created {created_count} style profiles for user {user_id}")
    else:
        print(f"ℹ️  No new style profiles created for user {user_id}")
