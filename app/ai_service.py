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

    "tiktok": """Crée un script TikTok viral optimisé pour 20-40 secondes.

FORMAT OBLIGATOIRE:
[0-3s] 🎯 HOOK EXPLOSIF (question choc, fait surprenant, promesse forte)
[3-30s] 📱 CONTENU (3 points max, rythme rapide, visuellement descriptif)
[30-40s] 💥 CTA PUISSANT (like, partage, follow avec raison claire)

STYLE: Énergique, jeune, authentique. Beaucoup d'émojis. Phrases courtes et percutantes.
NOTE: Indique les moments clés pour les transitions visuelles.""",

    "youtube_short": """Crée un script YouTube Short captivant de 30-60 secondes.

STRUCTURE:
[0-3s] ⚡ HOOK IRRÉSISTIBLE (intrigue maximale)
[3-45s] 🎬 CONTENU PRINCIPAL (histoire, démonstration, révélation)
[45-60s] 👉 CTA + TEASE (abonne-toi + teaser prochaine vidéo)

STYLE: Rythmé, storytelling fort, émotions fortes. Garde le suspense.
ASTUCE: Utilise des chiffres, des superlatifs, crée de la curiosité.""",

    "twitter": """Crée DUX versions pour Twitter/X:

VERSION 1 - TWEET UNIQUE (280 caractères MAX):
Message percutant et complet. 1-2 émojis. 2-3 hashtags stratégiques.

VERSION 2 - THREAD (3-5 tweets):
1/ Hook + promesse claire
2-4/ Développement (1 idée = 1 tweet)
5/ Conclusion + CTA

STYLE: Direct, impactant, conversationnel. Optimisé pour le retweet.""",

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

    "facebook": """Crée un post Facebook optimisé pour l'engagement communautaire.

STRUCTURE:
• Intro personnelle et chaleureuse
• Histoire ou contenu de valeur
• Transition naturelle vers la discussion
• Question ouverte pour stimuler les commentaires
• 2-3 émojis bien dosés

LONGUEUR: 80-150 mots
STYLE: Conversationnel, comme si tu parlais à un ami. Crée du débat positif.""",

    "instagram_story": """Crée une série de 3-5 stories Instagram engageantes.

FORMAT PAR STORY:
Story 1: 🎯 Hook visuel + texte court (5-7 mots max)
Story 2-3: 📱 Contenu principal (texte court, émojis, call-out)
Story 4: 💫 CTA interactif (sondage, question, swipe up)

STYLE: Très visuel. Texte minimal. Émojis larges. Instructions pour les stickers.
NOTE: Indique les placements texte (haut/centre/bas) et les stickers à utiliser.""",

    "email": """Crée un email professionnel hautement convertissant.

STRUCTURE COMPLÈTE:
━━━━━━━━━━━━━━━━━━━━
📧 OBJET: [Accrocheur, curiosité ou bénéfice direct, 40-60 caractères]
━━━━━━━━━━━━━━━━━━━━

Bonjour [Prénom],

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

    "newsletter": """Crée une section de newsletter engageante et informative.

STRUCTURE:
━━━━━━━━━━━━━━━━━━━━
📰 TITRE SECTION (impactant, bénéfice clair)
━━━━━━━━━━━━━━━━━━━━

👋 Intro courte et personnelle (1-2 phrases)

📍 CONTENU PRINCIPAL:
• Point clé 1 → Pourquoi c'est important
• Point clé 2 → Action concrète
• Point clé 3 → Bénéfice direct

💡 INSIGHT/CONSEIL PRO: [Valeur ajoutée unique]

🔗 Ressources utiles:
→ Lien 1: [Titre descriptif]
→ Lien 2: [Titre descriptif]

✨ Mini-CTA: [Action simple et claire]

LONGUEUR: 150-250 mots
STYLE: Informatif, scannable, valeur ajoutée haute.""",

    "article": """Crée un mini-article de blog optimisé SEO et engagement.

STRUCTURE COMPLÈTE:
━━━━━━━━━━━━━━━━━━━━
📝 TITRE H1: [Accrocheur + Bénéfice + Curiosité]
━━━━━━━━━━━━━━━━━━━━

🎯 INTRODUCTION (2-3 phrases):
[Hook + Problème + Promesse de solution]

━━━━━━━━━━━━━━━━━━━━
📍 POINT CLÉ 1: [Sous-titre H2]
[Développement 2-3 phrases + exemple concret]

📍 POINT CLÉ 2: [Sous-titre H2]
[Développement 2-3 phrases + astuce actionnable]

📍 POINT CLÉ 3: [Sous-titre H2]
[Développement 2-3 phrases + bénéfice tangible]

━━━━━━━━━━━━━━━━━━━━
✅ CONCLUSION:
[Récap rapide + CTA ou réflexion finale]

LONGUEUR: 200-300 mots
STYLE: Informatif, fluide, SEO-friendly, structuré.""",

    "storytelling": """Transforme le contenu en récit captivant avec impact émotionnel maximal.

STRUCTURE NARRATIVE:
━━━━━━━━━━━━━━━━━━━━
🎬 SITUATION INITIALE:
[Contexte, personnage, situation de départ - créer l'identification]

⚡ ÉLÉMENT DÉCLENCHEUR:
[Problème, challenge, moment de bascule - créer la tension]

🌊 ÉPREUVES/DÉVELOPPEMENT:
[Obstacles, luttes, doutes - amplifier l'émotion]

💡 RÉVÉLATION/SOLUTION:
[Découverte, changement, nouvelle approche - créer l'espoir]

🌟 TRANSFORMATION:
[Résultat, nouvelle situation, leçon apprise - inspirer]

💬 MESSAGE CLEF:
[Morale, enseignement universel, call to action émotionnel]

LONGUEUR: 200-300 mots
STYLE: Émotionnel, descriptif, rythme narratif fort, humanisant.""",

    "persuasive": """Crée un contenu copywriting ultra-persuasif optimisé pour la conversion.

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
STYLE: Persuasif, urgent, orienté action, focus bénéfices pas features.""",

    "educational": """Crée un contenu pédagogique clair et actionnable.

STRUCTURE DIDACTIQUE:
━━━━━━━━━━━━━━━━━━━━
📚 CONCEPT PRINCIPAL:
[Explication simple en 1 phrase]

🎯 POURQUOI C'EST IMPORTANT:
[Contexte et pertinence - relie à la vie réelle]

📍 DÉCOMPOSITION (3-4 points):

1️⃣ [Sous-concept 1]
→ Explication simple
→ Exemple concret du quotidien
→ Analogie si utile

2️⃣ [Sous-concept 2]
→ Explication simple
→ Exemple concret
→ Piège à éviter

3️⃣ [Sous-concept 3]
→ Explication simple
→ Cas pratique d'application

💡 ASTUCE PRO:
[Raccourci, méthode mnémotechnique, ou conseil avancé]

✅ À RETENIR:
[Récap en 2-3 bullets points]

🎯 EXERCICE PRATIQUE:
[Action simple à faire immédiatement pour ancrer]

LONGUEUR: 200-300 mots
STYLE: Clair, progressif, exemples nombreux, actionnable.""",

    "humorous": """Transforme le contenu en version drôle et mémorable.

APPROCHES HUMORISTIQUES:
━━━━━━━━━━━━━━━━━━━━
🎭 OUVERTURE DÉCALÉE:
[Hook absurde, exagération, ou observation inattendue]

😄 DÉVELOPPEMENT AVEC HUMOUR:
• Utilise l'auto-dérision
• Comparaisons absurdes ou inattendues
• Situations relatable amplifiées
• Références pop culture (si pertinent)
• Jeux de mots subtils (pas forcés)

💬 TECHNIQUES:
→ Exagération comique
→ Contraste inattendu
→ Observation satirique douce
→ Timing (punchlines bien placées)

🎯 MESSAGE SOUS-JACENT:
[Garde le message principal mais emballé dans l'humour]

😎 CLOSING:
[Chute drôle OU call-back au hook OU twist final]

NOTE: Reste bon enfant. Évite l'humour méchant ou clivant.
LONGUEUR: 150-250 mots
STYLE: Léger, énergique, émojis nombreux, tonalité positive.""",

    "dramatic": """Crée une version dramatique et intensément émotionnelle.

STRUCTURE DRAMATIQUE:
━━━━━━━━━━━━━━━━━━━━
⚡ OUVERTURE PERCUTANTE:
[Affirmation forte, stat choquante, ou déclaration audacieuse]

🌊 MONTÉE EN TENSION:
[Amplifie les enjeux - rends tout plus grand, plus important, plus urgent]

• Utilise des métaphores puissantes
• Vocabulaire intense (guerre, révolution, transformation)
• Contrasts extrêmes (avant/après)
• Enjeux existentiels ou turning points

💥 CLIMAX:
[Moment de vérité - révélation, prise de conscience, ou appel à l'action]

⚡ AMPLIFICATION ÉMOTIONNELLE:
→ Utilise "Ce n'est pas juste..., c'est..."
→ Questions rhétoriques puissantes
→ Répétitions pour emphase
→ Phrases courtes percutantes

🔥 CLOSING MÉMORABLE:
[Phrase choc finale - reste en tête, inspire l'action]

NOTE: Reste crédible. L'intensité doit servir le message.
LONGUEUR: 200-300 mots
STYLE: Intense, rythmé, émotionnel, mémorable, vocabulaire fort."""
}

TONE_MODIFIERS = {
    "professional": "Adopte un ton professionnel, formel et expert. Vocabulaire précis et crédible.",
    "casual": "Adopte un ton décontracté, amical et accessible. Parle comme à un ami proche.",
    "engaging": "Adopte un ton très engageant, dynamique et captivant. Crée de l'excitation et de l'énergie.",
    "inspirational": "Adopte un ton inspirant et motivant. Élève et pousse à l'action positive.",
    "educational": "Adopte un ton pédagogique et didactique. Explique clairement, étape par étape.",
    "humorous": "Adopte un ton humoristique et léger. Amuse tout en gardant le message principal.",
    "dramatic": "Adopte un ton dramatique et intense. Crée de l'impact émotionnel fort.",
    "persuasive": "Adopte un ton persuasif style copywriting. Focus sur la conversion et l'action."
}

LANGUAGE_NAMES = {
    "fr": "français",
    "en": "anglais",
    "es": "espagnol"
}

# Tokens optimaux par format (certains formats sont plus longs)
FORMAT_MAX_TOKENS = {
    "linkedin": 500,
    "tiktok": 400,
    "youtube_short": 450,
    "twitter": 350,
    "instagram": 600,
    "facebook": 400,
    "instagram_story": 500,
    "email": 600,
    "newsletter": 700,
    "article": 800,
    "storytelling": 700,
    "persuasive": 800,
    "educational": 750,
    "humorous": 500,
    "dramatic": 650
}

def polish_content_multi_format(original_text: str, tone: str = "professional", language: str = "fr") -> dict:
    """
    Génère TOUS les formats en une seule fois avec prompts optimisés
    """
    results = {}
    total_tokens = 0

    language_name = LANGUAGE_NAMES.get(language, "français")
    tone_modifier = TONE_MODIFIERS.get(tone, TONE_MODIFIERS["professional"])

    for format_key, format_prompt in FORMAT_PROMPTS.items():
        try:
            # Système de prompt en deux parties pour meilleure qualité
            system_message = f"""Tu es un expert de niveau mondial en création de contenu digital et copywriting.

MISSION: {format_prompt}

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

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Contenu à transformer:\n\n{original_text}"}
                ],
                temperature=0.8,  # Augmenté pour plus de créativité
                max_tokens=max_tokens,
                top_p=0.95,  # Pour diversité contrôlée
                presence_penalty=0.1,  # Évite les répétitions
                frequency_penalty=0.1  # Encourage la variété
            )

            polished_text = response.choices[0].message.content.strip()
            total_tokens += response.usage.total_tokens

            # Post-traitement: nettoie les artefacts potentiels
            polished_text = clean_generated_content(polished_text)

            results[format_key] = polished_text

        except Exception as e:
            print(f"❌ Erreur pour {format_key}: {e}")
            results[format_key] = f"[Erreur lors de la génération du format {format_key}. Veuillez réessayer.]"

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