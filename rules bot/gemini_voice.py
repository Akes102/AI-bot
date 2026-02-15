import os
import threading
import datetime
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from google import genai

# Voice (offline TTS + online STT)
import pyttsx3
import speech_recognition as sr

# -------------------------
# Block: Config + API key
# -------------------------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)
MODEL = "models/gemini-flash-latest"

# -------------------------
# Block: Chat session memory
# -------------------------
chat = client.chats.create(model=MODEL)

ROLE = "You are a helpful assistant. Keep replies short and clear."

def reset_chat():
    global chat
    chat = client.chats.create(model=MODEL)

# -------------------------
# Block: Logging
# -------------------------
os.makedirs("logs", exist_ok=True)
log_file = os.path.join(
    "logs",
    datetime.datetime.now().strftime("gui_chat_%Y%m%d_%H%M%S.txt")
)

def log_line(line: str):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# -------------------------
# Block: Text-to-Speech (offline)
# -------------------------
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 175)

tts_enabled = True

def speak(text: str):
    if not tts_enabled:
        return
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception:
        pass

# -------------------------
# Block: Speech-to-Text (mic)
# -------------------------
recognizer = sr.Recognizer()
mic_enabled = True

def listen_once():
    """
    Records one user sentence from the microphone and returns it as text.
    Uses Google Web Speech through SpeechRecognition (free, but needs internet).
    """
    if not mic_enabled:
        return None

    try:
        with sr.Microphone() as source:
            status_var.set("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
        status_var.set("Transcribing...")
        return recognizer.recognize_google(audio)
    except sr.WaitTimeoutError:
        status_var.set("Ready")
        return None
    except sr.UnknownValueError:
        status_var.set("Ready")
        return None
    except Exception:
        status_var.set("Ready")
        return None

# -------------------------
# Block: GUI helpers
# -------------------------
def append_chat(prefix: str, text: str):
    chat_box.configure(state="normal")
    chat_box.insert(tk.END, f"{prefix}: {text}\n")
    chat_box.configure(state="disabled")
    chat_box.see(tk.END)

def append_divider():
    chat_box.configure(state="normal")
    chat_box.insert(tk.END, "-" * 60 + "\n")
    chat_box.configure(state="disabled")
    chat_box.see(tk.END)

def set_theme_dark():
    root.configure(bg="#111827")
    sidebar.configure(bg="#0f172a")
    main.configure(bg="#111827")
    topbar.configure(bg="#0b1220")
    for w in (title_label, status_label):
        w.configure(bg="#0b1220", fg="#e5e7eb")
    chat_box.configure(bg="#0b1220", fg="#e5e7eb", insertbackground="#e5e7eb")
    entry.configure(bg="#0b1220", fg="#e5e7eb", insertbackground="#e5e7eb")
    status_var.set("Ready (Dark theme)")

def set_theme_light():
    root.configure(bg="#f3f4f6")
    sidebar.configure(bg="#e5e7eb")
    main.configure(bg="#f3f4f6")
    topbar.configure(bg="#ffffff")
    for w in (title_label, status_label):
        w.configure(bg="#ffffff", fg="#111827")
    chat_box.configure(bg="#ffffff", fg="#111827", insertbackground="#111827")
    entry.configure(bg="#ffffff", fg="#111827", insertbackground="#111827")
    status_var.set("Ready (Light theme)")

# -------------------------
# Block: Gemini call in background thread (UI stays responsive)
# -------------------------
def gemini_reply(user_text: str):
    global chat

    try:
        status_var.set("Thinking...")

        prompt = f"ROLE:\n{ROLE}\n\nUSER:\n{user_text}"

        resp = chat.send_message(prompt)
        reply = resp.text.strip() if resp.text else "(no response)"

        append_chat("Evo", reply)
        append_divider()

        log_line("YOU: " + user_text)
        log_line("Evo: " + reply)
        log_line("")

        status_var.set("Ready")
        speak(reply)

    except Exception as e:
        status_var.set("Ready")
        append_chat("Bot", f"Error: {e}")
        append_divider()

def send_text():
    user_text = entry.get().strip()
    if not user_text:
        return

    if user_text.lower() == "/clear":
        clear_chat()
        return

    entry.delete(0, tk.END)
    append_chat("You", user_text)
    threading.Thread(target=gemini_reply, args=(user_text,), daemon=True).start()

def clear_chat():
    reset_chat()
    chat_box.configure(state="normal")
    chat_box.delete("1.0", tk.END)
    chat_box.configure(state="disabled")
    append_chat("System", "Memory cleared.")
    append_divider()
    log_line("SYSTEM: memory cleared")
    status_var.set("Ready")

def save_chat_to_file():
    content = chat_box.get("1.0", tk.END).strip()
    if not content:
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

def toggle_tts():
    global tts_enabled
    tts_enabled = not tts_enabled
    tts_btn.configure(text=("TTS: ON" if tts_enabled else "TTS: OFF"))

def start_voice_input():
    """
    Record voice in a background thread and put transcribed text into entry.
    """
    def worker():
        text = listen_once()
        if text:
            entry.delete(0, tk.END)
            entry.insert(0, text)
        status_var.set("Ready")

    threading.Thread(target=worker, daemon=True).start()

def set_role():
    global ROLE
    new_role = role_text.get("1.0", tk.END).strip()
    if not new_role:
        messagebox.showinfo("Role", "Role is empty.")
        return
    ROLE = new_role
    reset_chat()
    append_chat("System", "Role updated and memory reset.")
    append_divider()
    log_line("SYSTEM: role updated")
    status_var.set("Ready")

# -------------------------
# Block: Build GUI
# -------------------------
root = tk.Tk()
root.title("Evo Assistant v9")
root.geometry("980x620")

status_var = tk.StringVar(value="Ready")

# Layout: left sidebar + main content
sidebar = tk.Frame(root, width=260)
sidebar.pack(side=tk.LEFT, fill=tk.Y)

main = tk.Frame(root)
main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Top bar
topbar = tk.Frame(main, height=50)
topbar.pack(side=tk.TOP, fill=tk.X)

title_label = tk.Label(topbar, text="Evo Assistant", font=("Segoe UI", 14, "bold"))
title_label.pack(side=tk.LEFT, padx=12, pady=10)

status_label = tk.Label(topbar, textvariable=status_var, font=("Segoe UI", 10))
status_label.pack(side=tk.RIGHT, padx=12)

# Chat box
chat_box = scrolledtext.ScrolledText(main, wrap=tk.WORD, font=("Segoe UI", 11))
chat_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))
chat_box.configure(state="disabled")

# Input row
input_row = tk.Frame(main)
input_row.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 12))

entry = tk.Entry(input_row, font=("Segoe UI", 11))
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

send_btn = tk.Button(input_row, text="Send", width=10, command=send_text)
send_btn.pack(side=tk.LEFT)

voice_btn = tk.Button(input_row, text="🎤 Voice", width=10, command=start_voice_input)
voice_btn.pack(side=tk.LEFT, padx=(8, 0))

entry.bind("<Return>", lambda e: send_text())

# Sidebar controls
tk.Label(sidebar, text="Controls", font=("Segoe UI", 12, "bold")).pack(pady=(12, 6))

clear_btn = tk.Button(sidebar, text="Clear memory", command=clear_chat)
clear_btn.pack(fill=tk.X, padx=12, pady=4)

save_btn = tk.Button(sidebar, text="Save chat", command=save_chat_to_file)
save_btn.pack(fill=tk.X, padx=12, pady=4)

tts_btn = tk.Button(sidebar, text="TTS: ON", command=toggle_tts)
tts_btn.pack(fill=tk.X, padx=12, pady=4)

tk.Label(sidebar, text="Theme", font=("Segoe UI", 11, "bold")).pack(pady=(14, 6))
tk.Button(sidebar, text="Dark", command=set_theme_dark).pack(fill=tk.X, padx=12, pady=4)
tk.Button(sidebar, text="Light", command=set_theme_light).pack(fill=tk.X, padx=12, pady=4)

tk.Label(sidebar, text="Bot role (system prompt)", font=("Segoe UI", 10, "bold")).pack(pady=(14, 6))
role_text = scrolledtext.ScrolledText(sidebar, height=6, wrap=tk.WORD, font=("Segoe UI", 10))
role_text.pack(fill=tk.BOTH, padx=12, pady=4)
role_text.insert(tk.END, ROLE)

tk.Button(sidebar, text="Apply Role (resets memory)", command=set_role).pack(fill=tk.X, padx=12, pady=6)

# Welcome message
append_chat("System", "Welcome. Type /clear to reset memory. Use Voice to dictate.")
append_divider()

# Default theme
set_theme_dark()

root.mainloop()
