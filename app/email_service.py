import os
from typing import Optional
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

# Configuration Brevo (API)
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "contact@aicontentpolisher.com")
FROM_NAME = os.getenv("FROM_NAME", "AI Content Polisher")

# Configuration du client API Brevo
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = BREVO_API_KEY

def send_verification_email(to_email: str, verification_code: str, user_name: Optional[str] = None) -> bool:
    """Envoie un email de vérification avec le code à 6 chiffres via l'API Brevo"""

    # Si pas de clé API, afficher le code dans la console (mode développement)
    if not BREVO_API_KEY:
        print(f"\n{'='*50}")
        print(f"MODE DÉVELOPPEMENT - CODE DE VÉRIFICATION")
        print(f"{'='*50}")
        print(f"Email: {to_email}")
        print(f"Code de vérification: {verification_code}")
        print(f"{'='*50}\n")
        return True

    try:
        # Version HTML de l'email
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            background: #ffffff;
            padding: 40px 30px;
        }}
        .content p {{
            margin: 0 0 20px 0;
            color: #555;
        }}
        .code-box {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
            border: 2px solid #667eea;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            margin: 30px 0;
        }}
        .code {{
            font-size: 42px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 12px;
            font-family: 'Courier New', monospace;
        }}
        .code-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .expiry {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 15px;
        }}
        .footer {{
            background: #f9fafb;
            text-align: center;
            padding: 30px;
            color: #999;
            font-size: 13px;
            border-top: 1px solid #e5e7eb;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        .security-note {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✨ AI Content Polisher</h1>
            <p>Vérifiez votre adresse email</p>
        </div>
        <div class="content">
            <p>Bonjour{' <strong>' + user_name + '</strong>' if user_name else ''},</p>
            <p>Bienvenue sur AI Content Polisher ! Nous sommes ravis de vous compter parmi nous.</p>
            <p>Pour activer votre compte, veuillez entrer le code de vérification suivant :</p>

            <div class="code-box">
                <div class="code-label">Votre code de vérification</div>
                <div class="code">{verification_code}</div>
                <div class="expiry">⏱️ Ce code expire dans <strong>15 minutes</strong></div>
            </div>

            <div class="security-note">
                🔒 <strong>Conseil de sécurité :</strong> Ne partagez jamais ce code avec qui que ce soit. Notre équipe ne vous demandera jamais ce code.
            </div>

            <p style="margin-top: 30px;">Si vous n'avez pas créé de compte sur AI Content Polisher, vous pouvez ignorer cet email en toute sécurité.</p>
        </div>
        <div class="footer">
            <p><strong>AI Content Polisher</strong></p>
            <p>© 2025 AI Content Polisher - Tous droits réservés</p>
            <p style="margin-top: 15px; font-size: 11px;">
                Cet email a été envoyé à {to_email}
            </p>
        </div>
    </div>
</body>
</html>
        """

        # Créer l'instance API
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        # Créer l'objet email
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={"name": FROM_NAME, "email": FROM_EMAIL},
            subject="Code de vérification - AI Content Polisher",
            html_content=html_content
        )

        # Envoyer l'email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"✅ Email de vérification envoyé à {to_email} via API Brevo (ID: {api_response.message_id})")
        return True

    except ApiException as e:
        print(f"❌ Erreur API Brevo lors de l'envoi de l'email: {e}")
        # En mode développement, afficher quand même le code
        print(f"\n{'='*50}")
        print(f"CODE DE VÉRIFICATION (envoi échoué)")
        print(f"{'='*50}")
        print(f"Email: {to_email}")
        print(f"Code: {verification_code}")
        print(f"{'='*50}\n")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email: {e}")
        print(f"\n{'='*50}")
        print(f"CODE DE VÉRIFICATION (envoi échoué)")
        print(f"{'='*50}")
        print(f"Email: {to_email}")
        print(f"Code: {verification_code}")
        print(f"{'='*50}\n")
        return False

def send_calendar_reminder(to_email: str, user_name: str, content_preview: str, platform: str, scheduled_date: str, time_before: str) -> bool:
    """Envoie un rappel par email pour un contenu planifié"""

    # Si pas de clé API, afficher dans la console
    if not BREVO_API_KEY:
        print(f"\n{'='*50}")
        print(f"MODE DÉVELOPPEMENT - RAPPEL CALENDRIER")
        print(f"{'='*50}")
        print(f"Email: {to_email}")
        print(f"Rappel: Publication {time_before} sur {platform}")
        print(f"Date: {scheduled_date}")
        print(f"{'='*50}\n")
        return True

    try:
        # Déterminer le titre en fonction du délai
        if time_before == "24h":
            subject = "📅 Rappel : Contenu à publier demain"
            time_text = "dans 24 heures"
        else:
            subject = "⏰ Rappel : Contenu à publier dans 1 heure"
            time_text = "dans 1 heure"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 16px;
            opacity: 0.9;
        }}
        .content {{
            background: #ffffff;
            padding: 40px 30px;
        }}
        .content p {{
            margin: 0 0 20px 0;
            color: #555;
        }}
        .reminder-box {{
            background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
            border: 2px solid #f56565;
            border-radius: 12px;
            padding: 25px;
            margin: 30px 0;
        }}
        .reminder-time {{
            font-size: 24px;
            font-weight: bold;
            color: #c53030;
            text-align: center;
            margin-bottom: 15px;
        }}
        .platform-badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            text-transform: uppercase;
            margin: 10px 0;
        }}
        .content-preview {{
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
            font-style: italic;
            color: #2d3748;
        }}
        .footer {{
            background: #f9fafb;
            text-align: center;
            padding: 30px;
            color: #999;
            font-size: 13px;
            border-top: 1px solid #e5e7eb;
        }}
        .footer p {{
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 Rappel de Publication</h1>
            <p>N'oubliez pas de publier votre contenu!</p>
        </div>
        <div class="content">
            <p>Bonjour <strong>{user_name}</strong>,</p>
            <p>Ceci est un rappel concernant votre contenu planifié.</p>

            <div class="reminder-box">
                <div class="reminder-time">⏰ À publier {time_text}</div>
                <p style="text-align: center; margin: 0;">
                    <span class="platform-badge">{platform}</span>
                </p>
                <p style="text-align: center; margin-top: 10px; color: #666;">
                    📆 {scheduled_date}
                </p>
            </div>

            <p><strong>Aperçu de votre contenu:</strong></p>
            <div class="content-preview">
                {content_preview[:200]}{"..." if len(content_preview) > 200 else ""}
            </div>

            <p style="margin-top: 30px;">Connectez-vous à AI Content Polisher pour accéder à votre contenu complet et le publier sur {platform}.</p>

            <p style="text-align: center; margin-top: 30px;">
                <a href="https://aicontentpolisher.com" style="display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600;">
                    Voir mon contenu
                </a>
            </p>
        </div>
        <div class="footer">
            <p><strong>AI Content Polisher</strong></p>
            <p>© 2025 AI Content Polisher - Tous droits réservés</p>
            <p style="margin-top: 15px; font-size: 11px;">
                Cet email a été envoyé à {to_email}
            </p>
        </div>
    </div>
</body>
</html>
        """

        # Créer l'instance API
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        # Créer l'objet email
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={"name": FROM_NAME, "email": FROM_EMAIL},
            subject=subject,
            html_content=html_content
        )

        # Envoyer l'email
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"✅ Rappel calendrier envoyé à {to_email} via API Brevo ({time_before} avant, ID: {api_response.message_id})")
        return True

    except ApiException as e:
        print(f"❌ Erreur API Brevo lors de l'envoi du rappel: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du rappel: {e}")
        return False
