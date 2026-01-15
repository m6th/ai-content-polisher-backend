from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Configuration pour Neon PostgreSQL (serverless avec SSL)
# Neon utilise un connection pooler qui nécessite des paramètres spécifiques
connect_args = {}

if DATABASE_URL and "neon.tech" in DATABASE_URL:
    # Neon requiert SSL et a des paramètres spécifiques pour le pooler
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 30,
    }
    # Pool configuration optimisée pour serverless
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300,  # Recycle connections toutes les 5 minutes
        pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    )
else:
    # Configuration standard pour autres bases PostgreSQL
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()