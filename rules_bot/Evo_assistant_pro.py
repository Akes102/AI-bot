
# =========================
# Imports
# =========================
# These are libraries (modules) i use. Each one adds a specific ability to the app.

import os                 # Work with environment variables + file paths
import json               # Read/write settings as JSON
import time               # Time helpers (not used much in this snippet but common for delays)
import threading          # Run long tasks in background so the UI doesn't freeze
import datetime           # Timestamps for chat messages
import re                 # Clean/normalize text using regular expressions
from dataclasses import dataclass  # Quick way to define simple data containers (Msg)

from typing import List, Optional, Tuple  # Type hints (helps readability and editor support)

from dotenv import load_dotenv            # Loads .env file into environment variables
import customtkinter as ctk               # Modern-looking Tkinter UI library
from tkinter import filedialog, messagebox # File save dialog + popup messages

from google import genai                  # Gemini (Google GenAI) client library

# Voice
import pyttsx3                            # Text-to-speech (TTS) engine (offline)
import speech_recognition as sr           # Speech-to-text (STT) using microphone


# =========================
# Evo v10 Pro Configuration
# =========================
# Constants: values that rarely change. Central place to tweak app behavior.

APP_TITLE = "Evo v10 Pro"                 # Window/app title shown at the top
SETTINGS_FILE = "evo_settings.json"       # Where user settings get saved/loaded
DEFAULT_MODEL = "gemini-3-flash-preview"  # Default Gemini model if no settings exist

MODEL_OPTIONS = [                         # Dropdown list options for model selection
    "gemini-3-flash-preview",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.5-flash",
]

# Default "role" or system instructions that shape how the assistant responds
DEFAULT_ROLE = (
    "You are Evo, a helpful assistant.\n"
    "Rules:\n"
    "1) Be clear and practical.\n"
    "2) Use short steps when giving instructions.\n"
    "3) If info is missing, ask one question.\n"
)

# Help text displayed when user asks for voice command help
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
# these functions gets reused in different parts of the app.

def now_ts() -> str:
    # Returns current time as "HH:MM" for message timestamps
    return datetime.datetime.now().strftime("%H:%M")


def safe_read_json(path: str) -> dict:
    # Reads a JSON file safely:
    # - If file doesn't exist -> return empty dict
    # - If file is invalid or error occurs -> return empty dict
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def safe_write_json(path: str, data: dict) -> None:
    # Writes a JSON file safely:
    # - Saves dict with nice indentation
    # - If writing fails, do nothing (prevents crashing the app)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def normalize_voice_command(text: str) -> str:
    # Normalizes voice input so commands match reliably:
    # - lowercase
    # - remove extra spaces
    t = (text or "").strip().lower()
    t = re.sub(r"\s+", " ", t)
    return t


# =========================
# Evo Message Model
# =========================
# A message "record" (data structure) for storing chat history in memory.

@dataclass
class Msg:
    sender: str  # Who sent it: "user" | "evo" | "system"
    text: str    # Message content
    ts: str      # Timestamp (HH:MM)


# =========================
# Evo App
# =========================
# Main application class: holds state (settings, UI widgets, chat, voice engines) and behavior.

class EvoProApp:
    def __init__(self):
        # -------------------------
        # Load environment variables
        # -------------------------
        load_dotenv()                              # Loads variables from a .env file (if present)
        self.api_key = os.getenv("GEMINI_API_KEY") # Reads the GEMINI_API_KEY from environment

        # If no key found, show a helpful error popup and stop the app
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

        # -------------------------
        # Load saved settings (or defaults)
        # -------------------------
        s = safe_read_json(SETTINGS_FILE)          # Load settings JSON if it exists
        self.model_id = s.get("model", DEFAULT_MODEL)          # Selected model (or default)
        self.role_text = s.get("role", DEFAULT_ROLE)           # Role text (or default)
        self.theme = s.get("theme", "dark")                     # UI theme ("dark" or "light")
        self.speak_enabled = bool(s.get("speak_enabled", True)) # Whether TTS is enabled
        self.tts_rate = int(s.get("tts_rate", 175))             # TTS speech rate
        self.mic_auto_send = bool(s.get("mic_auto_send", True)) # Auto-send after voice input

        # -------------------------
        # Gemini client + chat memory
        # -------------------------
        self.client = genai.Client(api_key=self.api_key)        # Create Gemini API client
        self.chat = self.client.chats.create(model=self.model_id)  # Create a chat session (keeps memory)

        # -------------------------
        # Voice engines (TTS + STT)
        # -------------------------
        self.tts = pyttsx3.init()                   # Initialize text-to-speech engine
        self.tts.setProperty("rate", self.tts_rate) # Set speech speed
        self.recognizer = sr.Recognizer()           # Create speech recognizer for microphone input

        # -------------------------
        # In-memory chat log
        # -------------------------
        self.messages: List[Msg] = []               # List of Msg objects for chat history

        # -------------------------
        # UI setup (CustomTkinter)
        # -------------------------
        ctk.set_default_color_theme("blue")         # UI accent theme
        ctk.set_appearance_mode(self.theme)         # Dark/light mode

        self.app = ctk.CTk()                        # Create the main window
        self.app.title(APP_TITLE)                   # Set window title
        self.app.geometry("1180x720")               # Initial window size
        self.app.minsize(1050, 640)                 # Minimum allowed window size

        self.status_var = ctk.StringVar(value="Ready")  # Status text shown in sidebar

        self._build_layout()                        # Build all UI widgets
        self._bind_hotkeys()                        # Setup keyboard shortcuts

        # Initial system messages in the chat view
        self.add_system(f"Welcome to {APP_TITLE}.")
        self.add_system("Shortcuts: Enter send, Ctrl+N new chat, Ctrl+L clear, Ctrl+S save, Ctrl+F search.")
        self.add_system("Type /help for commands. Use Mic button for voice.")

    # -------------------------
    # UI
    # -------------------------
    # These methods build the interface and wire up buttons/shortcuts.

    def _build_layout(self):
        # Configure window grid: sidebar (col 0) fixed, main content (col 1) expands
        self.app.grid_columnconfigure(0, weight=0)
        self.app.grid_columnconfigure(1, weight=1)
        self.app.grid_rowconfigure(0, weight=1)

        # Sidebar container (left panel)
        self.sidebar = ctk.CTkFrame(self.app, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(20, weight=1)  # Allows spacing stretch at bottom

        # Main container (right panel)
        self.main = ctk.CTkFrame(self.app, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        # -------------------------
        # Sidebar content
        # -------------------------
        ctk.CTkLabel(self.sidebar, text="Evo v10 Pro", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, padx=16, pady=(18, 6), sticky="w"
        )
        ctk.CTkLabel(self.sidebar, textvariable=self.status_var, font=("Segoe UI", 12)).grid(
            row=1, column=0, padx=16, pady=(0, 12), sticky="w"
        )

        # Model selector dropdown
        ctk.CTkLabel(self.sidebar, text="Model", font=("Segoe UI", 12, "bold")).grid(
            row=2, column=0, padx=16, pady=(6, 6), sticky="w"
        )
        self.model_var = ctk.StringVar(value=self.model_id)  # Selected model value
        self.model_menu = ctk.CTkOptionMenu(self.sidebar, values=MODEL_OPTIONS, variable=self.model_var)
        self.model_menu.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="we")

        # Role textbox (system prompt / instructions)
        ctk.CTkLabel(self.sidebar, text="Role", font=("Segoe UI", 12, "bold")).grid(
            row=4, column=0, padx=16, pady=(6, 6), sticky="w"
        )
        self.role_box = ctk.CTkTextbox(self.sidebar, height=170, font=("Segoe UI", 11))
        self.role_box.grid(row=5, column=0, padx=16, pady=(0, 10), sticky="we")
        self.role_box.insert("1.0", self.role_text)  # Fill textbox with current role

        # Apply role button resets model memory (starts fresh conversation)
        self.apply_role_btn = ctk.CTkButton(self.sidebar, text="Apply Role (resets memory)", command=self.apply_role)
        self.apply_role_btn.grid(row=6, column=0, padx=16, pady=(0, 8), sticky="we")

        # New chat button resets memory and clears UI
        self.new_btn = ctk.CTkButton(self.sidebar, text="New Chat", command=self.new_chat)
        self.new_btn.grid(row=7, column=0, padx=16, pady=(0, 8), sticky="we")

        # Clear chat view only clears UI log, not model memory
        self.clear_btn = ctk.CTkButton(self.sidebar, text="Clear Chat View", command=self.clear_chat_view)
        self.clear_btn.grid(row=8, column=0, padx=16, pady=(0, 8), sticky="we")

        # Save chat to a .txt file
        self.save_btn = ctk.CTkButton(self.sidebar, text="Save Chat (txt)", command=self.save_chat)
        self.save_btn.grid(row=9, column=0, padx=16, pady=(0, 8), sticky="we")

        # -------------------------
        # Voice controls
        # -------------------------
        ctk.CTkLabel(self.sidebar, text="Voice", font=("Segoe UI", 12, "bold")).grid(
            row=10, column=0, padx=16, pady=(12, 6), sticky="w"
        )

        # Toggle whether Evo speaks replies
        self.speak_btn = ctk.CTkButton(
            self.sidebar,
            text=("Speak: ON" if self.speak_enabled else "Speak: OFF"),
            command=self.toggle_speak,
        )
        self.speak_btn.grid(row=11, column=0, padx=16, pady=(0, 8), sticky="we")

        # Checkbox: after voice transcription, auto-send the message
        self.mic_send_var = ctk.BooleanVar(value=self.mic_auto_send)
        self.mic_send_chk = ctk.CTkCheckBox(
            self.sidebar,
            text="Auto-send after voice",
            variable=self.mic_send_var,
            command=self._on_mic_send_toggle,
        )
        self.mic_send_chk.grid(row=12, column=0, padx=16, pady=(0, 8), sticky="w")

        # Toggle light/dark mode
        self.theme_btn = ctk.CTkButton(self.sidebar, text="Toggle Theme", command=self.toggle_theme)
        self.theme_btn.grid(row=13, column=0, padx=16, pady=(0, 8), sticky="we")

        # -------------------------
        # Search widgets
        # -------------------------
        ctk.CTkLabel(self.sidebar, text="Search", font=("Segoe UI", 12, "bold")).grid(
            row=14, column=0, padx=16, pady=(12, 6), sticky="w"
        )
        self.search_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Find in chat...")
        self.search_entry.grid(row=15, column=0, padx=16, pady=(0, 8), sticky="we")

        self.search_btn = ctk.CTkButton(self.sidebar, text="Search", command=self.search_chat)
        self.search_btn.grid(row=16, column=0, padx=16, pady=(0, 8), sticky="we")

        self.search_result = ctk.CTkLabel(self.sidebar, text="", font=("Segoe UI", 11))
        self.search_result.grid(row=17, column=0, padx=16, pady=(0, 8), sticky="w")

        # -------------------------
        # Main area: chat feed + input bar
        # -------------------------
        self.chat_feed = ctk.CTkScrollableFrame(self.main, corner_radius=0)  # Scrollable chat history
        self.chat_feed.grid(row=0, column=0, sticky="nsew")

        self.input_bar = ctk.CTkFrame(self.main, corner_radius=0)           # Bottom input bar
        self.input_bar.grid(row=1, column=0, sticky="ew")
        self.input_bar.grid_columnconfigure(0, weight=1)                    # Entry expands

        # Text entry where user types
        self.entry = ctk.CTkEntry(self.input_bar, placeholder_text="Message Evo...")
        self.entry.grid(row=0, column=0, padx=12, pady=12, sticky="ew")

        # Mic button triggers speech-to-text
        self.mic_btn = ctk.CTkButton(self.input_bar, text="Mic", width=110, command=self.voice_input)
        self.mic_btn.grid(row=0, column=1, padx=(0, 8), pady=12)

        # Send button sends text to the model
        self.send_btn = ctk.CTkButton(self.input_bar, text="Send", width=110, command=self.send_message)
        self.send_btn.grid(row=0, column=2, padx=(0, 12), pady=12)

        # Pressing Enter triggers send_message
        self.entry.bind("<Return>", lambda e: self.send_message())

    def _bind_hotkeys(self):
        # Hotkeys to quickly perform common actions
        self.app.bind("<Control-n>", lambda e: self.new_chat())
        self.app.bind("<Control-l>", lambda e: self.clear_chat_view())
        self.app.bind("<Control-s>", lambda e: self.save_chat())
        self.app.bind("<Control-f>", lambda e: self._focus_search())

    def _focus_search(self):
        # Places cursor into the search bar
        self.search_entry.focus_set()

    # -------------------------
    # Persistence
    # -------------------------
    # Saving user settings (model, role, theme, etc.) to a JSON file.

    def persist(self):
        # Save current state to SETTINGS_FILE
        safe_write_json(
            SETTINGS_FILE,
            {
                "model": self.model_var.get(),              # currently selected model in UI
                "role": self.role_text,                     # role/system instructions
                "theme": self.theme,                        # dark/light
                "speak_enabled": self.speak_enabled,        # TTS enabled
                "tts_rate": int(self.tts.getProperty("rate")), # TTS speed
                "mic_auto_send": self.mic_auto_send,        # auto-send voice transcription
            },
        )

    def _on_mic_send_toggle(self):
        # Called when user toggles "Auto-send after voice"
        self.mic_auto_send = bool(self.mic_send_var.get())
        self.persist()

    # -------------------------
    # Chat UI helpers
    # -------------------------
    # These methods update the chat feed and manage message storage.

    def set_status(self, text: str):
        # Updates sidebar status label (Ready / Listening / Thinking etc.)
        self.status_var.set(text)

    def add_system(self, text: str):
        # Adds a system message to the chat feed and memory log
        self._add_msg("system", text)

    def add_user(self, text: str):
        # Adds a user message bubble
        self._add_msg("user", text)

    def add_evo(self, text: str):
        # Adds an Evo message bubble
        self._add_msg("evo", text)

    def _add_msg(self, sender: str, text: str):
        # Core message renderer:
        # 1) Store in self.messages
        # 2) Create a visual bubble/label in the UI
        text = (text or "").strip()
        if not text:
            return
        msg = Msg(sender=sender, text=text, ts=now_ts())
        self.messages.append(msg)

        # System messages appear as italic text (not a bubble)
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

        # Different colors and alignment for user vs evo messages
        bubble_color = "#2563eb" if sender == "user" else "#111827"
        text_color = "#ffffff" if sender == "user" else "#e5e7eb"
        anchor = "e" if sender == "user" else "w"  # user right, evo left

        # Bubble = a frame with timestamp and text inside
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
        self.chat_feed.update_idletasks()  # Refresh UI layout

    def clear_chat_view(self):
        # Clears the visible chat and the local message list
        # NOTE: It does NOT reset Gemini memory (that's reset_memory)
        self.messages.clear()
        for w in self.chat_feed.winfo_children():
            w.destroy()
        self.add_system("Chat view cleared (memory not reset).")

    def export_chat_text(self) -> str:
        # Converts all messages into a plain text format for saving
        lines = []
        for m in self.messages:
            who = "You" if m.sender == "user" else ("Evo" if m.sender == "evo" else "System")
            lines.append(f"[{m.ts}] {who}: {m.text}")
        return "\n".join(lines) + "\n"

    def save_chat(self):
        # Saves chat to a text file chosen via save dialog
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
        # Searches the in-memory message list for a substring
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
    # Handles changing models, applying role instructions, and resetting Gemini chat memory.

    def reset_memory(self):
        # Creates a fresh Gemini chat session (clears model conversation memory)
        self.model_id = self.model_var.get()
        self.chat = self.client.chats.create(model=self.model_id)

    def apply_role(self):
        # Reads role text from textbox, resets memory, and saves settings
        self.role_text = self.role_box.get("1.0", "end").strip() or DEFAULT_ROLE
        self.reset_memory()
        self.add_system("Role applied. Memory reset.")
        self.persist()

    def new_chat(self):
        # Starts a fresh chat: resets model memory + clears UI messages + saves settings
        self.reset_memory()
        self.clear_chat_view()
        self.add_system("New chat started.")
        self.persist()

    def toggle_theme(self):
        # Switch between dark/light mode and persist the choice
        mode = ctk.get_appearance_mode().lower()
        new_mode = "light" if mode == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.theme = new_mode
        self.persist()

    # -------------------------
    # Voice: STT + TTS
    # -------------------------
    # TTS = text to speech. STT = speech to text.

    def toggle_speak(self):
        # Turn speech on/off and persist the setting
        self.speak_enabled = not self.speak_enabled
        self.speak_btn.configure(text=("Speak: ON" if self.speak_enabled else "Speak: OFF"))
        self.persist()

    def speak(self, text: str):
        # Speaks text in a background thread so UI stays responsive
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
        # Records from microphone, transcribes using Google speech recognition,
        # handles voice commands, and optionally auto-sends the message.
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

                # Convert speech to a consistent format so commands match
                cmd = normalize_voice_command(text)
                if self._handle_voice_command(cmd):
                    return  # If it was a command, don't treat it as a chat message

                # Insert transcribed text into input box
                def fill():
                    self.entry.delete(0, "end")
                    self.entry.insert(0, text)

                self.app.after(0, fill)

                # Auto-send if enabled
                if self.mic_auto_send:
                    self.app.after(0, self.send_message)

            except Exception as e:
                # If anything fails (mic not found, timeout, etc.), show in system chat
                self.app.after(0, lambda: self.set_status("Ready"))
                self.app.after(0, lambda: self.add_system(f"Voice error: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_voice_command(self, cmd: str) -> bool:
        # Matches normalized spoken text to known commands and runs the action.
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

        return False  # Not a known command

    # -------------------------
    # Sending messages
    # -------------------------
    # Handles slash commands, sending text to Gemini in a background thread, and updating UI.

    def send_message(self):
        user_text = (self.entry.get() or "").strip()
        if not user_text:
            return

        # -------------------------
        # Slash commands (typed commands)
        # -------------------------
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

        # -------------------------
        # Normal message send flow
        # -------------------------
        self.entry.delete(0, "end")   # Clear input box
        self.add_user(user_text)      # Show user bubble in UI

        # If user changed model in the dropdown, reset chat memory for the new model
        selected_model = self.model_var.get()
        if selected_model != self.model_id:
            self.model_id = selected_model
            self.reset_memory()
            self.add_system(f"Model changed to {self.model_id}. Memory reset.")
            self.persist()

        # Update UI to "busy" state while model responds
        self.set_status("Thinking...")
        self.send_btn.configure(state="disabled")
        self.mic_btn.configure(state="disabled")

        def worker():
            try:
                # Construct prompt: role + user message
                prompt = f"ROLE:\n{self.role_text}\n\nUSER:\n{user_text}"

                # Send message to Gemini chat session (keeps conversation memory)
                resp = self.chat.send_message(prompt)
                reply = (resp.text or "").strip() or "(no response)"

                # Push UI updates back onto main UI thread using app.after
                self.app.after(0, lambda: self.add_evo(reply))
                self.app.after(0, lambda: self.set_status("Ready"))
                self.app.after(0, lambda: self.send_btn.configure(state="normal"))
                self.app.after(0, lambda: self.mic_btn.configure(state="normal"))

                # Optional: speak reply aloud
                self.speak(reply)

            except Exception as e:
                # Convert exception into user-friendly message
                msg = str(e)
                if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                    msg = "Rate limit hit. Wait a bit and try again."
                self.app.after(0, lambda: self.add_system(f"Error: {msg}"))
                self.app.after(0, lambda: self.set_status("Ready"))
                self.app.after(0, lambda: self.send_btn.configure(state="normal"))
                self.app.after(0, lambda: self.mic_btn.configure(state="normal"))

        # Run the model call in background so UI stays responsive
        threading.Thread(target=worker, daemon=True).start()

    # -------------------------
    # Run
    # -------------------------
    # Starts the Tkinter event loop (keeps the window open and responsive).

    def run(self):
        self.app.mainloop()


# =========================
# Script entry point
# =========================
# This makes sure the app only runs when you execute this file directly,
# not when it gets imported as a module.

if __name__ == "__main__":
    EvoProApp().run()