"""

## 🔍 What’s Happening in This Code?

- `OpenAI()` creates a connection to the OpenAI API
- `model` specifies which AI model you want to use
- `input` is your prompt (question or instruction)
- `response.output_text` contains the AI’s reply

👉 This is the **same technology behind ChatGPT**, but now *you* control it through code.

## Reponse

“The API response is like a box 📦

Inside the box is a list 🧾

Inside the list is a message ✉️

Inside the message is the actual text 📝”

"""

# uv add openai 

from openai import OpenAI # Create a client (make sure your OPENAI_API_KEY is set in your environment)
client = OpenAI()# Replace the prompt below with your own question or instruction

response = client.chat.completions.create(
    model="gpt-4o-mini",
    max_completion_tokens=100,
  
    # Enter your prompt
    messages=[{"role": "user", "content": "Can you tell me about MERN stack job market"}]
)

print(response.choices[0].message.content)