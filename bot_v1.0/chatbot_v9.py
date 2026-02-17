"""
EVO_v9 – Document Question Answering

Enables loading a text file and asking questions strictly based on its contents, simulating a document-aware AI assistant.

Concepts used: file reading, contextual prompting, controlled information scope.

"""
from openai import OpenAI
import os

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

loaded_text = ""
loaded_name = ""

messages = [{"role": "system", "content": "You are a helpful assistant. Keep replies short, clear, and friendly."}]

def show_help():
    print("Commands:")
    print("  /help")
    print("  /loadfile path_to_txt")
    print("  /unloadfile")
    print("  /clear")
    print("  /exit")

def load_file(path: str):
    global loaded_text, loaded_name
    if not os.path.exists(path):
        print("File not found.")
        return
    with open(path, "r", encoding="utf-8") as f:
        loaded_text = f.read()
    loaded_name = os.path.basename(path)
    print("Loaded file:", loaded_name)

print("Welcome to EVO v9 running. Type /help for commands.\n")

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

    if user_text.startswith("/loadfile"):
        path = user_text.replace("/loadfile", "", 1).strip()
        if not path:
            path = input("Path to .txt file: ").strip()
        load_file(path)
        continue

    if user_text == "/unloadfile":
        loaded_text = ""
        loaded_name = ""
        print("Unloaded file.")
        continue

    if not user_text:
        print("Type something.")
        continue

    if loaded_text:
        context = f"Use this document as context (file: {loaded_name}):\n\n{loaded_text}\n\nUser question: {user_text}"
        msgs = [
            {"role": "system", "content": "Answer using only the provided document. If not found, say so."},
            {"role": "user", "content": context}
        ]
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
        reply = resp.choices[0].message.content
        print("AI:", reply)
        continue

    messages.append({"role": "user", "content": user_text})
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply = resp.choices[0].message.content
    print("AI:", reply)
    messages.append({"role": "assistant", "content": reply})
