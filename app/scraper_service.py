"""
Service de scraping et d'analyse de style pour les profils sociaux
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict, Optional
import os
from groq import Groq

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def scrape_linkedin_posts(profile_url: str, max_posts: int = 10) -> List[str]:
    """
    Scrape les posts LinkedIn d'un profil public.
    Note: LinkedIn nécessite une authentification. Cette version est un placeholder.
    Pour une vraie implémentation, il faudrait utiliser l'API LinkedIn ou un service tiers.
    """
    # TODO: Implémenter avec l'API LinkedIn officielle ou un service de scraping
    # Pour l'instant, retourne des exemples mockés
    return [
        "Exemple de post LinkedIn professionnel avec insights sur le leadership.",
        "Post sur l'innovation et la transformation digitale dans mon entreprise.",
        "Partage d'une réussite d'équipe et leçons apprises.",
    ]


def scrape_instagram_posts(profile_url: str, max_posts: int = 10) -> List[str]:
    """
    Scrape les captions Instagram d'un profil public.
    Note: Instagram a des restrictions strictes. Utiliser l'API Graph ou un service tiers.
    """
    # TODO: Implémenter avec Instagram Graph API
    # Pour l'instant, retourne des exemples mockés
    return [
        "Lifestyle post avec émojis ✨ et hashtags inspirants #motivation #success",
        "Story authentique sur mon parcours entrepreneurial 💪",
        "Partage de moment personnel avec une touche d'inspiration",
    ]


def scrape_facebook_posts(profile_url: str, max_posts: int = 10) -> List[str]:
    """
    Scrape les posts Facebook d'un profil ou page publique.
    Note: Facebook nécessite l'API Graph. Cette version est un placeholder.
    """
    # TODO: Implémenter avec Facebook Graph API
    # Pour l'instant, retourne des exemples mockés
    return [
        "Post communautaire engageant avec questions à l'audience.",
        "Partage d'article avec commentaire personnel et réflexions.",
        "Annonce d'événement avec ton chaleureux et invitant.",
    ]


def scrape_posts_by_platform(platform: str, profile_url: str, max_posts: int = 10) -> List[str]:
    """
    Scrape les posts selon la plateforme détectée.
    """
    if platform == 'linkedin':
        return scrape_linkedin_posts(profile_url, max_posts)
    elif platform == 'instagram':
        return scrape_instagram_posts(profile_url, max_posts)
    elif platform == 'facebook':
        return scrape_facebook_posts(profile_url, max_posts)
    else:
        # Pour les autres plateformes, utiliser un scraping générique
        return scrape_generic_content(profile_url, max_posts)


def scrape_generic_content(url: str, max_posts: int = 10) -> List[str]:
    """
    Scraping générique pour URLs non supportées.
    Tente d'extraire du contenu textuel de la page.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraire tous les paragraphes
        paragraphs = soup.find_all('p')
        texts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50]

        return texts[:max_posts] if texts else ["Contenu non accessible pour cette URL"]

    except Exception as e:
        print(f"Erreur lors du scraping générique: {e}")
        return ["Impossible d'accéder au contenu de cette URL"]


def analyze_writing_style(posts: List[str], platform: str, style_type: str) -> str:
    """
    Analyse le style d'écriture à partir des posts en utilisant Claude via Groq.

    Args:
        posts: Liste des posts à analyser
        platform: Plateforme d'origine (linkedin, instagram, etc.)
        style_type: 'personal' ou 'creator'

    Returns:
        Analyse détaillée du style d'écriture
    """
    if not posts or len(posts) == 0:
        return "Aucun post disponible pour l'analyse."

    # Préparer les posts pour l'analyse
    posts_text = "\n\n---\n\n".join([f"Post {i+1}:\n{post}" for i, post in enumerate(posts[:15])])

    system_prompt = """Tu es un expert en analyse de style d'écriture et de communication digitale.
Ta mission est d'analyser en profondeur le style d'écriture d'une personne à partir de ses publications sur les réseaux sociaux.

Tu dois identifier et décrire précisément :
1. **Ton général** : professionnel, décontracté, inspirant, humoristique, éducatif, etc.
2. **Structure des phrases** : longues/courtes, complexes/simples, type de ponctuation
3. **Vocabulaire** : niveau de langage, termes récurrents, expressions caractéristiques
4. **Utilisation d'émojis** : fréquence, types, placement
5. **Organisation du contenu** : hooks, storytelling, listes, questions
6. **Voix narrative** : 1ère personne, tutoiement/vouvoiement, proximité avec l'audience
7. **Thèmes récurrents** : sujets abordés, angles d'approche
8. **Éléments de branding** : signature, formules récurrentes

Fournis une analyse détaillée et actionnable qui permettra de reproduire ce style."""

    user_prompt = f"""Analyse le style d'écriture de cette personne sur {platform.upper()}.

Type d'analyse : {'Style personnel (reproduire le style de l\'utilisateur)' if style_type == 'personal' else 'Style d\'un créateur (imiter un influenceur/créateur)'}

Voici {len(posts)} publications récentes :

{posts_text}

Fournis une analyse complète et structurée du style d'écriture. Sois très spécifique et donne des exemples concrets tirés des posts."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        analysis = response.choices[0].message.content.strip()
        return analysis

    except Exception as e:
        print(f"Erreur lors de l'analyse IA: {e}")
        return f"Erreur lors de l'analyse du style: {str(e)}"


def analyze_style_from_url(
    source_url: str,
    platform: str,
    style_type: str,
    max_posts: int = 10
) -> Dict[str, any]:
    """
    Fonction principale qui scrape et analyse le style d'écriture.

    Returns:
        Dict avec 'style_analysis', 'sample_posts', et 'status'
    """
    try:
        # Étape 1: Scraper les posts
        print(f"📥 Scraping des posts depuis {platform}...")
        posts = scrape_posts_by_platform(platform, source_url, max_posts)

        if not posts or len(posts) == 0:
            return {
                'status': 'failed',
                'error_message': 'Aucun contenu trouvé à cette URL',
                'style_analysis': None,
                'sample_posts': None
            }

        print(f"✅ {len(posts)} posts récupérés")

        # Étape 2: Analyser le style avec l'IA
        print(f"🤖 Analyse du style d'écriture...")
        style_analysis = analyze_writing_style(posts, platform, style_type)

        if not style_analysis or "Erreur" in style_analysis:
            return {
                'status': 'failed',
                'error_message': 'Erreur lors de l\'analyse du style',
                'style_analysis': style_analysis,
                'sample_posts': json.dumps(posts, ensure_ascii=False)
            }

        print(f"✅ Analyse terminée")

        return {
            'status': 'ready',
            'error_message': None,
            'style_analysis': style_analysis,
            'sample_posts': json.dumps(posts, ensure_ascii=False)
        }

    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return {
            'status': 'failed',
            'error_message': str(e),
            'style_analysis': None,
            'sample_posts': None
        }
