# gemini_v1_chat_newsdk.py
# Gemini CLI chatbot using the NEW Google Gen AI SDK: google-genai (import google.genai)
# Uses a model that your account already has: models/gemini-flash-latest

# Block: read environment variables
import os

# Block: import the NEW SDK client
from google import genai

# Block: check API key exists
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set. Set it in PowerShell first.")

# Block: create a client for the Gemini Developer API (API key auth)
client = genai.Client(api_key=api_key)

# Block: choose a model that exists on your account (from your ListModels output)
MODEL = "models/gemini-flash-latest"
print("-"*30)
print("Welcome to EVO v1. Type 'exit' to quit.\n")
print("-"*30)

# Block: main chat loop
while True:
    user_text = input("You: ").strip()

    # Block: exit condition
    if user_text.lower() == "exit":
        print("Bye for now, Come back to Evo soon...!")
        break

    # Block: basic validation
    if not user_text:
        print("Type something...")
        continue

    # Block: call Gemini generateContent
    response = client.models.generate_content(
        model=MODEL,
        contents=user_text
    )

    # Block: print the model output
    print("EVO:", response.text)
