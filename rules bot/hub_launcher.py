import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise RuntimeError("GEMINI_API_KEY is not set. Add it to .env")

projects = {
    "3) Evo Summarizer": "evo_v3_summarizer.py",
    "4) Evo Code Explainer": "evo_v4_code_explainer.py",
    "5) Evo Quiz Generator": "evo_v5_quiz_generator.py",
    "6) Evo Helpdesk": "evo_v6_helpdesk.py",
    "7) Evo File Q&A": "evo_v7_file_qa.py",
    "8) Evo GUI": "evo_v8_gui.py",
    "9) Evo Modern GUI": "evo_v9_modern_gui.py",
}

while True:
    print("\nEvo Project Hub v10")
    for i, name in enumerate(projects.keys(), start=1):
        print(f"{i}. {name}")
    print("0. Exit")

    choice = input("\nSelect a project: ").strip()

    if choice == "0":
        break

    try:
        idx = int(choice) - 1
        file_to_run = list(projects.values())[idx]
    except Exception:
        print("Invalid selection.")
        continue

    if not os.path.exists(file_to_run):
        print(f"Missing file: {file_to_run}")
        continue

    subprocess.run(["python", file_to_run], check=False)
