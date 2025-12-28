# Configuration des Rappels de Calendrier

## Fonctionnalité

Le système envoie automatiquement 2 rappels par email aux utilisateurs pour leurs contenus planifiés:
- **24 heures avant** la publication
- **1 heure avant** la publication

## Configuration du Cron Job

### Sur Linux/Ubuntu (Production - Render)

1. **Ajouter un cron job sur votre serveur Render** (via un worker séparé):

Dans votre `render.yaml`, ajoutez un service de type `cron`:

```yaml
services:
  - type: cron
    name: calendar-reminders
    env: python
    schedule: "0 * * * *"  # Toutes les heures
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python app/send_calendar_reminders.py"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: ai_content_polisher_db
          property: connectionString
      - key: SMTP_HOST
        value: smtp-relay.brevo.com
      - key: SMTP_PORT
        value: 587
      - key: SMTP_USER
        sync: false
      - key: SMTP_PASSWORD
        sync: false
      - key: FROM_EMAIL
        value: mathdu0609@gmail.com
      - key: FROM_NAME
        value: AI Content Polisher
```

### Sur Linux/Ubuntu (Manuel)

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne (exécute toutes les heures)
0 * * * * cd /path/to/backend && /path/to/backend/.venv/bin/python app/send_calendar_reminders.py >> /var/log/calendar_reminders.log 2>&1
```

### Test Manuel

Pour tester le script manuellement:

```bash
cd /home/mathd/backend
source .venv/bin/activate
python app/send_calendar_reminders.py
```

## Comment ça marche

1. Le script s'exécute **toutes les heures**
2. Il vérifie tous les contenus planifiés dans la base de données
3. Pour chaque contenu:
   - **Si la publication est dans ~24h** et que le rappel 24h n'a pas été envoyé → envoie le rappel 24h
   - **Si la publication est dans ~1h** et que le rappel 1h n'a pas été envoyé → envoie le rappel 1h
4. Marque les rappels comme envoyés pour éviter les doublons

## Tolérance

- **Rappel 24h**: ±30 minutes de tolérance
- **Rappel 1h**: ±5 minutes de tolérance

Cela permet de s'assurer que les rappels sont envoyés même si le cron ne s'exécute pas exactement au bon moment.

## Logs

Les logs sont affichés dans la console et peuvent être redirigés vers un fichier avec:

```bash
python app/send_calendar_reminders.py >> calendar_reminders.log 2>&1
```

## Champs de Base de Données

La table `scheduled_contents` a été mise à jour avec ces champs:
- `reminder_24h_sent` (Boolean): Indique si le rappel 24h a été envoyé
- `reminder_1h_sent` (Boolean): Indique si le rappel 1h a été envoyé
- `reminder_24h_sent_at` (DateTime): Date/heure d'envoi du rappel 24h
- `reminder_1h_sent_at` (DateTime): Date/heure d'envoi du rappel 1h

## Variables d'Environnement Requises

Assurez-vous que ces variables sont configurées dans votre `.env`:

```env
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=9eea85001@smtp-brevo.com
SMTP_PASSWORD=xsmtpsib-...
FROM_EMAIL=mathdu0609@gmail.com
FROM_NAME=AI Content Polisher
```
