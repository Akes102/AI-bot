"""
WELCOME TO EVO , distant cousin of OpenAi

"""

from openai import OpenAI
import os

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

SYSTEM_PROMPT = "You are a helpful assistant. Keep replies short, clear, and friendly."

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

print("Welcome to Evo assistant bot. Type 'exit' to quit.\n")

while True:
    user_text = input("You: ").strip()
    if user_text.lower() == "exit":
        print("Bye!")
        break
    if not user_text:
        print("Type something.")
        continue

    messages.append({"role": "user", "content": user_text})

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = resp.choices[0].message.content
    print("AI:", reply)
    messages.append({"role": "assistant", "content": reply})
