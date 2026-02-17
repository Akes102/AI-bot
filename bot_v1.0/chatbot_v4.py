""" 
EVO_v4 – Multi-Mode AI Assistant

Introduces multiple operating modes (tutor, helpdesk, study, interview) that change how the AI responds based on selected context.

Concepts used: dictionaries, configuration logic, prompt engineering.
"""



from openai import OpenAI
import os
import datetime

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

MODES = {
    "chat": "You are a helpful assistant. Keep replies short, clear, and friendly.",
    "tutor": "You are a Python tutor. Explain simply and give small examples.",
    "helpdesk": "You are an IT helpdesk assistant. Ask 1 question if needed, then give step-by-step fixes.",
    "study": "You are a study coach. Summarize clearly and ask one quick follow-up question.",
    "interview": "You are an interviewer for a junior IT role. Ask one question at a time, give feedback."
}

mode = "chat"
messages = [{"role": "system", "content": MODES[mode]}]

os.makedirs("logs", exist_ok=True)
log_name = datetime.datetime.now().strftime("logs/chat_%Y%m%d_%H%M%S.txt")

def log_line(line: str):
    with open(log_name, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def show_help():
    print("Commands:")
    print("  /help")
    print("  /clear")
    print("  /mode")
    print("  /role")
    print("  /exit")

print("Evo Bot v4 running. Logging to:", log_name)
print("Mode:", mode)
print("Type /help for commands.\n")

log_line("=== New Session ===")
log_line("MODE: " + mode)
log_line("SYSTEM: " + messages[0]["content"])

while True:
    user_text = input("You: ").strip()

    if user_text.lower() in ("exit", "/exit"):
        print("Bye!")
        log_line("SESSION ENDED")
        break

    if user_text == "/help":
        show_help()
        print("Modes:", ", ".join(MODES.keys()))
        continue

    if user_text == "/clear":
        messages[:] = messages[:1]
        print("Cleared memory.")
        log_line("MEMORY CLEARED")
        continue

    if user_text == "/mode":
        new_mode = input(f"Choose mode {list(MODES.keys())}: ").strip().lower()
        if new_mode in MODES:
            mode = new_mode
            messages[0]["content"] = MODES[mode]
            print("Mode set to:", mode)
            log_line("MODE SET: " + mode)
            log_line("SYSTEM: " + messages[0]["content"])
        else:
            print("Unknown mode.")
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
