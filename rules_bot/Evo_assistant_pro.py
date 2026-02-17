import os
import json
import time
import threading
import datetime
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from dotenv import load_dotenv
import customtkinter as ctk
from tkinter import filedialog, messagebox

from google import genai

# Voice
import pyttsx3
import speech_recognition as sr


# =========================
# Evo v10 Pro Configuration
# =========================

APP_TITLE = "Evo v10 Pro"
SETTINGS_FILE = "evo_settings.json"
DEFAULT_MODEL = "gemini-3-flash-preview"

MODEL_OPTIONS = [
    "gemini-3-flash-preview",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.5-flash",
]


DEFAULT_ROLE = (
    "You are Evo, a helpful assistant.\n"
    "Rules:\n"
    "1) Be clear and practical.\n"
    "2) Use short steps when giving instructions.\n"
    "3) If info is missing, ask one question.\n"
)

VOICE_COMMANDS_HELP = (
    "Voice commands you can say:\n"
    "- 'clear chat'\n"
    "- 'new chat'\n"
    "- 'save chat'\n"
    "- 'toggle speak'\n"
    "- 'help commands'\n"
)

# =========================
# Utilities
# =========================

def now_ts() -> str:
    return datetime.datetime.now().strftime("%H:%M")


def safe_read_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def safe_write_json(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def normalize_voice_command(text: str) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


# =========================
# Evo Message Model
# =========================

@dataclass
class Msg:
    sender: str  # "user" | "evo" | "system"
    text: str
    ts: str


# =========================
# Evo App
# =========================

class EvoProApp:
    def __init__(self):
        # Load env
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            messagebox.showerror(
                "Missing GEMINI_API_KEY",
                "GEMINI_API_KEY is not set.\n\n"
                "Fix:\n"
                "1) Create .env next to this script\n"
                "   GEMINI_API_KEY=your_key\n\n"
                "2) Or set in PowerShell:\n"
                '   $env:GEMINI_API_KEY="your_key"\n'
            )
            raise RuntimeError("GEMINI_API_KEY missing")

        # Settings
        s = safe_read_json(SETTINGS_FILE)
        self.model_id = s.get("model", DEFAULT_MODEL)
        self.role_text = s.get("role", DEFAULT_ROLE)
        self.theme = s.get("theme", "dark")
        self.speak_enabled = bool(s.get("speak_enabled", True))
        self.tts_rate = int(s.get("tts_rate", 175))
        self.mic_auto_send = bool(s.get("mic_auto_send", True))

        # Gemini client + chat memory
        self.client = genai.Client(api_key=self.api_key)
        self.chat = self.client.chats.create(model=self.model_id)

        # Voice engines
        self.tts = pyttsx3.init()
        self.tts.setProperty("rate", self.tts_rate)
        self.recognizer = sr.Recognizer()

        # Chat log
        self.messages: List[Msg] = []

        # UI setup
        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode(self.theme)

        self.app = ctk.CTk()
        self.app.title(APP_TITLE)
        self.app.geometry("1180x720")
        self.app.minsize(1050, 640)

        self.status_var = ctk.StringVar(value="Ready")

        self._build_layout()
        self._bind_hotkeys()

        self.add_system(f"Welcome to {APP_TITLE}.")
        self.add_system("Shortcuts: Enter send, Ctrl+N new chat, Ctrl+L clear, Ctrl+S save, Ctrl+F search.")
        self.add_system("Type /help for commands. Use Mic button for voice.")

    # -------------------------
    # UI
    # -------------------------

    def _build_layout(self):
        self.app.grid_columnconfigure(0, weight=0)
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self.app, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(20, weight=1)

        # Main
        self.main = ctk.CTkFrame(self.app, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # Sidebar content
        ctk.CTkLabel(self.sidebar, text="Evo v10 Pro", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, padx=16, pady=(18, 6), sticky="w"
        )
        ctk.CTkLabel(self.sidebar, textvariable=self.status_var, font=("Segoe UI", 12)).grid(
            row=1, column=0, padx=16, pady=(0, 12), sticky="w"
        )

        ctk.CTkLabel(self.sidebar, text="Model", font=("Segoe UI", 12, "bold")).grid(
            row=2, column=0, padx=16, pady=(6, 6), sticky="w"
        )
        self.model_var = ctk.StringVar(value=self.model_id)
        self.model_menu = ctk.CTkOptionMenu(self.sidebar, values=MODEL_OPTIONS, variable=self.model_var)
        self.model_menu.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="we")

        ctk.CTkLabel(self.sidebar, text="Role", font=("Segoe UI", 12, "bold")).grid(
            row=4, column=0, padx=16, pady=(6, 6), sticky="w"
        )
        self.role_box = ctk.CTkTextbox(self.sidebar, height=170, font=("Segoe UI", 11))
        self.role_box.grid(row=5, column=0, padx=16, pady=(0, 10), sticky="we")
        self.role_box.insert("1.0", self.role_text)

        self.apply_role_btn = ctk.CTkButton(self.sidebar, text="Apply Role (resets memory)", command=self.apply_role)
        self.apply_role_btn.grid(row=6, column=0, padx=16, pady=(0, 8), sticky="we")

        self.new_btn = ctk.CTkButton(self.sidebar, text="New Chat", command=self.new_chat)
        self.new_btn.grid(row=7, column=0, padx=16, pady=(0, 8), sticky="we")

        self.clear_btn = ctk.CTkButton(self.sidebar, text="Clear Chat View", command=self.clear_chat_view)
        self.clear_btn.grid(row=8, column=0, padx=16, pady=(0, 8), sticky="we")

        self.save_btn = ctk.CTkButton(self.sidebar, text="Save Chat (txt)", command=self.save_chat)
        self.save_btn.grid(row=9, column=0, padx=16, pady=(0, 8), sticky="we")

        # Voice controls
        ctk.CTkLabel(self.sidebar, text="Voice", font=("Segoe UI", 12, "bold")).grid(
            row=10, column=0, padx=16, pady=(12, 6), sticky="w"
        )

        self.speak_btn = ctk.CTkButton(
            self.sidebar,
            text=("Speak: ON" if self.speak_enabled else "Speak: OFF"),
            command=self.toggle_speak,
        )
        self.speak_btn.grid(row=11, column=0, padx=16, pady=(0, 8), sticky="we")

        self.mic_send_var = ctk.BooleanVar(value=self.mic_auto_send)
        self.mic_send_chk = ctk.CTkCheckBox(
            self.sidebar,
            text="Auto-send after voice",
            variable=self.mic_send_var,
            command=self._on_mic_send_toggle,
        )
        self.mic_send_chk.grid(row=12, column=0, padx=16, pady=(0, 8), sticky="w")

        self.theme_btn = ctk.CTkButton(self.sidebar, text="Toggle Theme", command=self.toggle_theme)
        self.theme_btn.grid(row=13, column=0, padx=16, pady=(0, 8), sticky="we")

        # Search
        ctk.CTkLabel(self.sidebar, text="Search", font=("Segoe UI", 12, "bold")).grid(
            row=14, column=0, padx=16, pady=(12, 6), sticky="w"
        )
        self.search_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Find in chat...")
        self.search_entry.grid(row=15, column=0, padx=16, pady=(0, 8), sticky="we")

        self.search_btn = ctk.CTkButton(self.sidebar, text="Search", command=self.search_chat)
        self.search_btn.grid(row=16, column=0, padx=16, pady=(0, 8), sticky="we")

        self.search_result = ctk.CTkLabel(self.sidebar, text="", font=("Segoe UI", 11))
        self.search_result.grid(row=17, column=0, padx=16, pady=(0, 8), sticky="w")

        # Main: chat feed + input
        self.chat_feed = ctk.CTkScrollableFrame(self.main, corner_radius=0)
        self.chat_feed.grid(row=0, column=0, sticky="nsew")

        self.input_bar = ctk.CTkFrame(self.main, corner_radius=0)
        self.input_bar.grid(row=1, column=0, sticky="ew")
        self.input_bar.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_bar, placeholder_text="Message Evo...")
        self.entry.grid(row=0, column=0, padx=12, pady=12, sticky="ew")

        self.mic_btn = ctk.CTkButton(self.input_bar, text="Mic", width=110, command=self.voice_input)
        self.mic_btn.grid(row=0, column=1, padx=(0, 8), pady=12)

        self.send_btn = ctk.CTkButton(self.input_bar, text="Send", width=110, command=self.send_message)
        self.send_btn.grid(row=0, column=2, padx=(0, 12), pady=12)

        self.entry.bind("<Return>", lambda e: self.send_message())

    def _bind_hotkeys(self):
        self.app.bind("<Control-n>", lambda e: self.new_chat())
        self.app.bind("<Control-l>", lambda e: self.clear_chat_view())
        self.app.bind("<Control-s>", lambda e: self.save_chat())
        self.app.bind("<Control-f>", lambda e: self._focus_search())

    def _focus_search(self):
        self.search_entry.focus_set()

    # -------------------------
    # Persistence
    # -------------------------

    def persist(self):
        safe_write_json(
            SETTINGS_FILE,
            {
                "model": self.model_var.get(),
                "role": self.role_text,
                "theme": self.theme,
                "speak_enabled": self.speak_enabled,
                "tts_rate": int(self.tts.getProperty("rate")),
                "mic_auto_send": self.mic_auto_send,
            },
        )

    def _on_mic_send_toggle(self):
        self.mic_auto_send = bool(self.mic_send_var.get())
        self.persist()

    # -------------------------
    # Chat UI helpers
    # -------------------------

    def set_status(self, text: str):
        self.status_var.set(text)

    def add_system(self, text: str):
        self._add_msg("system", text)

    def add_user(self, text: str):
        self._add_msg("user", text)

    def add_evo(self, text: str):
        self._add_msg("evo", text)

    def _add_msg(self, sender: str, text: str):
        text = (text or "").strip()
        if not text:
            return
        msg = Msg(sender=sender, text=text, ts=now_ts())
        self.messages.append(msg)

        if sender == "system":
            lbl = ctk.CTkLabel(
                self.chat_feed,
                text=f"[{msg.ts}] {text}",
                font=("Segoe UI", 11, "italic"),
                text_color="#9ca3af",
                wraplength=780,
                justify="left",
            )
            lbl.pack(anchor="w", padx=14, pady=(10, 6))
            return

        bubble_color = "#2563eb" if sender == "user" else "#111827"
        text_color = "#ffffff" if sender == "user" else "#e5e7eb"
        anchor = "e" if sender == "user" else "w"

        bubble = ctk.CTkFrame(self.chat_feed, corner_radius=14, fg_color=bubble_color)
        t = ctk.CTkLabel(bubble, text=msg.ts, font=("Segoe UI", 10), text_color=text_color)
        b = ctk.CTkLabel(
            bubble,
            text=text,
            font=("Segoe UI", 12),
            text_color=text_color,
            wraplength=760,
            justify="left",
        )
        t.pack(anchor="w", padx=12, pady=(8, 0))
        b.pack(anchor="w", padx=12, pady=(2, 10))
        bubble.pack(anchor=anchor, padx=14, pady=6)
        self.chat_feed.update_idletasks()

    def clear_chat_view(self):
        self.messages.clear()
        for w in self.chat_feed.winfo_children():
            w.destroy()
        self.add_system("Chat view cleared (memory not reset).")

    def export_chat_text(self) -> str:
        lines = []
        for m in self.messages:
            who = "You" if m.sender == "user" else ("Evo" if m.sender == "evo" else "System")
            lines.append(f"[{m.ts}] {who}: {m.text}")
        return "\n".join(lines) + "\n"

    def save_chat(self):
        if not self.messages:
            messagebox.showinfo("Save", "Nothing to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text file", "*.txt")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.export_chat_text())
        messagebox.showinfo("Saved", f"Saved chat to:\n{path}")

    def search_chat(self):
        q = (self.search_entry.get() or "").strip().lower()
        if not q:
            self.search_result.configure(text="Type something to search.")
            return

        hits = 0
        last_hit: Optional[Msg] = None
        for m in self.messages:
            if q in m.text.lower():
                hits += 1
                last_hit = m

        if hits == 0:
            self.search_result.configure(text="No matches.")
            return

        if last_hit:
            self.search_result.configure(text=f"Matches: {hits}. Last at {last_hit.ts} ({last_hit.sender}).")
        else:
            self.search_result.configure(text=f"Matches: {hits}.")

    # -------------------------
    # Model + Role
    # -------------------------

    def reset_memory(self):
        self.model_id = self.model_var.get()
        self.chat = self.client.chats.create(model=self.model_id)

    def apply_role(self):
        self.role_text = self.role_box.get("1.0", "end").strip() or DEFAULT_ROLE
        self.reset_memory()
        self.add_system("Role applied. Memory reset.")
        self.persist()

    def new_chat(self):
        self.reset_memory()
        self.clear_chat_view()
        self.add_system("New chat started.")
        self.persist()

    def toggle_theme(self):
        mode = ctk.get_appearance_mode().lower()
        new_mode = "light" if mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.theme = new_mode
        self.persist()

    # -------------------------
    # Voice: STT + TTS
    # -------------------------

    def toggle_speak(self):
        self.speak_enabled = not self.speak_enabled
        self.speak_btn.configure(text=("Speak: ON" if self.speak_enabled else "Speak: OFF"))
        self.persist()

    def speak(self, text: str):
        if not self.speak_enabled:
            return
        text = (text or "").strip()
        if not text:
            return

        def worker():
            try:
                self.tts.say(text)
                self.tts.runAndWait()
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def voice_input(self):
        def worker():
            try:
                self.set_status("Listening...")
                with sr.Microphone() as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=10)

                self.set_status("Transcribing...")
                text = self.recognizer.recognize_google(audio)
                text = (text or "").strip()

                self.app.after(0, lambda: self.set_status("Ready"))

                if not text:
                    self.app.after(0, lambda: self.add_system("Voice: no speech detected."))
                    return

                # Handle voice commands
                cmd = normalize_voice_command(text)
                if self._handle_voice_command(cmd):
                    return

                # Put text into entry
                def fill():
                    self.entry.delete(0, "end")
                    self.entry.insert(0, text)

                self.app.after(0, fill)

                if self.mic_auto_send:
                    self.app.after(0, self.send_message)

            except Exception as e:
                self.app.after(0, lambda: self.set_status("Ready"))
                self.app.after(0, lambda: self.add_system(f"Voice error: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_voice_command(self, cmd: str) -> bool:
        if cmd in {"clear chat", "clear"}:
            self.app.after(0, self.clear_chat_view)
            self.app.after(0, lambda: self.add_system("Voice command: cleared chat view."))
            return True

        if cmd in {"new chat", "new"}:
            self.app.after(0, self.new_chat)
            self.app.after(0, lambda: self.add_system("Voice command: new chat."))
            return True

        if cmd in {"save chat", "save"}:
            self.app.after(0, self.save_chat)
            self.app.after(0, lambda: self.add_system("Voice command: save chat."))
            return True

        if cmd in {"toggle speak", "toggle speech", "toggle voice"}:
            self.app.after(0, self.toggle_speak)
            self.app.after(0, lambda: self.add_system("Voice command: toggled speak."))
            return True

        if cmd in {"help commands", "help"}:
            self.app.after(0, lambda: self.add_system(VOICE_COMMANDS_HELP))
            return True

        return False

    # -------------------------
    # Sending messages
    # -------------------------

    def send_message(self):
        user_text = (self.entry.get() or "").strip()
        if not user_text:
            return

        # Slash commands
        if user_text.lower() in {"/help", "help"}:
            self.entry.delete(0, "end")
            self.add_system(
                "Commands:\n"
                "- /help\n"
                "- /new\n"
                "- /clear (resets memory)\n"
                "- /save\n"
                "- /role (shows current role)\n"
            )
            return

        if user_text.lower() == "/new":
            self.entry.delete(0, "end")
            self.new_chat()
            return

        if user_text.lower() == "/save":
            self.entry.delete(0, "end")
            self.save_chat()
            return

        if user_text.lower() == "/role":
            self.entry.delete(0, "end")
            self.add_system(f"Current role:\n{self.role_text}")
            return

        if user_text.lower() == "/clear":
            self.entry.delete(0, "end")
            self.reset_memory()
            self.add_system("Memory cleared.")
            return

        # Send
        self.entry.delete(0, "end")
        self.add_user(user_text)

        # Model changed?
        selected_model = self.model_var.get()
        if selected_model != self.model_id:
            self.model_id = selected_model
            self.reset_memory()
            self.add_system(f"Model changed to {self.model_id}. Memory reset.")
            self.persist()

        self.set_status("Thinking...")
        self.send_btn.configure(state="disabled")
        self.mic_btn.configure(state="disabled")

        def worker():
            try:
                prompt = f"ROLE:\n{self.role_text}\n\nUSER:\n{user_text}"

                # Chat memory call
                resp = self.chat.send_message(prompt)
                reply = (resp.text or "").strip() or "(no response)"

                self.app.after(0, lambda: self.add_evo(reply))
                self.app.after(0, lambda: self.set_status("Ready"))
                self.app.after(0, lambda: self.send_btn.configure(state="normal"))
                self.app.after(0, lambda: self.mic_btn.configure(state="normal"))

                self.speak(reply)

            except Exception as e:
                msg = str(e)
                # Friendly quota hint
                if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                    msg = "Rate limit hit. Wait a bit and try again."
                self.app.after(0, lambda: self.add_system(f"Error: {msg}"))
                self.app.after(0, lambda: self.set_status("Ready"))
                self.app.after(0, lambda: self.send_btn.configure(state="normal"))
                self.app.after(0, lambda: self.mic_btn.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # -------------------------
    # Run
    # -------------------------

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    EvoProApp().run()
