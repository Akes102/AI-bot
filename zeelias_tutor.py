"""
create a tutor assistant for my daughter

"""


import os
import threading
from dotenv import load_dotenv
from google import genai
import customtkinter as ctk

# -----------------------
# Setup
# -----------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found. Put it in .env")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3-flash-preview"  # switch to "gemini-2.0-flash" if preview ever fails

ROLE = (
    "You a grade 8 Tutor, a helpful assistant for Zeelia.\n"
    "Be clear, practical, and slightly funny.\n"
    "you will address her as Zeelia Rose.\n"
    "always greet her in your first response and include the timer.\n"
    "You will strictly help with home work nothing more noting less.\n"
    "if she tries to use you in any other way, tell her that dad said no.\n"
    "try to make her learning fun.\n"
    "she relates to anime and gatcha games and roblox-u may refer to these sometimes to ease her up.\n"
    "keep track of her time spent and remind her evry 20min how much time she has left of 1.5 hours to use you-end her time if she exceeds this limit.\n"
    "you are only to help her improve not give her freebies.\n"
    "if she struggles more than a few minutes on a task, you may help her\n"
    "Keep replies short unless she ask for detail."
    
)

# Create a chat session so Evo remembers the conversation
chat = client.chats.create(model=MODEL)

# -----------------------
# GUI
# -----------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Evo Mini Chat")
app.geometry("900x600")

app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1)

chat_box = ctk.CTkTextbox(app, wrap="word")
chat_box.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
chat_box.configure(state="disabled")

bottom = ctk.CTkFrame(app)
bottom.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")
bottom.grid_columnconfigure(0, weight=1)

entry = ctk.CTkEntry(bottom, placeholder_text="Type a message...")
entry.grid(row=0, column=0, padx=(8, 8), pady=8, sticky="ew")

send_btn = ctk.CTkButton(bottom, text="Send")
send_btn.grid(row=0, column=1, padx=(0, 8), pady=8)

status_var = ctk.StringVar(value="Ready")
status = ctk.CTkLabel(app, textvariable=status_var)
status.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="w")


def add_line(text: str):
    chat_box.configure(state="normal")
    chat_box.insert("end", text + "\n")
    chat_box.see("end")
    chat_box.configure(state="disabled")


def set_status(text: str):
    status_var.set(text)


def reset_chat():
    global chat
    chat = client.chats.create(model=MODEL)
    add_line("System: New chat started (memory reset).")


def send_message():
    user_text = entry.get().strip()
    if not user_text:
        return

    # Commands
    if user_text.lower() == "/clear":
        entry.delete(0, "end")
        chat_box.configure(state="normal")
        chat_box.delete("1.0", "end")
        chat_box.configure(state="disabled")
        add_line("System: Chat cleared (view only).")
        return

    if user_text.lower() == "/new":
        entry.delete(0, "end")
        reset_chat()
        return

    # Show user message
    add_line(f"You: {user_text}")
    entry.delete(0, "end")

    # Disable button while thinking
    send_btn.configure(state="disabled")
    set_status("Thinking...")

    def worker():
        try:
            prompt = f"ROLE:\n{ROLE}\n\nUSER:\n{user_text}"
            resp = chat.send_message(prompt)
            reply = resp.text.strip() if resp.text else "(no response)"
        except Exception as e:
            reply = f"Error: {e}"

        # Update UI back on main thread
        app.after(0, lambda: add_line(f"Evo: {reply}\n"))
        app.after(0, lambda: send_btn.configure(state="normal"))
        app.after(0, lambda: set_status("Ready"))

    threading.Thread(target=worker, daemon=True).start()


send_btn.configure(command=send_message)
entry.bind("<Return>", lambda e: send_message())

add_line("System: Evo Mini Chat ready.")
add_line("System: Commands: /new (reset memory), /clear (clear view)")
app.mainloop()


print(response.output_text)


