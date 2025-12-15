import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"Clé OpenAI trouvée : {api_key[:20]}..." if api_key else "❌ Aucune clé trouvée")

try:
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Dis bonjour en une phrase"}
        ],
        max_tokens=50
    )
    
    print(f"✅ Succès ! Réponse de l'IA : {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ Erreur : {e}")