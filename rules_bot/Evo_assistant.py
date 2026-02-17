# gemini_modern_gui.py
# Modern-looking GUI using CustomTkinter + Gemini (google.genai)
# Features:
# - sidebar controls
# - chat bubbles
# - status bar
# - model picker
# - save chat
# - responsive UI (threading)

import os
import threading
import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
from google import genai

# -----------------------------
# Block: API setup and defaults
# -----------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set. Set it in PowerShell before running.")

CLIENT = genai.Client(api_key=API_KEY)

MODEL_OPTIONS = [
    "models/gemini-flash-latest",
    "models/gemini-2.0-flash",
    "models/gemini-2.5-flash",
    "models/gemini-pro-latest",
]

DEFAULT_MODEL = "models/gemini-flash-latest"

DEFAULT_ROLE = "You are a helpful assistant. Keep replies short, clear, and friendly."

# -----------------------------
# Block: Chat state
# -----------------------------
chat = CLIENT.chats.create(model=DEFAULT_MODEL)
current_role = DEFAULT_ROLE

# -----------------------------
# Block: Logging (optional)
# -----------------------------
os.makedirs("logs", exist_ok=True)
log_file = os.path.join("logs", datetime.datetime.now().strftime("modern_gui_%Y%m%d_%H%M%S.txt"))

def log_line(line: str):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# -----------------------------
# Block: UI helpers
# -----------------------------
def safe_text(s: str) -> str:
    return (s or "").strip()

class ChatBubble(ctk.CTkFrame):
    # Chat bubble component (left for bot, right for user)
    def __init__(self, master, text: str, sender: str):
        super().__init__(master, corner_radius=14)
        self.sender = sender

        # Block: bubble colors by sender
        if sender == "user":
            self.configure(fg_color=("#2563eb", "#2563eb"))  # blue
            text_color = "#ffffff"
            anchor = "e"
        else:
            self.configure(fg_color=("#1f2937", "#111827"))  # gray
            text_color = "#e5e7eb"
            anchor = "w"

        self.label = ctk.CTkLabel(
            self,
            text=text,
            text_color=text_color,
            justify="left",
            anchor="w",
            wraplength=620,
            font=("Segoe UI", 12),
        )
        self.label.pack(padx=12, pady=10, fill="both", expand=True)

        # Block: alignment wrapper
        self.pack_propagate(False)
        self.update_idletasks()

        # bubble width control
        w = min(680, max(200, self.label.winfo_reqwidth() + 24))
        self.configure(width=w)

        # Position bubble
        if anchor == "e":
            self.pack(anchor="e", padx=14, pady=6)
        else:
            self.pack(anchor="w", padx=14, pady=6)

# -----------------------------
# Block: Main App
# -----------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Evo Assistant")
app.geometry("1100x700")
app.minsize(980, 640)

# Layout grid
app.grid_columnconfigure(0, weight=0)  # sidebar
app.grid_columnconfigure(1, weight=1)  # main
app.grid_rowconfigure(0, weight=1)

# -----------------------------
# Block: Sidebar
# -----------------------------
sidebar = ctk.CTkFrame(app, corner_radius=0)
sidebar.grid(row=0, column=0, sticky="nsw")
sidebar.grid_rowconfigure(9, weight=1)

title = ctk.CTkLabel(sidebar, text="Controls", font=("Segoe UI", 16, "bold"))
title.grid(row=0, column=0, padx=16, pady=(18, 10), sticky="w")

status_var = ctk.StringVar(value="Ready")

status_label = ctk.CTkLabel(sidebar, textvariable=status_var, font=("Segoe UI", 12))
status_label.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

model_label = ctk.CTkLabel(sidebar, text="Model", font=("Segoe UI", 12, "bold"))
model_label.grid(row=2, column=0, padx=16, pady=(4, 6), sticky="w")

model_var = ctk.StringVar(value=DEFAULT_MODEL)
model_menu = ctk.CTkOptionMenu(sidebar, values=MODEL_OPTIONS, variable=model_var)
model_menu.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="we")

role_label = ctk.CTkLabel(sidebar, text="Role", font=("Segoe UI", 12, "bold"))
role_label.grid(row=4, column=0, padx=16, pady=(4, 6), sticky="w")

role_box = ctk.CTkTextbox(sidebar, height=140, font=("Segoe UI", 11))
role_box.grid(row=5, column=0, padx=16, pady=(0, 12), sticky="we")
role_box.insert("1.0", DEFAULT_ROLE)

def set_role():
    global current_role, chat
    current_role = safe_text(role_box.get("1.0", "end"))
    chat = CLIENT.chats.create(model=model_var.get())
    add_system("Role updated. Memory reset.")
    status_var.set("Ready")
    log_line("SYSTEM: role updated")

apply_role_btn = ctk.CTkButton(sidebar, text="Apply Role (reset)", command=set_role)
apply_role_btn.grid(row=6, column=0, padx=16, pady=(0, 8), sticky="we")

def new_chat():
    global chat
    chat = CLIENT.chats.create(model=model_var.get())
    clear_chat_view()
    add_system("New chat started.")
    status_var.set("Ready")
    log_line("SYSTEM: new chat")

new_chat_btn = ctk.CTkButton(sidebar, text="New Chat", command=new_chat)
new_chat_btn.grid(row=7, column=0, padx=16, pady=(0, 8), sticky="we")

def clear_memory():
    global chat
    chat = CLIENT.chats.create(model=model_var.get())
    add_system("Memory cleared.")
    status_var.set("Ready")
    log_line("SYSTEM: memory cleared")

clear_btn = ctk.CTkButton(sidebar, text="Clear Memory", command=clear_memory)
clear_btn.grid(row=8, column=0, padx=16, pady=(0, 8), sticky="we")

def save_chat():
    content = export_chat_text()
    if not content.strip():
        messagebox.showinfo("Save", "Nothing to save.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")]
    )
    if not path:
        return

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    messagebox.showinfo("Save", f"Saved to:\n{path}")

save_btn = ctk.CTkButton(sidebar, text="Save Chat", command=save_chat)
save_btn.grid(row=10, column=0, padx=16, pady=(0, 18), sticky="we")

def toggle_theme():
    mode = ctk.get_appearance_mode().lower()
    ctk.set_appearance_mode("light" if mode == "dark" else "dark")

theme_btn = ctk.CTkButton(sidebar, text="Toggle Theme", command=toggle_theme)
theme_btn.grid(row=11, column=0, padx=16, pady=(0, 18), sticky="we")

# -----------------------------
# Block: Main chat area
# -----------------------------
main = ctk.CTkFrame(app, corner_radius=0)
main.grid(row=0, column=1, sticky="nsew")
main.grid_rowconfigure(0, weight=1)
main.grid_columnconfigure(0, weight=1)

# Scrollable chat container
chat_scroll = ctk.CTkScrollableFrame(main, corner_radius=0)
chat_scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

# Input bar
input_bar = ctk.CTkFrame(main, corner_radius=0)
input_bar.grid(row=1, column=0, sticky="ew")
input_bar.grid_columnconfigure(0, weight=1)

entry = ctk.CTkEntry(input_bar, placeholder_text="Ask Evo anything...", font=("Segoe UI", 12))
entry.grid(row=0, column=0, padx=14, pady=14, sticky="ew")

send_btn = ctk.CTkButton(input_bar, text="Send", width=110)
send_btn.grid(row=0, column=1, padx=(0, 14), pady=14)

# -----------------------------
# Block: Chat rendering + export
# -----------------------------
chat_lines = []  # list of tuples: (sender, text)

def add_system(text: str):
    add_message("system", text)

def add_message(sender: str, text: str):
    text = safe_text(text)
    if not text:
        return

    chat_lines.append((sender, text))

    if sender == "system":
        sys_label = ctk.CTkLabel(
            chat_scroll,
            text=text,
            text_color="#9ca3af",
            font=("Segoe UI", 11, "italic"),
            wraplength=720,
            justify="left",
            anchor="w",
        )
        sys_label.pack(anchor="w", padx=14, pady=(10, 6))
        return

    bubble = ChatBubble(chat_scroll, text=text, sender=("user" if sender == "user" else "bot"))
    chat_scroll.update_idletasks()

def clear_chat_view():
    global chat_lines
    chat_lines = []
    for widget in chat_scroll.winfo_children():
        widget.destroy()

def export_chat_text() -> str:
    out = []
    for sender, text in chat_lines:
        if sender == "user":
            out.append(f"You: {text}")
        elif sender == "bot":
            out.append(f"Bot: {text}")
        else:
            out.append(f"System: {text}")
    return "\n".join(out) + "\n"

# -----------------------------
# Block: Gemini call in background thread
# -----------------------------
def call_gemini(user_text: str):
    global chat

    try:
        status_var.set("Thinking...")

        # Block: ensure chat uses selected model
        selected_model = model_var.get()
        if getattr(chat, "model", None) != selected_model:
            chat = CLIENT.chats.create(model=selected_model)

        prompt = f"ROLE:\n{current_role}\n\nUSER:\n{user_text}"

        resp = chat.send_message(prompt)
        reply = safe_text(resp.text) or "(no response)"

        # Block: update UI from main thread
        app.after(0, lambda: add_message("bot", reply))
        app.after(0, lambda: status_var.set("Ready"))

        log_line("YOU: " + user_text)
        log_line("BOT: " + reply)
        log_line("")

    except Exception as e:
        app.after(0, lambda: add_message("bot", f"Error: {e}"))
        app.after(0, lambda: status_var.set("Ready"))
        log_line("ERROR: " + str(e))

def send_message():
    user_text = safe_text(entry.get())
    if not user_text:
        return

    # Commands
    if user_text.lower() == "/clear":
        entry.delete(0, "end")
        clear_memory()
        return
    if user_text.lower() == "/new":
        entry.delete(0, "end")
        new_chat()
        return

    entry.delete(0, "end")
    add_message("user", user_text)

    thread = threading.Thread(target=call_gemini, args=(user_text,), daemon=True)
    thread.start()

send_btn.configure(command=send_message)
entry.bind("<Return>", lambda e: send_message())

# -----------------------------
# Block: Welcome message
# -----------------------------
add_system("Welcome To EVO v 10.0.1. Commands: /new starts a fresh chat, /clear clears memory.")
add_system(f"Using model: {DEFAULT_MODEL}")
log_line("SYSTEM: app started")
log_line("SYSTEM: " + DEFAULT_ROLE)

app.mainloop()
