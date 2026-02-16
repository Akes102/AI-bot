"""
EVO_v6 – Persistent Settings

Stores user preferences like mode and custom role in a settings.json file so they persist across program restarts.

Concepts used: JSON serialization, configuration files, persistent state.

"""


from openai import OpenAI
import os
import json
import datetime

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

SETTINGS_FILE = "settings.json"

MODES = {
    "chat": "You are a helpful assistant. Keep replies short, clear, and friendly.",
    "tutor": "You are a Python tutor. Explain simply and give small examples.",
    "helpdesk": "You are an IT helpdesk assistant. Ask 1 question if needed, then give step-by-step fixes.",
    "study": "You are a study coach. Summarize clearly and ask one quick follow-up question.",
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"mode": "chat", "custom_role": ""}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"mode": "chat", "custom_role": ""}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

settings = load_settings()
mode = settings.get("mode", "chat")
custom_role = settings.get("custom_role", "")

system_prompt = custom_role if custom_role else MODES.get(mode, MODES["chat"])
messages = [{"role": "system", "content": system_prompt}]

os.makedirs("logs", exist_ok=True)
log_name = datetime.datetime.now().strftime("logs/chat_%Y%m%d_%H%M%S.txt")

def log_line(line: str):
    with open(log_name, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def show_help():
    print("Commands:")
    print("  /help /clear /mode /role /showsettings /exit")

print("Evo Bot v6 running. Logging to:", log_name)
print("Mode:", mode, "| Custom role:", "yes" if custom_role else "no")
print("Type /help for commands.\n")

while True:
    user_text = input("You: ").strip()

    if user_text.lower() in ("exit", "/exit"):
        print("Bye!")
        break

    if user_text == "/help":
        show_help()
        print("Modes:", ", ".join(MODES.keys()))
        continue

    if user_text == "/showsettings":
        print(json.dumps(settings, indent=2))
        continue

    if user_text == "/clear":
        messages[:] = messages[:1]
        print("Cleared memory.")
        continue

    if user_text == "/mode":
        new_mode = input(f"Choose mode {list(MODES.keys())}: ").strip().lower()
        if new_mode in MODES:
            mode = new_mode
            settings["mode"] = mode
            settings["custom_role"] = ""
            save_settings(settings)
            messages[0]["content"] = MODES[mode]
            print("Mode set to:", mode)
        else:
            print("Unknown mode.")
        continue

    if user_text == "/role":
        new_role = input("New role (blank to remove): ").strip()
        settings["custom_role"] = new_role
        save_settings(settings)
        messages[0]["content"] = new_role if new_role else MODES.get(mode, MODES["chat"])
        print("Role updated.")
        continue

    if not user_text:
        print("Type something.")
        continue

    messages.append({"role": "user", "content": user_text})
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply = resp.choices[0].message.content
    print("AI:", reply)
    messages.append({"role": "assistant", "content": reply})
