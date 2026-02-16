import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)
MODEL = "gemini-2.0-flash"

code = input("Paste Python code:\n").strip()
if not code:
    raise RuntimeError("No code provided.")

prompt = (
    "Explain this Python code line by line for a beginner.\n"
    "Also include:\n"
    "- What the program is trying to do\n"
    "- 2 common beginner mistakes with similar code\n\n"
    f"CODE:\n{code}"
)

resp = client.models.generate_content(model=MODEL, contents=prompt)

print("\nExplanation:\n")
print(resp.text)
