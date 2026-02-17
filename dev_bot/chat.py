"""

## 6. Making a Request (Python)

We use OpenAI’s **Python library**.

High-level steps:

1. Import the OpenAI client
2. Create a client with your API key
3. Call an endpoint
4. Send messages (prompt)
5. Receive a response

The **chat completions endpoint**:

- Sends a conversation (messages)
- Returns a model-generated reply

"""


import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

# Optional: check if key is loaded
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# Create OpenAI client
client = OpenAI(api_key=api_key)

#promt here
prompt = "Explain OpenAI API in simple terms"

#get response
response = client.responses.create(
    model="gpt-4.1-mini",
    input=prompt
)

print(response.output_text)