"""
Evo v1 – Making a Request with a Function

Steps:
1. Load API key
2. Create Gemini client
3. Define a function that sends a prompt
4. Call the function
"""

import os
from dotenv import load_dotenv
from google import genai


# Load environment variables
load_dotenv()

# Get API key
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")


# Create Gemini client (once)
client = genai.Client(api_key=API_KEY)


def evo_ask(prompt: str) -> str:
    """
    Sends a prompt to Evo (Gemini) and returns the response text.
    """
    response = client.models.generate_content(
        model="gemini-3-flash-preview",  # or gemini-2.0-flash for stability
        contents=prompt,
        config={
            "max_output_tokens": 150,
            "temperature": 0.7
        }
    )

    return response.text


# ---- Run Evo v1 ----
if __name__ == "__main__":
    user_prompt = "Explain the Gemini API in simple terms"
    reply = evo_ask(user_prompt)
    print(reply)
