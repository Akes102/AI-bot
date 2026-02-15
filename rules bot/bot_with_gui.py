# gemini_v8_gui.py
# Tkinter GUI chatbot using the NEW Gemini SDK with memory.

import os
import tkinter as tk
from tkinter import scrolledtext
from google import genai

# Block: check API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

# Block: create client and select model
client = genai.Client(api_key=api_key)
MODEL = "models/gemini-flash-latest"

# Block: create chat session (memory)
chat = client.chats.create(model=MODEL)

# Block: role instruction (controls bot behavior)
ROLE = "You are a helpful assistant. Keep replies short and clear."

def reset_chat():
    # Block: recreate chat object to clear memory
    global chat
    chat = client.chats.create(model=MODEL)

def send_message():
    # Block: get user input
    user_text = entry.get().strip()
    if not user_text:
        return

    # Block: clear command
    if user_text.lower() == "/clear":
        reset_chat()
        chat_box.delete("1.0", tk.END)
        chat_box.insert(tk.END, "Memory cleared.\n\n")
        entry.delete(0, tk.END)
        return

    # Block: show user message in UI
    chat_box.insert(tk.END, f"You: {user_text}\n")
    entry.delete(0, tk.END)

    # Block: add role instruction
    prompt = f"ROLE:\n{ROLE}\n\nUSER:\n{user_text}"

    # Block: call Gemini with error handling
    try:
        resp = chat.send_message(prompt)
        reply = resp.text
    except Exception:
        reply = "Error: request failed. Check your key or internet."

    # Block: show reply
    chat_box.insert(tk.END, f"Bot: {reply}\n\n")
    chat_box.see(tk.END)

def on_enter(event):
    # Block: Enter key sends message
    send_message()

# Block: build UI window
root = tk.Tk()
root.title("Evo assastant v8")

chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20)
chat_box.pack(padx=10, pady=10)

entry = tk.Entry(root, width=70)
entry.pack(padx=10, pady=(0, 10))
entry.bind("<Return>", on_enter)

btn = tk.Button(root, text="Send", command=send_message)
btn.pack(pady=(0, 10))

chat_box.insert(tk.END, "EVO GUI Bot v8 running.\nType /clear to reset memory.\n\n")

# Block: start GUI loop
root.mainloop()
