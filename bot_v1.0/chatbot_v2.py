"""
Evo_v2 – Command-Enabled Chatbot

Adds user commands such as /help, /clear, and /role, allowing interaction with the chatbot’s behavior instead of only chatting.

Concepts used: command parsing, functions, state management.

"""

from openai import OpenAI
import os

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

DEFAULT_ROLE = "You are a helpful assistant. Keep replies short, clear, and friendly."
messages = [{"role": "system", "content": DEFAULT_ROLE}]

def show_help():
    print("Commands:")
    print("  /help         Show commands")
    print("  /clear        Clear conversation memory")
    print("  /role         Change assistant role (system prompt)")
    print("  /exit         Quit")

print("Hi there, Welcome to Evo v2 Type /help for commands.\n")

while True:
    user_text = input("You: ").strip()

    if user_text.lower() in ("exit", "/exit"):
        print("Bye!")
        break

    if user_text == "/help":
        show_help()
        continue

    if user_text == "/clear":
        messages[:] = messages[:1]
        print("Cleared memory.")
        continue

    if user_text == "/role":
        new_role = input("New role: ").strip()
        if new_role:
            messages[0]["content"] = new_role
            print("Role updated.")
        else:
            print("Role unchanged.")
        continue

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
