# gemini_v3_summarizer.py
# Summarizes any text into beginner-friendly bullet points.

import os
from google import genai

# Block: read and verify API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

# Block: create client + choose model
client = genai.Client(api_key=api_key)
MODEL = "models/gemini-flash-latest"

# Block: read input text
text = input("Paste text to summarize:\n\n").strip()
if not text:
    raise RuntimeError("No text provided.")

# Block: build instruction prompt
prompt = (
    "Summarize the text for a beginner.\n"
    "Rules:\n"
    "- Max 6 bullet points\n"
    "- Simple wording\n"
    "- Add 1 short example if helpful\n\n"
    f"TEXT:\n{text}"
)

# Block: call Gemini
resp = client.models.generate_content(model=MODEL, contents=prompt)

# Block: print result
print("\nSummary:\n")
print(resp.text)
