# gemini_v4_code_explainer.py
# Explains Python code line-by-line for beginners.

import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)
MODEL = "models/gemini-flash-latest"

# Block: read code
code = input("Paste Python code:\n").strip()
if not code:
    raise RuntimeError("No code provided.")

# Block: prompt with structure rules
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
