# gemini_v5_quiz_generator.py
# Generates a 5-question multiple-choice quiz with answers.

import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)
MODEL = "models/gemini-flash-latest"

# Block: read topic
topic = input("Quiz topic: ").strip()
if not topic:
    raise RuntimeError("No topic provided.")

# Block: prompt for consistent formatting
prompt = f"""
Create a beginner quiz about: {topic}

Rules:
- 5 multiple-choice questions
- Each question has A, B, C, D
- Show answers at the end
- Keep questions simple
"""

resp = client.models.generate_content(model=MODEL, contents=prompt)

print("\nQuiz:\n")
print(resp.text)
