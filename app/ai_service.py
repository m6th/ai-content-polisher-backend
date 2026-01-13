import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Prompts améliorés pour chaque format avec instructions détaillées
FORMAT_PROMPTS = {
    "linkedin": """Crée un post LinkedIn professionnel et engageant optimisé pour l'algorithme.

STRUCTURE OBLIGATOIRE:
• Hook puissant (première ligne pour capter l'attention)
• Développement avec valeur ajoutée (insights, conseils pratiques)
• Appel à l'action clair
• 3-5 hashtags pertinents et populaires
• 2-4 émojis professionnels bien placés

LONGUEUR: 100-200 mots
STYLE: Professionnel mais accessible, crée de l'engagement""",

    "instagram": """Crée une caption Instagram hautement engageante.

STRUCTURE:
📸 HOOK VISUEL (3-5 mots qui arrêtent le scroll)

[Corps du message avec beaucoup d'émojis et de sauts de ligne]
• Raconte une micro-histoire OU
• Partage une transformation OU
• Donne des conseils actionnables

💬 QUESTION D'ENGAGEMENT (pour stimuler les commentaires)

#Hashtags (10-15 hashtags mélangés: populaires + niches + ultra-spécifiques)

LONGUEUR: 150-300 mots
STYLE: Inspirant, authentique, visuellement aéré""",

    "tiktok": """Crée un script TikTok viral optimisé pour 20-40 secondes.

FORMAT OBLIGATOIRE:
[0-3s] 🎯 HOOK EXPLOSIF (question choc, fait surprenant, promesse forte)
[3-30s] 📱 CONTENU (3 points max, rythme rapide, visuellement descriptif)
[30-40s] 💥 CTA PUISSANT (like, partage, follow avec raison claire)

STYLE: Énergique, jeune, authentique. Beaucoup d'émojis. Phrases courtes et percutantes.
NOTE: Indique les moments clés pour les transitions visuelles.""",

    "twitter": """Crée DEUX versions pour Twitter/X:

VERSION 1 - TWEET UNIQUE (280 caractères MAX):
Message percutant et complet. 1-2 émojis. 2-3 hashtags stratégiques.

VERSION 2 - THREAD (3-5 tweets):
1/ Hook + promesse claire
2-4/ Développement (1 idée = 1 tweet)
5/ Conclusion + CTA

STYLE: Direct, impactant, conversationnel. Optimisé pour le retweet.""",

    "email": """Crée un email professionnel hautement convertissant.

STRUCTURE COMPLÈTE:
━━━━━━━━━━━━━━━━━━━━
📧 OBJET: [Accrocheur, curiosité ou bénéfice direct, 40-60 caractères]
━━━━━━━━━━━━━━━━━━━━

Bonjour,

[OUVERTURE PERSONNALISÉE - fait référence à un contexte commun]

[CORPS DU MESSAGE]
• Contexte rapide
• Valeur ajoutée principale
• Bénéfices concrets (bullet points)
• Preuve sociale ou résultats (si pertinent)

[CTA CLAIR ET ACTIONNABLE]
→ Bouton/lien avec action spécifique

[SIGNATURE]
Cordialement,
[Signature avec contact]

LONGUEUR: 100-200 mots
STYLE: Professionnel mais chaleureux. Scannable. CTA visible.""",

    "persuasive": """Crée un contenu publicitaire ultra-persuasif optimisé pour la conversion.

FRAMEWORK AIDA AMÉLIORÉ:
━━━━━━━━━━━━━━━━━━━━
🎯 ATTENTION:
[Hook irrésistible - stat choc, question provocante, ou affirmation audacieuse]

🔥 PROBLÈME + AGITATION:
[Décris le problème de manière viscérale]
→ Conséquences négatives (douleur amplifiée)
→ Pourquoi les autres solutions ne marchent pas
→ Urgence et coût de l'inaction

💡 SOLUTION:
[Présente TA solution comme LA réponse évidente]
→ Comment ça marche (simple et clair)
→ Pourquoi c'est différent (unique selling point)

✨ BÉNÉFICES:
[Liste 3-5 transformations concrètes]
✓ Bénéfice 1 (avec résultat mesurable)
✓ Bénéfice 2 (avec économie temps/argent)
✓ Bénéfice 3 (avec impact émotionnel)

🏆 PREUVE SOCIALE:
[Résultats, témoignages, chiffres crédibles]

⚡ CTA PUISSANT:
[Action immédiate + bénéfice + urgence/rareté]

LONGUEUR: 250-350 mots
STYLE: Persuasif, urgent, orienté action, focus bénéfices pas features."""
}

TONE_MODIFIERS = {
    "professional": "Adopte un ton professionnel, formel et expert. Vocabulaire précis et crédible.",
    "engaging": "Adopte un ton très engageant, dynamique et captivant. Crée de l'excitation et de l'énergie.",
    "storytelling": "Adopte un ton narratif et captivant. Raconte une histoire avec émotions, personnages et arc narratif. Crée de l'identification et de l'impact émotionnel."
}

LANGUAGE_NAMES = {
    "fr": "français",
    "en": "anglais",
    "es": "espagnol"
}

# Tokens optimaux par format (certains formats sont plus longs)
FORMAT_MAX_TOKENS = {
    "linkedin": 500,
    "instagram": 600,
    "tiktok": 400,
    "twitter": 350,
    "email": 600,
    "persuasive": 800
}

def polish_content_multi_format(original_text: str, tone: str = "professional", language: str = "fr", user_plan: str = "free", custom_style_analysis: str = None) -> dict:
    """
    Génère les formats selon le plan de l'utilisateur avec prompts optimisés
    Génère 3 variantes pour les plans Pro et Business

    Args:
        custom_style_analysis: Analyse du style personnalisé de l'utilisateur (si disponible)
    """
    import time
    from .plan_config import get_plan_config

    results = {}
    total_tokens = 0

    language_name = LANGUAGE_NAMES.get(language, "français")

    # Si un style custom est fourni, l'utiliser à la place du tone_modifier prédéfini
    if custom_style_analysis:
        tone_modifier = f"""STYLE PERSONNALISÉ À IMITER:
{custom_style_analysis}

IMPORTANT: Reproduis fidèlement ce style d'écriture, y compris:
- Le ton et la voix
- Les expressions et tournures de phrases caractéristiques
- La structure et l'organisation des idées
- L'utilisation d'émojis, ponctuation, et mise en forme
- Le niveau de formalité et les choix de vocabulaire"""
    else:
        tone_modifier = TONE_MODIFIERS.get(tone, TONE_MODIFIERS["professional"])

    # Récupère le nombre de variantes selon le plan
    plan_config = get_plan_config(user_plan)
    num_variants = plan_config.get('features', {}).get('variants', 1)

    # Limiter les formats pour le plan free (3 formats seulement)
    if user_plan == "free":
        allowed_formats = ["linkedin", "instagram", "tiktok"]
        formats_to_generate = {k: v for k, v in FORMAT_PROMPTS.items() if k in allowed_formats}
        delay_ms = 0  # Pas de délai pour free (seulement 3 formats)
    else:
        # Plans payants : tous les 6 formats
        formats_to_generate = FORMAT_PROMPTS
        delay_ms = 100  # 100ms de délai entre chaque requête pour les plans payants

    for format_key, format_prompt in formats_to_generate.items():
        # Générer plusieurs variantes pour Pro/Business
        format_variants = []

        for variant_num in range(num_variants):
            try:
                # Système de prompt en deux parties pour meilleure qualité
                variant_instruction = ""
                if num_variants > 1:
                    if variant_num == 0:
                        variant_instruction = "\n\n🎯 VARIANTE 1: Version équilibrée et polyvalente."
                    elif variant_num == 1:
                        variant_instruction = "\n\n🎯 VARIANTE 2: Version plus audacieuse et créative avec un angle différent."
                    elif variant_num == 2:
                        variant_instruction = "\n\n🎯 VARIANTE 3: Version alternative avec une approche unique et originale."

                system_message = f"""Tu es un expert de niveau mondial en création de contenu digital et copywriting.

MISSION: {format_prompt}{variant_instruction}

TON À ADOPTER: {tone_modifier}

LANGUE: Écris exclusivement en {language_name}.

RÈGLES CRITIQUES:
✓ Suis EXACTEMENT la structure indiquée dans la mission
✓ Réponds UNIQUEMENT avec le contenu final prêt à publier
✓ N'ajoute AUCUNE explication, commentaire ou méta-texte
✓ Ne mentionne jamais "[Prénom]", "[Nom]" ou autres placeholders - utilise des formulations génériques
✓ Optimise pour l'engagement et la viralité
✓ Sois authentique et humain dans le ton"""

                # Max tokens adapté au format
                max_tokens = FORMAT_MAX_TOKENS.get(format_key, 600)

                # Température variable pour plus de diversité entre variantes
                temperature = 0.8 + (variant_num * 0.1)  # 0.8, 0.9, 1.0

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"Contenu à transformer:\n\n{original_text}"}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.95,
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                )

                polished_text = response.choices[0].message.content.strip()
                total_tokens += response.usage.total_tokens

                # Post-traitement: nettoie les artefacts potentiels
                polished_text = clean_generated_content(polished_text)

                format_variants.append(polished_text)

                # Ajouter un délai entre les requêtes pour éviter les rate limits
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)

            except Exception as e:
                print(f"❌ Erreur pour {format_key} variante {variant_num + 1}: {e}")
                format_variants.append(f"[Erreur lors de la génération de la variante {variant_num + 1}. Veuillez réessayer.]")

        # Stocker les variantes (soit une seule, soit plusieurs)
        results[format_key] = format_variants if num_variants > 1 else format_variants[0]

    return results, total_tokens

def clean_generated_content(text: str) -> str:
    """
    Nettoie le contenu généré des artefacts communs
    """
    # Retire les phrases méta communes
    meta_phrases = [
        "Voici le contenu",
        "Voici la version",
        "Voici le post",
        "Voici l'email",
        "Voici le script",
        "Voici un",
        "Voici une",
        "Version finale:",
        "Contenu final:",
    ]

    for phrase in meta_phrases:
        if text.lower().startswith(phrase.lower()):
            # Retire la première ligne
            text = '\n'.join(text.split('\n')[1:]).strip()

    # Retire les guillemets englobants si présents
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]

    # Retire les espaces multiples
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 sauts de ligne
    text = re.sub(r' {2,}', ' ', text)  # Max 1 espace

    return text.strip()

def generate_ai_suggestions(content: str, language: str = "fr") -> dict:
    """
    Génère des suggestions d'amélioration IA pour le contenu
    Analyse le contenu et propose des améliorations concrètes
    """
    try:
        language_name = LANGUAGE_NAMES.get(language, "français")

        system_message = f"""Tu es un expert en optimisation de contenu et copywriting.

MISSION: Analyse ce contenu et génère des suggestions d'amélioration concrètes.

ANALYSE À FAIRE:
1. Score d'engagement potentiel (0-100)
2. Points forts du contenu (2-3 éléments)
3. Axes d'amélioration (3-4 suggestions actionnables)
4. Mots-clés SEO recommandés (5-7 mots-clés)
5. Émojis suggérés pour plus d'impact (3-5 émojis)

LANGUE: Analyse et réponds en {language_name}.

FORMAT DE RÉPONSE (JSON strict):
{{
  "engagement_score": 75,
  "strengths": ["Point fort 1", "Point fort 2"],
  "improvements": ["Amélioration 1", "Amélioration 2", "Amélioration 3"],
  "keywords": ["mot1", "mot2", "mot3"],
  "suggested_emojis": ["💡", "🚀", "✨"]
}}

Réponds UNIQUEMENT avec le JSON, sans texte supplémentaire."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Contenu à analyser:\n\n{content[:800]}"}
            ],
            temperature=0.5,
            max_tokens=400
        )

        import json
        suggestions_text = response.choices[0].message.content.strip()

        # Parse le JSON
        try:
            suggestions = json.loads(suggestions_text)
            return suggestions
        except json.JSONDecodeError:
            # Fallback si le JSON est malformé
            return {
                "engagement_score": 50,
                "strengths": ["Contenu structuré"],
                "improvements": ["Ajouter plus d'émojis", "Renforcer le call-to-action"],
                "keywords": ["contenu", "digital", "marketing"],
                "suggested_emojis": ["💡", "🚀"]
            }

    except Exception as e:
        print(f"❌ Erreur génération suggestions: {e}")
        return {
            "engagement_score": 0,
            "strengths": [],
            "improvements": [],
            "keywords": [],
            "suggested_emojis": []
        }

def generate_hashtags(content: str, language: str = "fr", count: int = 10) -> list:
    """
    Génère des hashtags pertinents et stratégiques pour le contenu
    Mix de hashtags populaires, moyens et de niches
    """
    try:
        language_name = LANGUAGE_NAMES.get(language, "français")

        system_message = f"""Tu es un expert en stratégie de hashtags pour les réseaux sociaux.

MISSION: Génère exactement {count} hashtags stratégiques pour maximiser la portée.

STRATÉGIE À SUIVRE:
• 30% hashtags populaires (>100k posts) - pour la visibilité
• 40% hashtags moyens (10k-100k posts) - pour l'engagement
• 30% hashtags de niche (<10k posts) - pour cibler précisément

RÈGLES:
✓ Hashtags en {language_name} uniquement
✓ Sans espaces, sans caractères spéciaux
✓ Pertinents au contenu ET à l'industrie
✓ Mélange de hashtags génériques et spécifiques
✓ Inclus des hashtags tendances si pertinent
✓ Format: #Hashtag (avec majuscules pour lisibilité)

RETOURNE UNIQUEMENT la liste des hashtags, un par ligne, sans numéros ni explications."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Contenu:\n{content[:500]}"}  # Limite à 500 chars pour économiser
            ],
            temperature=0.7,
            max_tokens=200
        )

        hashtags_text = response.choices[0].message.content.strip()

        # Parse les hashtags
        hashtags = []
        for line in hashtags_text.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                hashtags.append(line)
            elif line and not line[0].isdigit():  # Pas une numérotation
                # Ajoute # si manquant
                hashtags.append(f"#{line}" if not line.startswith('#') else line)

        return hashtags[:count]  # Limite au nombre demandé

    except Exception as e:
        print(f"❌ Erreur génération hashtags: {e}")
        return []