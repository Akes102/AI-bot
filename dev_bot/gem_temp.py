from dotenv import load_dotenv
load_dotenv()

from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


resp = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Hello gemini, what is the weather in cape town south africa today" #promt here
)

print(resp.text)
