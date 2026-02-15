# gemini_pro_gui.py
# Modern Gemini desktop assistant with:
# - CustomTkinter modern UI
# - chat bubbles + timestamps
# - status bar: Ready / Listening / Thinking
# - model picker + role editor
# - save chat, new chat, clear memory
# - voice input (speech-to-text)
# - speak replies (text-to-speech)
# - hotkeys + settings persistence
# - non-freezing UI (threads)

import os
import json
import threading
import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
from google import genai

# Optional: load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Voice features
import pyttsx3
import speech_recognition as sr

# ----------------------------
# Block: Settings persistence
# ----------------------------
SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

settings = load_settings()

# ----------------------------
# Block: API key + client
# ----------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    messagebox.showerror(
        "Missing API Key",
        "GEMINI_API_KEY is not set.\n\n"
        "Fix options:\n"
        "1) In PowerShell:\n"
        "   $env:GEMINI_API_KEY=\"your_key\"\n\n"
        "2) Create a .env file next to this script:\n"
        "   GEMINI_API_KEY=your_key"
    )
    raise RuntimeError("GEMINI_API_KEY is not set.")

CLIENT = genai.Client(api_key=API_KEY)

MODEL_OPTIONS = [
    "models/gemini-flash-latest",
    "models/gemini-pro-latest",
    "models/gemini-2.0-flash",
    "models/gemini-2.5-flash",
    "models/gemma-3-4b-it",
]

DEFAULT_MODEL = settings.get("model", "models/gemini-flash-latest")
DEFAULT_ROLE = settings.get(
    "role",
    "You are a helpful assistant. Keep replies short, clear, and friendly."
)

# ----------------------------
# Block: Voice engines
# ----------------------------
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", int(settings.get("tts_rate", 175)))

recognizer = sr.Recognizer()

def speak(text: str):
    if not state["tts_enabled"]:
        return
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception:
        pass

def listen_once():
    """
    Speech-to-text using SpeechRecognition.
    This uses a free recognizer backend and usually needs internet.
    If mic fails, it returns None without crashing the app.
    """
    try:
        with sr.Microphone() as source:
            set_status("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
        set_status("Transcribing...")
        text = recognizer.recognize_google(audio)
        return text.strip() if text else None
    except Exception:
        set_status("Ready")
        return None

# ----------------------------
# Block: App state
# ----------------------------
state = {
    "model": DEFAULT_MODEL,
    "role": DEFAULT_ROLE,
    "theme": settings.get("theme", "dark"),
    "tts_enabled": bool(settings.get("tts_enabled", True)),
}

chat = CLIENT.chats.create(model=state["model"])

# ----------------------------
# Block: UI setup
# ----------------------------
ctk.set_default_color_theme("blue")
ctk.set_appearance_mode(state["theme"])

app = ctk.CTk()
app.title("Evo Assistant Pro")
app.geometry("1120x720")
app.minsize(980, 640)

app.grid_columnconfigure(0, weight=0)
app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=1)

# Sidebar
sidebar = ctk.CTkFrame(app, corner_radius=0, width=280)
sidebar.grid(row=0, column=0, sticky="nsw")
sidebar.grid_rowconfigure(20, weight=1)

# Main
main = ctk.CTkFrame(app, corner_radius=0)
main.grid(row=0, column=1, sticky="nsew")
main.grid_rowconfigure(0, weight=1)
main.grid_columnconfigure(0, weight=1)

# Status bar variable
status_var = ctk.StringVar(value="Ready")

def set_status(text: str):
    status_var.set(text)

# ----------------------------
# Block: Chat view (bubbles)
# ----------------------------
chat_scroll = ctk.CTkScrollableFrame(main, corner_radius=0)
chat_scroll.grid(row=0, column=0, sticky="nsew")

chat_lines = []  # list of dicts: {sender, text, ts}

def now_ts():
    return datetime.datetime.now().strftime("%H:%M")

def bubble_color(sender: str):
    if sender == "user":
        return ("#2563eb", "#2563eb")
    if sender == "bot":
        return ("#1f2937", "#111827")
    return ("#111827", "#111827")

def text_color(sender: str):
    if sender == "user":
        return "#ffffff"
    if sender == "bot":
        return "#e5e7eb"
    return "#9ca3af"

def add_message(sender: str, text: str):
    text = (text or "").strip()
    if not text:
        return

    msg = {"sender": sender, "text": text, "ts": now_ts()}
    chat_lines.append(msg)

    # System messages as subtle labels
    if sender == "system":
        label = ctk.CTkLabel(
            chat_scroll,
            text=f"[{msg['ts']}] {text}",
            text_color=text_color(sender),
            font=("Segoe UI", 11, "italic"),
            wraplength=760,
            justify="left",
        )
        label.pack(anchor="w", padx=14, pady=(10, 6))
        return

    # Bubble frame
    bubble = ctk.CTkFrame(chat_scroll, corner_radius=14, fg_color=bubble_color(sender))
    time_lbl = ctk.CTkLabel(
        bubble,
        text=msg["ts"],
        text_color=text_color(sender),
        font=("Segoe UI", 10),
    )
    body_lbl = ctk.CTkLabel(
        bubble,
        text=text,
        text_color=text_color(sender),
        font=("Segoe UI", 12),
        wraplength=720,
        justify="left",
        anchor="w",
    )

    time_lbl.pack(anchor="w", padx=12, pady=(8, 0))
    body_lbl.pack(anchor="w", padx=12, pady=(2, 10))

    if sender == "user":
        bubble.pack(anchor="e", padx=14, pady=6)
    else:
        bubble.pack(anchor="w", padx=14, pady=6)

    chat_scroll.update_idletasks()

def export_chat_text():
    out = []
    for m in chat_lines:
        label = "You" if m["sender"] == "user" else ("Bot" if m["sender"] == "bot" else "System")
        out.append(f"[{m['ts']}] {label}: {m['text']}")
    return "\n".join(out) + "\n"

def clear_chat_view():
    chat_lines.clear()
    for w in chat_scroll.winfo_children():
        w.destroy()

# ----------------------------
# Block: Sidebar widgets
# ----------------------------
ctk.CTkLabel(sidebar, text="Evo Assistant Pro", font=("Segoe UI", 16, "bold")).grid(
    row=0, column=0, padx=16, pady=(18, 6), sticky="w"
)

ctk.CTkLabel(sidebar, textvariable=status_var, font=("Segoe UI", 12)).grid(
    row=1, column=0, padx=16, pady=(0, 12), sticky="w"
)

ctk.CTkLabel(sidebar, text="Model", font=("Segoe UI", 12, "bold")).grid(
    row=2, column=0, padx=16, pady=(4, 6), sticky="w"
)

model_var = ctk.StringVar(value=state["model"])
model_menu = ctk.CTkOptionMenu(sidebar, values=MODEL_OPTIONS, variable=model_var)
model_menu.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="we")

ctk.CTkLabel(sidebar, text="Role", font=("Segoe UI", 12, "bold")).grid(
    row=4, column=0, padx=16, pady=(4, 6), sticky="w"
)

role_box = ctk.CTkTextbox(sidebar, height=150, font=("Segoe UI", 11))
role_box.grid(row=5, column=0, padx=16, pady=(0, 12), sticky="we")
role_box.insert("1.0", state["role"])

def reset_chat_memory():
    global chat
    chat = CLIENT.chats.create(model=model_var.get())

def apply_role():
    state["role"] = role_box.get("1.0", "end").strip()
    reset_chat_memory()
    add_message("system", "Role updated. Memory reset.")
    persist()

def new_chat():
    reset_chat_memory()
    clear_chat_view()
    add_message("system", "New chat started.")
    persist()

def clear_memory():
    reset_chat_memory()
    add_message("system", "Memory cleared.")
    persist()

def save_chat():
    content = export_chat_text().strip()
    if not content:
        messagebox.showinfo("Save", "Nothing to save.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if not path:
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    messagebox.showinfo("Save", f"Saved to:\n{path}")

def toggle_theme():
    mode = ctk.get_appearance_mode().lower()
    new_mode = "light" if mode == "dark" else "dark"
    ctk.set_appearance_mode(new_mode)
    state["theme"] = new_mode
    persist()

def toggle_tts():
    state["tts_enabled"] = not state["tts_enabled"]
    tts_btn.configure(text=("Speak: ON" if state["tts_enabled"] else "Speak: OFF"))
    persist()

def persist():
    save_settings({
        "model": model_var.get(),
        "role": state["role"],
        "theme": state["theme"],
        "tts_enabled": state["tts_enabled"],
        "tts_rate": tts_engine.getProperty("rate"),
    })

apply_btn = ctk.CTkButton(sidebar, text="Apply Role (reset)", command=apply_role)
apply_btn.grid(row=6, column=0, padx=16, pady=(0, 8), sticky="we")

ctk.CTkButton(sidebar, text="New Chat", command=new_chat).grid(
    row=7, column=0, padx=16, pady=(0, 8), sticky="we"
)

ctk.CTkButton(sidebar, text="Clear Memory", command=clear_memory).grid(
    row=8, column=0, padx=16, pady=(0, 8), sticky="we"
)

ctk.CTkButton(sidebar, text="Save Chat", command=save_chat).grid(
    row=9, column=0, padx=16, pady=(0, 14), sticky="we"
)

tts_btn = ctk.CTkButton(sidebar, text=("Speak: ON" if state["tts_enabled"] else "Speak: OFF"), command=toggle_tts)
tts_btn.grid(row=10, column=0, padx=16, pady=(0, 8), sticky="we")

ctk.CTkButton(sidebar, text="Toggle Theme", command=toggle_theme).grid(
    row=11, column=0, padx=16, pady=(0, 14), sticky="we"
)

ctk.CTkLabel(sidebar, text="Voice", font=("Segoe UI", 12, "bold")).grid(
    row=12, column=0, padx=16, pady=(6, 6), sticky="w"
)

# ----------------------------
# Block: Input bar + buttons
# ----------------------------
input_bar = ctk.CTkFrame(main, corner_radius=0)
input_bar.grid(row=1, column=0, sticky="ew")
input_bar.grid_columnconfigure(0, weight=1)

entry = ctk.CTkEntry(input_bar, placeholder_text="Ask Evo Anything...", font=("Segoe UI", 12))
entry.grid(row=0, column=0, padx=14, pady=14, sticky="ew")

def start_voice():
    def worker():
        text = listen_once()
        if text:
            app.after(0, lambda: entry.delete(0, "end"))
            app.after(0, lambda: entry.insert(0, text))
        app.after(0, lambda: set_status("Ready"))

    threading.Thread(target=worker, daemon=True).start()

voice_btn = ctk.CTkButton(input_bar, text="Mic", width=110, command=start_voice)
voice_btn.grid(row=0, column=1, padx=(0, 8), pady=14)

send_btn = ctk.CTkButton(input_bar, text="Send", width=110)
send_btn.grid(row=0, column=2, padx=(0, 14), pady=14)

# ----------------------------
# Block: Gemini call (threaded)
# ----------------------------
def call_gemini(user_text: str):
    global chat

    try:
        set_status("Thinking...")

        selected_model = model_var.get()
        if selected_model != state["model"]:
            state["model"] = selected_model
            reset_chat_memory()
            persist()

        prompt = f"ROLE:\n{state['role']}\n\nUSER:\n{user_text}"

        resp = chat.send_message(prompt)
        reply = (resp.text or "").strip() or "(no response)"

        app.after(0, lambda: add_message("bot", reply))
        app.after(0, lambda: set_status("Ready"))

        speak(reply)

    except Exception as e:
        app.after(0, lambda: add_message("bot", f"Error: {e}"))
        app.after(0, lambda: set_status("Ready"))

def send_message():
    user_text = (entry.get() or "").strip()
    if not user_text:
        return

    # Commands
    lower = user_text.lower()
    if lower == "/new":
        entry.delete(0, "end")
        new_chat()
        return
    if lower == "/clear":
        entry.delete(0, "end")
        clear_memory()
        return

    entry.delete(0, "end")
    add_message("user", user_text)
    threading.Thread(target=call_gemini, args=(user_text,), daemon=True).start()

send_btn.configure(command=send_message)
entry.bind("<Return>", lambda e: send_message())

# ----------------------------
# Block: Hotkeys
# ----------------------------
app.bind("<Control-s>", lambda e: save_chat())
app.bind("<Control-n>", lambda e: new_chat())
app.bind("<Control-l>", lambda e: clear_memory())

# ----------------------------
# Block: Welcome
# ----------------------------
add_message("system", "Welcome To Evo Assistant Pro. Commands: /new (new chat), /clear (clear memory). Hotkeys: Ctrl+N, Ctrl+L, Ctrl+S.")

app.mainloop()
