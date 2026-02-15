# gemini_v2_chat_memory_newsdk.py
# Gemini chatbot with memory using the NEW SDK.

import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set.")

client = genai.Client(api_key=api_key)
MODEL = "models/gemini-flash-latest"

# Block: start a chat session (keeps history for memory)
chat = client.chats.create(model=MODEL)

print("Evo v2 (new SDK + memory). Type 'exit' to quit.\n")

while True:
    user_text = input("You: ").strip()

    if user_text.lower() == "exit":
        print("Bye!")
        break

    if not user_text:
        print("Type something...")
        continue

    # Block: send a message to the chat session
    response = chat.send_message(user_text)

    print("Evo:", response.text)
