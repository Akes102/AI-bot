# rule_bot_v1.py
# Rule-Based Chatbot (No API)
# Features:
# - keyword detection
# - simple memory (name + mood)
# - mini helpdesk troubleshooting
# - /help commands

import re

memory = {
    "name": None,
    "mood": None,
}

def show_help():
    print("\nCommands:")
    print("  /help    show commands")
    print("  /clear   clear memory")
    print("  /exit    quit")
    print("\nTry saying:")
    print("  'my name is Arnold'")
    print("  'i feel stressed'")
    print("  'python list vs tuple'")
    print("  'pip not recognized'")
    print()

def clear_memory():
    memory["name"] = None
    memory["mood"] = None

def extract_name(text: str):
    # Matches: "my name is Arnold" or "i am Arnold"
    m = re.search(r"\b(my name is|i am)\s+([a-zA-Z]+)\b", text, re.IGNORECASE)
    if m:
        return m.group(2)
    return None

def extract_mood(text: str):
    moods = ["happy", "sad", "stressed", "tired", "angry", "excited", "okay", "fine"]
    for mood in moods:
        if re.search(rf"\b{mood}\b", text, re.IGNORECASE):
            return mood
    return None

def respond(text: str) -> str:
    t = text.lower().strip()

    # 1) Commands
    if t == "/help":
        show_help()
        return "Done."
    if t == "/clear":
        clear_memory()
        return "Memory cleared."
    if t in ("/exit", "exit", "quit"):
        return "__EXIT__"

    # 2) Save name
    name = extract_name(text)
    if name:
        memory["name"] = name
        return f"Nice to meet you, {name}. What do you want to talk about?"

    # 3) Save mood
    mood = extract_mood(text)
    if mood:
        memory["mood"] = mood
        who = memory["name"] or "friend"
        if mood in ("stressed", "tired", "sad", "angry"):
            return f"I hear you, {who}. Want a quick plan to handle it, or do you just want to vent?"
        return f"Nice, {who}. What’s making you feel {mood}?"

    # 4) Personalized small talk
    if "how are you" in t or "how r u" in t:
        who = memory["name"] or "there"
        mood_part = f" You said you feel {memory['mood']} earlier." if memory["mood"] else ""
        return f"I’m good, {who}.{mood_part} What’s up?"

    # 5) Python help rules
    if "list" in t and "tuple" in t:
        return (
            "List vs Tuple:\n"
            "- List: mutable (you can change it), uses [ ]\n"
            "- Tuple: immutable (can’t change), uses ( )\n"
            "Example:\n"
            "  nums = [1,2,3]  # can append\n"
            "  coords = (1,2)  # fixed\n"
        )

    if "function" in t and ("how" in t or "explain" in t):
        return (
            "Functions in Python (simple):\n"
            "1) Define it with def\n"
            "2) Call it by using ()\n"
            "Example:\n"
            "  def add(a,b):\n"
            "      return a+b\n"
            "  print(add(2,3))\n"
        )

    if "loop" in t and ("for" in t or "while" in t):
        return (
            "Loops quick guide:\n"
            "- for: when you know what to loop over\n"
            "- while: when you loop until something changes\n"
            "Example:\n"
            "  for i in range(3):\n"
            "      print(i)\n"
        )

    # 6) Helpdesk rules (based on your real errors)
    if "pip" in t and ("not recognized" in t or "not recognised" in t):
        return (
            "Fix: 'pip is not recognized' (Windows)\n"
            "Try:\n"
            "  python -m pip install openai\n"
            "If python is not recognized, reinstall Python and tick 'Add Python to PATH'."
        )

    if "permission denied" in t:
        return (
            "Permission denied usually means:\n"
            "- you need admin rights, or\n"
            "- wrong folder permissions, or\n"
            "- you’re trying to run a file without permission.\n"
            "Tell me what command you ran and I’ll match the fix."
        )

    if "api key" in t or "openai key" in t:
        return (
            "Rule: never hardcode keys in code.\n"
            "Use environment variables instead:\n"
            "  $env:OPENAI_API_KEY='your_key'\n"
            "And add .env or settings files to .gitignore."
        )

    # 7) Default fallback
    who = memory["name"] or "friend"
    return (
        f"Okay {who}, I’m not sure I understood.\n"
        "Try one of these:\n"
        "- 'my name is ...'\n"
        "- 'python list vs tuple'\n"
        "- 'pip not recognized'\n"
        "- '/help'\n"
    )

def main():
    print("Rule Bot v1 (No API). Type /help. Type /exit to quit.\n")
    while True:
        user = input("You: ")
        reply = respond(user)
        if reply == "__EXIT__":
            print("Bot: Bye!")
            break
        print("Bot:", reply)

if __name__ == "__main__":
    main()
