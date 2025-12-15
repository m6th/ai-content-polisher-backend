"""
Script de renouvellement automatique des crédits mensuels
À exécuter quotidiennement via un cron job
"""
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import User
from app.plan_config import get_plan_credits
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def renew_credits_for_users():
    """
    Renouvelle les crédits pour tous les utilisateurs dont le dernier renouvellement
    date de plus de 30 jours
    """
    db = SessionLocal()
    try:
        # Date limite : il y a 30 jours
        renewal_cutoff = datetime.utcnow() - timedelta(days=30)

        # Récupérer tous les utilisateurs dont le dernier renouvellement est ancien
        users_to_renew = db.query(User).filter(
            User.last_credit_renewal <= renewal_cutoff
        ).all()

        logger.info(f"🔄 Trouvé {len(users_to_renew)} utilisateur(s) à renouveler")

        renewed_count = 0
        for user in users_to_renew:
            # Récupérer le nombre de crédits pour le plan de l'utilisateur
            plan_credits = get_plan_credits(user.current_plan)

            # Renouveler les crédits
            user.credits_remaining = plan_credits
            user.last_credit_renewal = datetime.utcnow()

            logger.info(
                f"✅ Crédits renouvelés pour {user.email} "
                f"(Plan: {user.current_plan}, Crédits: {plan_credits})"
            )
            renewed_count += 1

        db.commit()
        logger.info(f"✨ Renouvellement terminé : {renewed_count} utilisateur(s) renouvelé(s)")

        return renewed_count

    except Exception as e:
        logger.error(f"❌ Erreur lors du renouvellement : {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def force_renew_for_user(email: str):
    """
    Force le renouvellement des crédits pour un utilisateur spécifique
    Utilisé par l'endpoint admin
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        if not user:
            logger.error(f"❌ Utilisateur {email} non trouvé")
            return False

        # Récupérer le nombre de crédits pour le plan de l'utilisateur
        plan_credits = get_plan_credits(user.current_plan)

        # Renouveler les crédits
        user.credits_remaining = plan_credits
        user.last_credit_renewal = datetime.utcnow()

        db.commit()
        logger.info(
            f"✅ Crédits renouvelés pour {user.email} "
            f"(Plan: {user.current_plan}, Crédits: {plan_credits})"
        )

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors du renouvellement : {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("🚀 Démarrage du script de renouvellement des crédits")
    renewed = renew_credits_for_users()
    logger.info(f"🎯 Script terminé : {renewed} utilisateur(s) renouvelé(s)")
