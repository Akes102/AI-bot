import os
import threading
from dotenv import load_dotenv
from google import genai
import customtkinter as ctk
from tkinter import filedialog, messagebox

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)
MODEL = "gemini-2.0-flash"

chat = client.chats.create(model=MODEL)
EVO_ROLE = "You are Evo. Keep replies short, clear, and helpful."

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Evo Modern GUI v9")
app.geometry("1000x650")
app.grid_columnconfigure(0, weight=0)
app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=1)

status_var = ctk.StringVar(value="Ready")

sidebar = ctk.CTkFrame(app, width=260, corner_radius=0)
sidebar.grid(row=0, column=0, sticky="nsw")
sidebar.grid_rowconfigure(10, weight=1)

main = ctk.CTkFrame(app, corner_radius=0)
main.grid(row=0, column=1, sticky="nsew")
main.grid_rowconfigure(0, weight=1)
main.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(sidebar, text="Evo Controls", font=("Segoe UI", 16, "bold")).grid(
    row=0, column=0, padx=16, pady=(16, 6), sticky="w"
)

ctk.CTkLabel(sidebar, textvariable=status_var, font=("Segoe UI", 12)).grid(
    row=1, column=0, padx=16, pady=(0, 12), sticky="w"
)

role_box = ctk.CTkTextbox(sidebar, height=140, font=("Segoe UI", 11))
role_box.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="we")
role_box.insert("1.0", EVO_ROLE)

chat_scroll = ctk.CTkScrollableFrame(main, corner_radius=0)
chat_scroll.grid(row=0, column=0, sticky="nsew")

chat_lines = []

def add_line(sender: str, text: str):
    chat_lines.append((sender, text))
    label = ctk.CTkLabel(
        chat_scroll,
        text=f"{sender}: {text}",
        wraplength=650,
        justify="left",
        anchor="w"
    )
    label.pack(anchor="w", padx=12, pady=6)

def reset_memory():
    global chat
    chat = client.chats.create(model=MODEL)

def clear_view():
    chat_lines.clear()
    for w in chat_scroll.winfo_children():
        w.destroy()

def save_chat():
    if not chat_lines:
        messagebox.showinfo("Save", "Nothing to save.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")]
    )
    if not path:
        return

    with open(path, "w", encoding="utf-8") as f:
        for s, t in chat_lines:
            f.write(f"{s}: {t}\n")

    messagebox.showinfo("Save", f"Saved to:\n{path}")

def apply_role():
    global EVO_ROLE
    EVO_ROLE = role_box.get("1.0", "end").strip()
    reset_memory()
    add_line("System", "Evo role updated. Memory reset.")

ctk.CTkButton(sidebar, text="Apply Role (reset)", command=apply_role).grid(
    row=3, column=0, padx=16, pady=(0, 8), sticky="we"
)

ctk.CTkButton(sidebar, text="Clear Memory", command=lambda: (reset_memory(), add_line("System", "Memory cleared."))).grid(
    row=4, column=0, padx=16, pady=(0, 8), sticky="we"
)

ctk.CTkButton(sidebar, text="New Chat", command=lambda: (reset_memory(), clear_view(), add_line("System", "New chat started."))).grid(
    row=5, column=0, padx=16, pady=(0, 8), sticky="we"
)

ctk.CTkButton(sidebar, text="Save Chat", command=save_chat).grid(
    row=6, column=0, padx=16, pady=(0, 8), sticky="we"
)

input_bar = ctk.CTkFrame(main, corner_radius=0)
input_bar.grid(row=1, column=0, sticky="ew")
input_bar.grid_columnconfigure(0, weight=1)

entry = ctk.CTkEntry(input_bar, placeholder_text="Type a message to Evo...")
entry.grid(row=0, column=0, padx=12, pady=12, sticky="ew")

def send_message():
    user_text = entry.get().strip()
    if not user_text:
        return

    entry.delete(0, "end")
    add_line("You", user_text)
    status_var.set("Thinking...")

    def worker():
        try:
            prompt = f"ROLE:\n{EVO_ROLE}\n\nUSER:\n{user_text}"
            resp = chat.send_message(prompt)
            reply = resp.text.strip() if resp.text else "(no response)"
        except Exception as e:
            reply = f"Error: {e}"

        app.after(0, lambda: add_line("Evo", reply))
        app.after(0, lambda: status_var.set("Ready"))

    threading.Thread(target=worker, daemon=True).start()

ctk.CTkButton(input_bar, text="Send", width=110, command=send_message).grid(
    row=0, column=1, padx=(0, 12), pady=12
)

entry.bind("<Return>", lambda e: send_message())

add_line("System", "Evo Modern GUI v9 running.")
app.mainloop()
