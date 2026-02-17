"""
EVO_v7 – Session Save and Load

Allows users to save and reload entire conversation sessions, making it possible to resume previous chats.

Concepts used: data serialization, file management, list manipulation.

"""



from openai import OpenAI
import os
import json
import datetime

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

SESS_DIR = "sessions"
os.makedirs(SESS_DIR, exist_ok=True)

DEFAULT_ROLE = "You are a helpful assistant. Keep replies short, clear, and friendly."
messages = [{"role": "system", "content": DEFAULT_ROLE}]

def show_help():
    print("Commands:")
    print("  /help /clear /save /load /list /exit")

def session_path(name: str) -> str:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in ("_", "-")).strip()
    if not safe:
        safe = "session"
    return os.path.join(SESS_DIR, safe + ".json")

def save_session(name: str):
    path = session_path(name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2)
    print("Saved:", path)

def load_session(name: str):
    path = session_path(name)
    if not os.path.exists(path):
        print("No such session:", path)
        return
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    if not isinstance(loaded, list) or not loaded:
        print("Invalid session file.")
        return
    messages[:] = loaded
    print("Loaded:", path)

def list_sessions():
    files = [f for f in os.listdir(SESS_DIR) if f.endswith(".json")]
    if not files:
        print("No saved sessions.")
        return
    for f in files:
        print(" ", f)

print("Evo Bot v7 running. Type /help for commands.\n")

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

    if user_text.startswith("/save"):
        name = user_text.replace("/save", "", 1).strip() or input("Session name: ").strip()
        save_session(name)
        continue

    if user_text.startswith("/load"):
        name = user_text.replace("/load", "", 1).strip() or input("Session name: ").strip()
        load_session(name)
        continue

    if user_text == "/list":
        list_sessions()
        continue

    if not user_text:
        print("Type something.")
        continue

    messages.append({"role": "user", "content": user_text})
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply = resp.choices[0].message.content
    print("AI:", reply)
    messages.append({"role": "assistant", "content": reply})
