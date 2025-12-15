from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from groq import Groq
import os
from ..database import get_db
from ..auth import get_current_user
from ..models import User

router = APIRouter(prefix="/ai", tags=["ai"])

# Pydantic models
class HashtagRequest(BaseModel):
    content: str
    platform: str
    language: str = "fr"

class HashtagResponse(BaseModel):
    hashtags: List[str]

class EmojiRequest(BaseModel):
    content: str
    platform: str

class EmojiResponse(BaseModel):
    emojis: List[str]

class AnalyzeRequest(BaseModel):
    content: str

class AnalyzeResponse(BaseModel):
    sentiment: str
    engagement_score: int
    suggestions: List[str]

class PostingTimeResponse(BaseModel):
    best_time: str
    reason: str
    peak_days: List[str]

class ImproveRequest(BaseModel):
    content: str
    tone: str
    language: str

class ImproveResponse(BaseModel):
    improved_content: str
    improvements: List[str]

# Initialize Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@router.post("/hashtags", response_model=HashtagResponse)
async def generate_hashtags(
    request: HashtagRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate relevant hashtags for content based on platform"""
    try:
        # Map platform to specific hashtag strategy
        platform_context = {
            "linkedin": "professional networking and business content",
            "twitter": "trending topics and concise engagement",
            "facebook": "community engagement and broad reach",
            "instagram": "visual content and lifestyle",
            "tiktok": "viral trends and entertainment",
            "youtube": "video content and SEO optimization"
        }

        context = platform_context.get(request.platform.lower(), "general social media")

        prompt = f"""Generate 8-12 relevant and trending hashtags for the following {request.platform} content.

Content: {request.content[:500]}

Requirements:
- Mix of popular and niche hashtags
- Relevant to {context}
- In {request.language} language
- No duplicates
- Return ONLY the hashtags, one per line, with # prefix

Hashtags:"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a social media expert specializing in hashtag strategy."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        hashtags_text = response.choices[0].message.content.strip()
        hashtags = [tag.strip() for tag in hashtags_text.split('\n') if tag.strip().startswith('#')]

        # Ensure we have hashtags
        if not hashtags:
            hashtags = ["#content", "#socialmedia", "#engagement"]

        return HashtagResponse(hashtags=hashtags[:12])

    except Exception as e:
        print(f"Error generating hashtags: {e}")
        # Return default hashtags on error
        return HashtagResponse(hashtags=["#content", "#socialmedia", "#engagement"])

@router.post("/emojis", response_model=EmojiResponse)
async def suggest_emojis(
    request: EmojiRequest,
    current_user: User = Depends(get_current_user)
):
    """Suggest relevant emojis for content"""
    try:
        prompt = f"""Suggest 5-8 relevant emojis for this {request.platform} content:

Content: {request.content[:300]}

Return ONLY the emojis, separated by spaces, no explanations."""

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an emoji expert for social media content."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=50
        )

        emojis_text = response.choices[0].message.content.strip()
        emojis = emojis_text.split()

        return EmojiResponse(emojis=emojis[:8])

    except Exception as e:
        print(f"Error suggesting emojis: {e}")
        return EmojiResponse(emojis=["✨", "🎯", "💡", "🚀", "⭐"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(
    request: AnalyzeRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze content for sentiment and engagement potential"""
    try:
        prompt = f"""Analyze this social media content:

Content: {request.content}

Provide:
1. Sentiment (positive/neutral/negative)
2. Engagement score (0-100)
3. 3 specific improvement suggestions

Format your response as JSON:
{{
  "sentiment": "positive/neutral/negative",
  "engagement_score": 75,
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a social media analytics expert. Always respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )

        import json
        result = json.loads(response.choices[0].message.content.strip())

        return AnalyzeResponse(
            sentiment=result.get("sentiment", "neutral"),
            engagement_score=min(100, max(0, result.get("engagement_score", 50))),
            suggestions=result.get("suggestions", [])[:3]
        )

    except Exception as e:
        print(f"Error analyzing content: {e}")
        return AnalyzeResponse(
            sentiment="neutral",
            engagement_score=50,
            suggestions=[
                "Add more engaging questions",
                "Include relevant hashtags",
                "Make the call-to-action clearer"
            ]
        )

@router.get("/best-posting-time", response_model=PostingTimeResponse)
async def get_best_posting_time(
    platform: str,
    current_user: User = Depends(get_current_user)
):
    """Get best posting times based on platform and industry data"""

    # Data based on social media research and best practices
    posting_times = {
        "linkedin": {
            "best_time": "Mardi-Jeudi, 9h-11h",
            "reason": "Activité maximale des professionnels pendant les heures de travail",
            "peak_days": ["Mardi", "Mercredi", "Jeudi"]
        },
        "twitter": {
            "best_time": "Lundi-Vendredi, 12h-13h",
            "reason": "Pic d'engagement pendant la pause déjeuner",
            "peak_days": ["Lundi", "Mercredi", "Vendredi"]
        },
        "facebook": {
            "best_time": "Mercredi-Vendredi, 13h-16h",
            "reason": "Engagement élevé en milieu d'après-midi",
            "peak_days": ["Mercredi", "Jeudi", "Vendredi"]
        },
        "instagram": {
            "best_time": "Lundi-Vendredi, 11h-14h",
            "reason": "Activité maximale pendant et après le déjeuner",
            "peak_days": ["Lundi", "Mercredi", "Vendredi"]
        },
        "tiktok": {
            "best_time": "Mardi-Jeudi, 18h-22h",
            "reason": "Pic d'engagement en soirée",
            "peak_days": ["Mardi", "Jeudi", "Samedi"]
        },
        "youtube": {
            "best_time": "Jeudi-Samedi, 14h-16h",
            "reason": "Meilleur moment pour les vidéos longue durée",
            "peak_days": ["Jeudi", "Vendredi", "Samedi"]
        }
    }

    platform_lower = platform.lower()
    data = posting_times.get(platform_lower, posting_times["linkedin"])

    return PostingTimeResponse(**data)

@router.post("/improve", response_model=ImproveResponse)
async def improve_content(
    request: ImproveRequest,
    current_user: User = Depends(get_current_user)
):
    """Get AI suggestions to improve content"""
    try:
        tone_map = {
            "professional": "professionnel et formel",
            "casual": "décontracté et amical",
            "engaging": "engageant et dynamique",
            "inspirational": "inspirant et motivant",
            "humorous": "humoristique et léger",
            "educational": "éducatif et informatif"
        }

        tone_desc = tone_map.get(request.tone, "engageant")

        prompt = f"""Improve this social media content to make it more {tone_desc}.

Original content: {request.content}

Language: {request.language}

Provide:
1. An improved version of the content
2. List 3 specific improvements made

Format as JSON:
{{
  "improved_content": "the improved text",
  "improvements": ["improvement 1", "improvement 2", "improvement 3"]
}}"""

        response = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": f"You are a social media copywriting expert. Always write in {request.language} and respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        import json
        result = json.loads(response.choices[0].message.content.strip())

        return ImproveResponse(
            improved_content=result.get("improved_content", request.content),
            improvements=result.get("improvements", [])[:3]
        )

    except Exception as e:
        print(f"Error improving content: {e}")
        return ImproveResponse(
            improved_content=request.content,
            improvements=["Error processing improvement request"]
        )
