from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import users, content, analytics, admin, plans, ai, stripe_router

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
    allow_origins=["*"],  # En production, spécifie les domaines autorisés
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

@app.get("/")
def home():
    return {
        "message": "AI Content Polisher API 🚀",
        "status": "opérationnel",
        "docs": "/docs"
    }