import os, requests
from dotenv import load_dotenv

load_dotenv('/workspace/Sigvaldi-/.env')
key = os.getenv('OPENROUTER_API_KEY')

print(f"Notum lykil sem byrjar á: {key[:12]}...")

try:
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "HTTP-Referer": "https://alvitur.is"},
        json={"model": "mistralai/mixtral-8x7b-instruct", "messages": [{"role": "user", "content": "Halló"}]}
    )
    print(f"Staða frá OR: {resp.status_code}")
    print(f"Svar: {resp.text[:300]}")
except Exception as e:
    print(f"Python Villa: {e}")
