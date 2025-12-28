"""
Script pour envoyer les rappels de calendrier (24h et 1h avant publication)
À exécuter toutes les heures via cron
"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models
from app.email_service import send_calendar_reminder


def send_reminders():
    """Envoie les rappels pour les contenus planifiés"""
    db: Session = SessionLocal()

    try:
        now = datetime.utcnow()

        # Trouver les contenus nécessitant un rappel 24h
        reminder_24h_time = now + timedelta(hours=24)
        # Tolérance de ±30 minutes pour le rappel 24h
        scheduled_24h = db.query(models.ScheduledContent).filter(
            models.ScheduledContent.status == "scheduled",
            models.ScheduledContent.reminder_24h_sent == False,
            models.ScheduledContent.scheduled_date >= reminder_24h_time - timedelta(minutes=30),
            models.ScheduledContent.scheduled_date <= reminder_24h_time + timedelta(minutes=30)
        ).all()

        print(f"\n📅 Vérification des rappels 24h: {len(scheduled_24h)} contenu(s) trouvé(s)")

        for scheduled in scheduled_24h:
            # Récupérer l'utilisateur
            user = db.query(models.User).filter(models.User.id == scheduled.user_id).first()
            if not user:
                continue

            # Récupérer le contenu
            content = None
            content_preview = "Votre contenu planifié"

            if scheduled.generated_content_id:
                gen_content = db.query(models.GeneratedContent).filter(
                    models.GeneratedContent.id == scheduled.generated_content_id
                ).first()
                if gen_content:
                    content_preview = gen_content.polished_text

            # Formatter la date
            scheduled_date_str = scheduled.scheduled_date.strftime("%d/%m/%Y à %H:%M")

            # Envoyer l'email
            success = send_calendar_reminder(
                to_email=user.email,
                user_name=user.name or "utilisateur",
                content_preview=content_preview,
                platform=scheduled.platform,
                scheduled_date=scheduled_date_str,
                time_before="24h"
            )

            if success:
                scheduled.reminder_24h_sent = True
                scheduled.reminder_24h_sent_at = now
                db.commit()
                print(f"  ✅ Rappel 24h envoyé à {user.email}")

        # Trouver les contenus nécessitant un rappel 1h
        reminder_1h_time = now + timedelta(hours=1)
        # Tolérance de ±5 minutes pour le rappel 1h
        scheduled_1h = db.query(models.ScheduledContent).filter(
            models.ScheduledContent.status == "scheduled",
            models.ScheduledContent.reminder_1h_sent == False,
            models.ScheduledContent.scheduled_date >= reminder_1h_time - timedelta(minutes=5),
            models.ScheduledContent.scheduled_date <= reminder_1h_time + timedelta(minutes=5)
        ).all()

        print(f"\n⏰ Vérification des rappels 1h: {len(scheduled_1h)} contenu(s) trouvé(s)")

        for scheduled in scheduled_1h:
            # Récupérer l'utilisateur
            user = db.query(models.User).filter(models.User.id == scheduled.user_id).first()
            if not user:
                continue

            # Récupérer le contenu
            content_preview = "Votre contenu planifié"

            if scheduled.generated_content_id:
                gen_content = db.query(models.GeneratedContent).filter(
                    models.GeneratedContent.id == scheduled.generated_content_id
                ).first()
                if gen_content:
                    content_preview = gen_content.polished_text

            # Formatter la date
            scheduled_date_str = scheduled.scheduled_date.strftime("%d/%m/%Y à %H:%M")

            # Envoyer l'email
            success = send_calendar_reminder(
                to_email=user.email,
                user_name=user.name or "utilisateur",
                content_preview=content_preview,
                platform=scheduled.platform,
                scheduled_date=scheduled_date_str,
                time_before="1h"
            )

            if success:
                scheduled.reminder_1h_sent = True
                scheduled.reminder_1h_sent_at = now
                db.commit()
                print(f"  ✅ Rappel 1h envoyé à {user.email}")

        print(f"\n✨ Vérification terminée à {now.strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi des rappels: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    print("="*60)
    print("🔔 Démarrage du script d'envoi de rappels calendrier")
    print("="*60)
    send_reminders()
