from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import users, content, analytics, admin, plans, ai, stripe_router, calendar, teams

# Crée les tables (au cas où)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Content Polisher",
    description="API pour transformer du texte en contenu adapté aux réseaux sociaux",
    version="1.0.0"
)

# CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Développement local
        "http://127.0.0.1:5173",  # Développement local
        "https://ai-content-polisher-frontend.vercel.app",  # Production Vercel
        "https://aicontentpolisher.com",  # Domaine personnalisé (futur)
        "https://www.aicontentpolisher.com",  # Domaine personnalisé avec www
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routers
app.include_router(users.router)
app.include_router(content.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(plans.router)
app.include_router(ai.router)
app.include_router(stripe_router.router)
app.include_router(calendar.router)
app.include_router(teams.router)

@app.get("/")
def home():
    return {
        "message": "AI Content Polisher API 🚀",
        "status": "opérationnel",
        "docs": "/docs"
    }