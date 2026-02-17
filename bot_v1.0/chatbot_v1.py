""" 
EVO

A basic AI chatbot that accepts user input, sends it to the OpenAI API, and returns responses while keeping conversation memory during a single session.

Concepts used: API calls, loops, conditionals, lists, environment variables.

"""


from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import os

# 1) Check API key early
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set. Set it in PowerShell before running.")

# 2) Create client
client = OpenAI()

# 3) System role (bot personality)
SYSTEM_PROMPT = "You are a helpful assistant. Keep replies short, clear, and friendly."

# 4) Conversation memory
messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

print("AI Bot running. Type 'exit' to quit.\n")

while True:
    user_text = input("You: ").strip()

    if user_text.lower() == "exit":
        print("Bye!")
        break

    if not user_text:
        print("Type something.")
        continue

    # Add user message
    messages.append({"role": "user", "content": user_text})

    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = response.choices[0].message.content
    print("AI:", reply)

    # Add assistant message (memory)
    messages.append({"role": "assistant", "content": reply})
