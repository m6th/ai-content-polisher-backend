from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import users, content, analytics, admin, plans, ai, stripe_router, calendar, teams, trial, api_keys, api_v1, onboarding

# Crée les tables (au cas où)
Base.metadata.create_all(bind=engine)

# Run migrations
try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from run_migrations import run_migrations
    run_migrations()
except Exception as e:
    print(f"Warning: Could not run migrations: {e}")

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
app.include_router(trial.router)
app.include_router(api_keys.router)  # Gestion des clés API
app.include_router(api_v1.router)    # API publique v1
app.include_router(onboarding.router)  # Onboarding utilisateur

@app.get("/")
def home():
    return {
        "message": "AI Content Polisher API 🚀",
        "status": "opérationnel",
        "docs": "/docs"
    }