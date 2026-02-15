""" 
EVO v3 – Chat Logging

Extends the chatbot to automatically save conversations to timestamped log files for later review.

Concepts used: file handling, directories, timestamps, persistent data storage.

"""


from openai import OpenAI
import os
import datetime

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

DEFAULT_ROLE = "You are a helpful assistant. Keep replies short, clear, and friendly."
messages = [{"role": "system", "content": DEFAULT_ROLE}]

os.makedirs("logs", exist_ok=True)
log_name = datetime.datetime.now().strftime("logs/chat_%Y%m%d_%H%M%S.txt")

def log_line(line: str):
    with open(log_name, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def show_help():
    print("Commands: /help /clear /role /exit")

print("Welcome to Evo v3. Logging you in...:", log_name)
print("Type /help for commands.\n")

log_line("=== New Session ===")
log_line("SYSTEM: " + messages[0]["content"])

while True:
    user_text = input("You: ").strip()

    if user_text.lower() in ("exit", "/exit"):
        print("Bye!")
        log_line("SESSION ENDED")
        break

    if user_text == "/help":
        show_help()
        continue

    if user_text == "/clear":
        messages[:] = messages[:1]
        print("Cleared memory.")
        log_line("MEMORY CLEARED")
        continue

    if user_text == "/role":
        new_role = input("New role: ").strip()
        if new_role:
            messages[0]["content"] = new_role
            print("Role updated.")
            log_line("SYSTEM UPDATED: " + new_role)
        else:
            print("Role unchanged.")
        continue

    if not user_text:
        print("Type something.")
        continue

    log_line("YOU: " + user_text)
    messages.append({"role": "user", "content": user_text})

    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply = resp.choices[0].message.content

    print("AI:", reply)
    log_line("AI: " + reply)

    messages.append({"role": "assistant", "content": reply})
