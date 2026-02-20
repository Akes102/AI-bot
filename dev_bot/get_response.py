
"""You are a junior developer at a dynamic startup that generates 
content with the help of AI. The company believes this 
technology can revolutionize storytelling, and you are excited 
to be a part of it. Today, your task is to generate a 
continuation of a story with a delimited prompt using an f-string.

The `OpenAI` package, the `get_response()` function,
and the `story` variable have been pre-loaded for you.

- Create a prompt asking to complete the variable `story` (provided to
you as a string): use f-string, and delimit the `story` with **triple 
backticks (```)** to pass its content to the prompt.
- Get the generated response."""

# import os
# from dotenv import load_dotenv
# from openai import OpenAI

# # Load environment variables from .env
# load_dotenv()

# # Get API key
# api_key = os.getenv("OPENAI_API_KEY")

# # Optional: check if key is loaded
# if not api_key:
#     raise ValueError("OPENAI_API_KEY not found in .env file")

# # Create OpenAI client
# client = OpenAI(api_key=api_key)



# def get_response(prompt):
# 		response = client.chat.completions.create(
#     model="gpt-4o-mini",
#     messages=[{"role":"User", "content":prompt}],
#     temperature = 0
    
#     )
#     return response.choices[0].message.content

# response = get_response("What is prompt engineering?")
# print(response)


import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

# Create OpenAI client
client = OpenAI(api_key=api_key)


def get_response(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content


response = get_response("What is prompt engineering?")
print(response)
