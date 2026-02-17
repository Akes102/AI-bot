"""
EVO_v10 – Graphical User Interface (GUI)

Wraps the chatbot in a simple Tkinter interface, providing a window-based application instead of a terminal program.

Concepts used: GUI programming, event handling, user interface design.

"""



from openai import OpenAI
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

SYSTEM_PROMPT = "You are a helpful assistant. Keep replies short, clear, and friendly."
messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def send_message():
    user_text = entry.get().strip()
    if not user_text:
        return
    if user_text.lower() == "/clear":
        messages[:] = messages[:1]
        chat_box.delete("1.0", tk.END)
        chat_box.insert(tk.END, "Cleared memory.\n")
        entry.delete(0, tk.END)
        return

    chat_box.insert(tk.END, f"You: {user_text}\n")
    entry.delete(0, tk.END)

    messages.append({"role": "user", "content": user_text})

    try:
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        reply = resp.choices[0].message.content
    except Exception as e:
        reply = "Error: " + str(e)
        messages.pop()

    chat_box.insert(tk.END, f"AI: {reply}\n\n")
    chat_box.see(tk.END)

    if not reply.startswith("Error:"):
        messages.append({"role": "assistant", "content": reply})

def on_enter(event):
    send_message()

root = tk.Tk()
root.title("AI Bot v10")

chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20)
chat_box.pack(padx=10, pady=10)

entry = tk.Entry(root, width=70)
entry.pack(padx=10, pady=(0, 10))
entry.bind("<Return>", on_enter)

btn = tk.Button(root, text="Send", command=send_message)
btn.pack(pady=(0, 10))

chat_box.insert(tk.END, "EVO v10 GUI running.\nType /clear to reset memory.\n\n")

root.mainloop()
