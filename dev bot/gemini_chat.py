import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

prompt = "Explain Gemini API in simple terms"

resp = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=prompt
)

print(resp.text)

import time
from google.api_core.exceptions import ResourceExhausted

for attempt in range(5):
    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        print(resp.text)
        break
    except ResourceExhausted as e:
        wait = 5 * (attempt + 1)
        print(f"Rate limited. Waiting {wait}s...")
        time.sleep(wait)
