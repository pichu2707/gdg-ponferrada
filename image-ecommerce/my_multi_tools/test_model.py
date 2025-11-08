import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # ← cargar .env

api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key presente: {bool(api_key)}")

if not api_key:
    print("✗ GOOGLE_API_KEY no está en .env")
else:
    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents="ping")
        print(f"✓ OK con API: {resp.text[:50]}")
    except Exception as e:
        print(f"✗ FAIL: {e}")