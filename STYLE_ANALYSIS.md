# Système d'Analyse de Style Personnalisé

## Vue d'ensemble

Ce système permet aux utilisateurs de créer des styles d'écriture personnalisés basés sur :
1. **Leur propre style** : Analyse de leurs publications sur les réseaux sociaux
2. **Style d'un créateur** : Imitation du style d'un influenceur/créateur

## Architecture

### 1. Base de données (`user_style_profiles`)

```sql
CREATE TABLE user_style_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    style_name VARCHAR NOT NULL,           -- "Mon style LinkedIn"
    style_type VARCHAR NOT NULL,           -- 'personal' ou 'creator'
    platform VARCHAR,                      -- 'linkedin', 'instagram', etc.
    source_url VARCHAR NOT NULL,          -- URL du profil
    style_analysis TEXT,                  -- Analyse détaillée du style
    sample_posts TEXT,                    -- JSON des posts échantillons
    status VARCHAR DEFAULT 'pending',     -- 'pending', 'analyzing', 'ready', 'failed'
    error_message TEXT,
    last_analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Service de Scraping (`app/scraper_service.py`)

#### Fonctions principales :

- `scrape_posts_by_platform()` : Scrape selon la plateforme
- `analyze_writing_style()` : Analyse IA du style via Groq/Claude
- `analyze_style_from_url()` : Fonction principale orchestrant scraping + analyse

#### Plateformes supportées :

✅ **LinkedIn** : Posts professionnels (nécessite API ou service tiers)
✅ **Instagram** : Captions des posts (nécessite Graph API)
✅ **Facebook** : Posts publics (nécessite Graph API)
⚠️ **Twitter/TikTok/YouTube** : Limités par restrictions API

#### Flow d'analyse :

```
1. User crée un style profile → status = 'pending'
2. Background task démarre → status = 'analyzing'
3. Scraping des 10-15 derniers posts
4. Analyse IA du style d'écriture (Groq/Claude)
5. Sauvegarde → status = 'ready' ou 'failed'
```

### 3. API Endpoints (`/styles`)

#### GET `/styles/available-tones`
Retourne tous les tons disponibles :
- Tons prédéfinis (Professionnel, Engageant, etc.)
- Styles personnalisés de l'utilisateur

```json
[
  {
    "id": "professional",
    "name": "Professionnel",
    "type": "predefined"
  },
  {
    "id": "custom_123",
    "name": "Mon style LinkedIn",
    "type": "custom",
    "status": "ready",
    "platform": "linkedin"
  }
]
```

#### POST `/styles/create`
Crée un nouveau profil de style :
```json
{
  "style_type": "personal",
  "source_url": "https://linkedin.com/in/username",
  "style_name": "Mon style LinkedIn" // optionnel
}
```

#### DELETE `/styles/{id}`
Supprime un profil de style

#### POST `/styles/{id}/reanalyze`
Relance l'analyse (utile si les posts ont changé)

### 4. Intégration dans la génération de contenu

Fichier : `app/ai_service.py`

```python
def polish_content_multi_format(
    original_text: str,
    tone: str = "professional",
    language: str = "fr",
    user_plan: str = "free",
    custom_style_analysis: str = None  # ← Nouveau paramètre
):
    if custom_style_analysis:
        tone_modifier = f"""STYLE PERSONNALISÉ À IMITER:
        {custom_style_analysis}

        IMPORTANT: Reproduis fidèlement ce style d'écriture...
        """
    else:
        tone_modifier = TONE_MODIFIERS.get(tone, ...)
```

Quand le user sélectionne un ton commençant par `custom_`, le système :
1. Récupère le `UserStyleProfile` correspondant
2. Extrait le `style_analysis`
3. L'injecte dans le prompt de génération
4. L'IA reproduit le style analysé

## Amélioration du Scraping (Production)

### Limitations actuelles

Le scraping actuel utilise des **posts mockés** pour les plateformes nécessitant une authentification. Pour une implémentation production, il faut :

### 1. LinkedIn

**Option A : API LinkedIn officielle**
```bash
# Installation
pip install linkedin-api

# Utilisation
from linkedin_api import Linkedin
api = Linkedin(email, password)
profile = api.get_profile_posts(public_id='username')
```

**Option B : Service tiers**
- Apify (https://apify.com/apify/linkedin-profile-scraper)
- Bright Data
- ScraperAPI

### 2. Instagram

**Graph API (recommandé)**
```bash
# Nécessite compte Business/Creator
import requests

url = f"https://graph.instagram.com/me/media"
params = {
    'fields': 'caption,timestamp,media_type',
    'access_token': INSTAGRAM_ACCESS_TOKEN
}
response = requests.get(url, params=params)
```

**Alternative : Instaloader**
```bash
pip install instaloader
import instaloader

L = instaloader.Instaloader()
profile = instaloader.Profile.from_username(L.context, 'username')
for post in profile.get_posts():
    print(post.caption)
```

### 3. Facebook

**Graph API**
```python
import requests

url = f"https://graph.facebook.com/v18.0/{page_id}/posts"
params = {
    'fields': 'message,created_time',
    'access_token': FB_ACCESS_TOKEN
}
response = requests.get(url, params=params)
```

### 4. Twitter/X

**API v2 (payante)**
```python
import tweepy

client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
tweets = client.get_users_tweets(
    id=user_id,
    max_results=10,
    tweet_fields=['text', 'created_at']
)
```

## Configuration Recommandée

### Variables d'environnement à ajouter :

```bash
# LinkedIn
LINKEDIN_EMAIL=your_email
LINKEDIN_PASSWORD=your_password

# Instagram Graph API
INSTAGRAM_ACCESS_TOKEN=your_token

# Facebook Graph API
FACEBOOK_ACCESS_TOKEN=your_token

# Twitter API v2
TWITTER_BEARER_TOKEN=your_token

# Services tiers (optionnel)
APIFY_API_KEY=your_key
SCRAPERAPI_KEY=your_key
```

## Workflow Utilisateur Complet

### 1. Pendant l'onboarding

Si l'utilisateur choisit "Mon style personnel" et fournit des URLs :
```
Onboarding complété
→ create_styles_from_onboarding() appelé automatiquement
→ Crée un UserStyleProfile pour chaque URL fournie
→ Lance l'analyse en background pour chacun
```

### 2. Ajout manuel d'un style

Via le bouton "Nouveau style" dans le Dashboard :
```
User clique "Nouveau style"
→ Modal s'ouvre
→ User choisit type (personnel/créateur) et entre URL
→ POST /styles/create
→ Profil créé avec status='pending'
→ Background task lance le scraping + analyse
→ Frontend recharge les tons disponibles
→ Nouveau style apparaît dans le dropdown avec icône de status
```

### 3. Utilisation du style

```
User sélectionne "✅ Mon style LinkedIn" dans le dropdown
→ Génère du contenu
→ Backend détecte tone="custom_123"
→ Récupère le style_analysis de la DB
→ Injecte dans le prompt IA
→ Contenu généré imite le style de l'utilisateur
```

## Monitoring et Logs

Le système log toutes les étapes :
```
🔄 Starting analysis for profile 123 (linkedin)
📥 Scraping des posts depuis linkedin...
✅ 10 posts récupérés
🤖 Analyse du style d'écriture...
✅ Analyse terminée
✅ Analysis completed for profile 123: ready
```

En cas d'erreur :
```
❌ Error analyzing profile 123: Connection timeout
→ status = 'failed'
→ error_message stocké en DB
→ User voit ❌ dans le dropdown
```

## Tests Recommandés

1. **Test avec URLs mockées** : Vérifier le flow complet
2. **Test analyse IA** : S'assurer que Claude analyse bien le style
3. **Test génération** : Vérifier que le style est appliqué
4. **Test erreurs** : URLs invalides, timeouts, etc.

## Coûts Estimés

- **API LinkedIn** : Gratuit avec limitations
- **Instagram Graph API** : Gratuit
- **Facebook Graph API** : Gratuit
- **Twitter API v2** : $100/mois (Basic tier)
- **Services tiers (Apify, etc.)** : $49-$499/mois selon usage

## Prochaines Améliorations

1. ✅ Cache des analyses (ne pas re-scraper trop souvent)
2. ✅ Permettre à l'user de modifier l'analyse manuellement
3. ✅ Suggestions de styles basées sur l'industrie/niche
4. ✅ Analyse comparative entre plusieurs styles
5. ✅ A/B testing des styles pour voir lequel performe mieux
