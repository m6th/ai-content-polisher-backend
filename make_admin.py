#!/usr/bin/env python3
"""Script pour rendre un utilisateur administrateur"""

import sys
from app.database import SessionLocal
from app.models import User

def make_admin(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ Utilisateur avec l'email {email} non trouvé")
            return False

        user.is_admin = 1
        db.commit()
        print(f"✅ L'utilisateur {email} est maintenant administrateur")
        print(f"   - Nom: {user.name}")
        print(f"   - Email: {user.email}")
        print(f"   - Admin: {user.is_admin}")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    email = "mathdu0609@gmail.com"
    make_admin(email)
