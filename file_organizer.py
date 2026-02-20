import tkinter as tk
from tkinter import filedialog
import os, shutil

root = tk.Tk()
root.title("File Organizer")
root.geometry("400x250")
root.configure(bg="#000")

status_var= tk.StringVar(value="Ready")
tk.Label(root,textvariable=status_var, bg="#111", fg="#0ff", font=("Ariel",16,"bold"),height=2).pack(fill="x", padx=10, pady=20)
TYPES = {
    "Images":[".Jpg",".jpeg",".png",".gif"],
    "Docs": [".pdf",".dox",".pages",],
    "Videos":[".mp4",".mov",".avi"],
    "Audio": [".mp3",".wav"],
    "Code": [".py",".toml"]
}

def organize_files(event):
    folder = filedialog.askdirectory()
    if not folder: return
    
    count=0
    for file in os.listdir(folder):
        if "." not in file: continue
        ext = os.path.splitext(file)[1].lower()
        
        for category, extension in TYPES.items():
            if ext in extension:
                target_dir = os.path.join(
                folder, category)
                if not os.path.exists(target_dir):
                    os.mkdir(target_dir)
                    shutil.move(os.path.join(folder, file), os.path.join(target_dir, file))
                    count+=1
                    break
    status_var.set(f"Moved {count} Files! ")
    
    frame = tk.Frame(root, bg="#000")
    frame.pack(pady=20)
    
    
                                    
                