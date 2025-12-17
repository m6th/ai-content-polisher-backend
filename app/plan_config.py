"""
Configuration centralisée des plans et leurs fonctionnalités
"""

PLAN_CONFIG = {
    'free': {
        'name': 'Gratuit',
        'price': 0,
        'credits': 3,
        'platforms': ['linkedin', 'instagram', 'tiktok'],  # 3 plateformes seulement
        'tones': ['professional', 'casual', 'engaging'],  # 3 tons seulement
        'languages': ['fr', 'en', 'es'],
        'history_days': 7,  # Historique limité à 7 jours
        'features': {
            'export': False,
            'analytics': False,
            'variants': 1,  # 1 seule version
            'hashtags': False,
            'multi_users': 1,
            'support': None,
            'api_access': False,
            'custom_tones': False,
            'bulk_export': False
        }
    },
    'starter': {
        'name': 'Starter',
        'price': 7.99,
        'credits': 40,
        'platforms': ['linkedin', 'instagram', 'facebook', 'twitter', 'tiktok'],  # Toutes
        'tones': ['professional', 'casual', 'engaging'],  # Mêmes 3 tons que free
        'languages': ['fr', 'en', 'es'],
        'history_days': None,  # Historique complet (illimité)
        'features': {
            'export': True,
            'analytics': False,
            'variants': 1,
            'hashtags': False,
            'multi_users': 1,
            'support': 'email_48h',
            'api_access': False,
            'custom_tones': False,
            'bulk_export': False
        }
    },
    'pro': {
        'name': 'Pro',
        'price': 17.99,
        'credits': 150,
        'platforms': ['linkedin', 'instagram', 'facebook', 'twitter', 'tiktok'],
        'tones': ['professional', 'casual', 'engaging', 'friendly', 'authoritative', 'inspirational', 'humorous'],  # Tous les tons
        'languages': ['fr', 'en', 'es'],
        'history_days': None,
        'features': {
            'export': True,
            'analytics': True,
            'variants': 3,  # 3 variantes
            'hashtags': True,
            'multi_users': 2,
            'support': 'email_24h',
            'api_access': False,
            'custom_tones': False,
            'bulk_export': False
        }
    },
    'business': {
        'name': 'Business',
        'price': 44.99,
        'credits': 500,
        'platforms': ['linkedin', 'instagram', 'facebook', 'twitter', 'tiktok'],
        'tones': ['professional', 'casual', 'engaging', 'friendly', 'authoritative', 'inspirational', 'humorous'],
        'languages': ['fr', 'en', 'es'],
        'history_days': None,
        'features': {
            'export': True,
            'analytics': True,
            'variants': 3,
            'hashtags': True,
            'multi_users': 5,
            'support': 'priority_12h_chat',
            'api_access': True,
            'custom_tones': True,
            'bulk_export': True,
            'extra_credits_price': 0.08  # Prix par crédit supplémentaire
        }
    }
}

# Mapping des anciens noms de plans vers les nouveaux
PLAN_MAPPING = {
    'free': 'free',
    'standard': 'starter',  # Ancien "standard" devient "starter"
    'premium': 'pro',       # Ancien "premium" devient "pro"
    'agency': 'business'    # Ancien "agency" devient "business"
}

# Limites des plans (pour Stripe)
PLAN_LIMITS = {
    'free': {
        'credits': 3,
        'max_requests_per_day': 3
    },
    'standard': {
        'credits': 40,
        'max_requests_per_day': 40
    },
    'premium': {
        'credits': 150,
        'max_requests_per_day': 150
    },
    'agency': {
        'credits': 500,
        'max_requests_per_day': 500
    }
}

def get_plan_config(plan_name: str) -> dict:
    """Récupère la configuration d'un plan"""
    # Mapper les anciens noms si nécessaire
    plan_name = PLAN_MAPPING.get(plan_name, plan_name)
    return PLAN_CONFIG.get(plan_name, PLAN_CONFIG['free'])

def get_plan_credits(plan_name: str) -> int:
    """Récupère le nombre de crédits d'un plan"""
    config = get_plan_config(plan_name)
    return config['credits']

def can_use_platform(plan_name: str, platform: str) -> bool:
    """Vérifie si un plan peut utiliser une plateforme"""
    config = get_plan_config(plan_name)
    return platform in config['platforms']

def can_use_tone(plan_name: str, tone: str) -> bool:
    """Vérifie si un plan peut utiliser un ton"""
    config = get_plan_config(plan_name)
    return tone in config['tones']

def get_available_platforms(plan_name: str) -> list:
    """Récupère les plateformes disponibles pour un plan"""
    config = get_plan_config(plan_name)
    return config['platforms']

def get_available_tones(plan_name: str) -> list:
    """Récupère les tons disponibles pour un plan"""
    config = get_plan_config(plan_name)
    return config['tones']
