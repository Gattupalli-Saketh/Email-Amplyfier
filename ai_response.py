# ai_response.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def generate_ai_greeting(name: str = "Friend", context: str = "") -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "Hello! Have a wonderful day! "

    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = f"""
    Write a warm, professional, and beautiful email greeting for someone named "{name}".
    Context: {context or "general business follow-up"}
    Make it sincere, positive, and under 4 sentences.
    """

    try:
        response = requests.post(
            url,
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
    except:
        pass  # fallback below

    return f"Dear {name},\n\nI hope this message finds you well and in great spirits! Wishing you a productive and joyful day ahead."