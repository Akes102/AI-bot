# gemini_v6_helpdesk_bot.py
# IT helpdesk assistant that asks one clarifying question if needed,
# then gives step-by-step troubleshooting.

import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)
MODEL = "models/gemini-flash-latest"

print("Gemini Helpdesk Bot (v6). Type 'exit' to quit.\n")

while True:
    # Block: get user issue
    issue = input("Issue: ").strip()

    # Block: exit condition
    if issue.lower() == "exit":
        print("Bye!")
        break

    # Block: validate
    if not issue:
        print("Describe the issue.")
        continue

    # Block: prompt rules
    prompt = f"""
You are an IT helpdesk assistant.

Output format:
1) Ask exactly ONE clarifying question if needed.
2) Then give step-by-step troubleshooting.
3) End with: "If that fails, paste the full error text."

Issue:
{issue}
"""

    # Block: call Gemini
    resp = client.models.generate_content(model=MODEL, contents=prompt)

    # Block: output
    print("\nFix:\n")
    print(resp.text)
