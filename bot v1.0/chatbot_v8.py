"""
EVO_v8 – Built-In Utility Tools

Adds non-AI tools such as a calculator, unit converter, and password strength checker, turning the chatbot into a multi-purpose assistant.

Concepts used: string parsing, regular expressions, secure evaluation, modular functions.

"""



from openai import OpenAI
import os
import math
import re

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set.")

client = OpenAI()

messages = [{"role": "system", "content": "You are a helpful assistant. Keep replies short, clear, and friendly."}]

def show_help():
    print("Commands:")
    print("  /help /clear /calc 2+2 /convert km_to_miles 10 /pw mypassword /exit")

def safe_calc(expr: str):
    allowed = set("0123456789+-*/(). ")
    if any(ch not in allowed for ch in expr):
        return "Blocked: only numbers and + - * / ( ) allowed"
    try:
        return str(eval(expr, {"__builtins__": {}}, {}))
    except Exception:
        return "Invalid expression"

def convert(kind: str, value: float):
    if kind == "km_to_miles":
        return value * 0.621371
    if kind == "miles_to_km":
        return value / 0.621371
    if kind == "c_to_f":
        return (value * 9/5) + 32
    if kind == "f_to_c":
        return (value - 32) * 5/9
    return None

def password_score(pw: str):
    score = 0
    tips = []
    if len(pw) >= 8:
        score += 1
    else:
        tips.append("Use 8+ characters")
    if re.search(r"[A-Z]", pw):
        score += 1
    else:
        tips.append("Add an uppercase letter")
    if re.search(r"[a-z]", pw):
        score += 1
    else:
        tips.append("Add a lowercase letter")
    if re.search(r"\d", pw):
        score += 1
    else:
        tips.append("Add a number")
    if re.search(r"[^A-Za-z0-9]", pw):
        score += 1
    else:
        tips.append("Add a symbol")
    return score, tips

print("Evo v8 running. Type /help for commands.\n")

while True:
    user_text = input("You: ").strip()

    if user_text.lower() in ("exit", "/exit"):
        print("Bye!")
        break

    if user_text == "/help":
        show_help()
        continue

    if user_text == "/clear":
        messages[:] = messages[:1]
        print("Cleared memory.")
        continue

    if user_text.startswith("/calc"):
        expr = user_text.replace("/calc", "", 1).strip()
        if not expr:
            expr = input("Expression: ").strip()
        print("Calc:", safe_calc(expr))
        continue

    if user_text.startswith("/convert"):
        parts = user_text.split()
        if len(parts) < 3:
            print("Usage: /convert km_to_miles 10")
            print("Types: km_to_miles miles_to_km c_to_f f_to_c")
            continue
        kind = parts[1]
        try:
            val = float(parts[2])
        except ValueError:
            print("Value must be a number.")
            continue
        out = convert(kind, val)
        if out is None:
            print("Unknown conversion type.")
        else:
            print("Result:", out)
        continue

    if user_text.startswith("/pw"):
        pw = user_text.replace("/pw", "", 1).strip()
        if not pw:
            pw = input("Password to check: ").strip()
        score, tips = password_score(pw)
        print("Strength score (0-5):", score)
        if tips:
            print("Tips:")
            for t in tips:
                print(" ", t)
        else:
            print("Solid password.")
        continue

    if not user_text:
        print("Type something.")
        continue

    messages.append({"role": "user", "content": user_text})
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply = resp.choices[0].message.content
    print("AI:", reply)
    messages.append({"role": "assistant", "content": reply})
