import os
from typing import Optional
import resend

# Configuration Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")

# Initialiser Resend avec la clé API
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

def send_verification_email(to_email: str, verification_code: str, user_name: Optional[str] = None) -> bool:
    """Envoie un email de vérification avec le code à 6 chiffres via Resend"""

    # Si pas de configuration Resend, afficher le code dans la console (mode développement)
    if not RESEND_API_KEY:
        print(f"\n{'='*50}")
        print(f"MODE DÉVELOPPEMENT - CODE DE VÉRIFICATION")
        print(f"{'='*50}")
        print(f"Email: {to_email}")
        print(f"Code de vérification: {verification_code}")
        print(f"{'='*50}\n")
        return True

    # En mode test Resend (sans domaine vérifié), on ne peut envoyer qu'à mathdu0609@gmail.com
    # Pour les autres emails, afficher le code en console
    VERIFIED_EMAIL = "mathdu0609@gmail.com"
    if to_email.lower() != VERIFIED_EMAIL.lower():
        print(f"\n{'='*50}")
        print(f"MODE TEST - CODE DE VÉRIFICATION")
        print(f"{'='*50}")
        print(f"Email: {to_email}")
        print(f"Code de vérification: {verification_code}")
        print(f"Note: Pour recevoir de vrais emails, utilisez {VERIFIED_EMAIL}")
        print(f"ou configurez un domaine sur resend.com/domains")
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
        .button {{
            display: inline-block;
            padding: 14px 28px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin: 20px 0;
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
            <p>© {2025} AI Content Polisher - Tous droits réservés</p>
            <p style="margin-top: 15px; font-size: 11px;">
                Cet email a été envoyé à {to_email}
            </p>
        </div>
    </div>
</body>
</html>
        """

        # Envoyer l'email via Resend
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Code de vérification - AI Content Polisher",
            "html": html_content,
        }

        response = resend.Emails.send(params)
        print(f"✅ Email de vérification envoyé à {to_email} (ID: {response.get('id', 'N/A')})")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email via Resend: {e}")
        # En mode développement, afficher quand même le code
        print(f"\n{'='*50}")
        print(f"CODE DE VÉRIFICATION (envoi échoué)")
        print(f"{'='*50}")
        print(f"Email: {to_email}")
        print(f"Code: {verification_code}")
        print(f"{'='*50}\n")
        return False
