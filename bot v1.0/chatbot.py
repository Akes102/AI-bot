from openai import OpenAI
import os

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY is not set")

client = OpenAI()

print("AI Chatbot. Type 'exit' to quit.\n")

messages = [
    {"role": "system", "content": "You are a helpful assistant. Keep replies short and clear."}
]

while True:
    user_text = input("You: ").strip()
    if user_text.lower() == "exit":
        break

    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    reply = response.choices[0].message.content
    print("AI:", reply)

    messages.append({"role": "assistant", "content": reply})
