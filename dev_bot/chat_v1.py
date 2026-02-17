"""
im adding a token limit here but its not 
neccassary with gemini as it will use the least tokens
by default
also adding a temperature for response level

"""

from dotenv import load_dotenv
load_dotenv()

import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain Gemini API in simple terms",
    config={
        "max_output_tokens": 150,
        "temperature": 0.7
    }
)

print(response.text)
